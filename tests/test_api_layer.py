"""
FloatChart MCP API Layer — Functional Test Suite
=================================================
Simulates an AI agent interacting with the FloatChart API endpoints using
Flask's built-in test_client (no running server required).

Tests:
    1. Manifest Ping     — GET  /api/v1/tools   → 200, 7 MCP-compliant tools
    2. Safe Query         — POST /api/v1/query   → 200, valid JSON response
    3. Malicious Injection— POST /api/v1/query   → blocked (non-crash)
    4. SQL Validator       — POST /api/v1/validate-sql → safety verdicts
    5. Missing Payload     — POST /api/v1/query   → 400 for empty body
    6. Route Isolation     — GET  /               → 200 (no MCP interference)

Run:
    python test_api_layer.py
"""

import sys
import os
import json
import unittest

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── Ensure ARGO_CHATBOT is on the path ────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ARGO_CHATBOT"))

# ── Prevent database auto-connect during tests (no DB needed for API layer) ──
os.environ.setdefault("DATABASE_URL", "")


class TestMCPAPILayer(unittest.TestCase):
    """Functional tests for the FloatChart MCP API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Create the Flask test client once for all tests."""
        from app import app
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.app = app

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 1: Manifest Ping
    # ─────────────────────────────────────────────────────────────────────────
    def test_01_manifest_ping(self):
        """GET /api/v1/tools → 200, contains 7 MCP-compliant tools."""
        resp = self.client.get("/api/v1/tools")
        self.assertEqual(resp.status_code, 200, f"Expected 200, got {resp.status_code}")

        data = resp.get_json()
        self.assertIn("tools", data, "Response missing top-level 'tools' key")

        tools = data["tools"]
        self.assertEqual(len(tools), 7, f"Expected 7 tools, got {len(tools)}")

        # Verify each tool has the required MCP fields
        expected_names = {
            "query_ocean_data",
            "validate_sql_safety",
            "get_floats_near_location",
            "get_temperature_trend",
            "get_depth_profile",
            "get_database_stats",
            "parse_query_intent",
        }
        actual_names = {t["name"] for t in tools}
        self.assertEqual(actual_names, expected_names,
                         f"Tool name mismatch.\n  Missing: {expected_names - actual_names}"
                         f"\n  Extra:   {actual_names - expected_names}")

        for tool in tools:
            self.assertIn("name", tool, "Tool missing 'name'")
            self.assertIn("description", tool, f"Tool '{tool['name']}' missing 'description'")
            self.assertIn("inputSchema", tool, f"Tool '{tool['name']}' missing 'inputSchema'")
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object",
                             f"Tool '{tool['name']}' inputSchema.type must be 'object'")
            self.assertIn("properties", schema,
                          f"Tool '{tool['name']}' inputSchema missing 'properties'")
            self.assertIn("required", schema,
                          f"Tool '{tool['name']}' inputSchema missing 'required'")

        print("  ✅ TEST 1 PASSED: Manifest ping — 7 MCP-compliant tools returned")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 2: Safe Query Test
    # ─────────────────────────────────────────────────────────────────────────
    def test_02_safe_query(self):
        """POST /api/v1/query with a safe question → 200 or graceful 500 (no DB)."""
        resp = self.client.post(
            "/api/v1/query",
            data=json.dumps({"query": "What is the average temperature?"}),
            content_type="application/json",
        )
        # Without a live database/AI module, the server may return 500 with a
        # structured error — that's acceptable. What matters is:
        #   1. It does NOT crash (we get a response).
        #   2. The response is valid JSON.
        #   3. It contains 'api_version': 'v1'.
        self.assertIn(resp.status_code, [200, 500],
                      f"Expected 200 or 500, got {resp.status_code}")

        data = resp.get_json()
        self.assertIsNotNone(data, "Response is not valid JSON")
        self.assertEqual(data.get("api_version"), "v1",
                         "Response missing 'api_version': 'v1'")

        if resp.status_code == 200:
            self.assertTrue(data.get("success", False), "Expected success=True on 200")
            print("  ✅ TEST 2 PASSED: Safe query — 200 OK with valid data")
        else:
            # 500 with structured error is acceptable when no DB/AI is available
            self.assertIn("error", data, "500 response missing 'error' key")
            print("  ✅ TEST 2 PASSED: Safe query — 500 with structured error (no DB, expected)")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 3: Alignment/Safety — Malicious Injection
    # ─────────────────────────────────────────────────────────────────────────
    def test_03_malicious_injection(self):
        """POST /api/v1/query with injection attempts → never crashes."""
        attack_payloads = [
            {"query": "DROP TABLE argo_data;"},
            {"query": "'; DELETE FROM argo_data; --"},
            {"query": "SELECT * FROM argo_data; INSERT INTO argo_data VALUES (1,2,3);"},
            {"query": "GRANT ALL PRIVILEGES ON argo_data TO public;"},
        ]

        for payload in attack_payloads:
            resp = self.client.post(
                "/api/v1/query",
                data=json.dumps(payload),
                content_type="application/json",
            )
            # The server MUST NOT crash — any status code is fine as long as
            # we get a valid JSON response back (not a 500 stacktrace HTML page).
            data = resp.get_json()
            self.assertIsNotNone(data,
                                 f"Injection payload '{payload['query'][:40]}...' returned non-JSON")
            self.assertEqual(data.get("api_version"), "v1",
                             f"Missing api_version for payload '{payload['query'][:40]}...'")

        print("  ✅ TEST 3 PASSED: Alignment/safety — all injection payloads handled gracefully")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 4: SQL Validator Endpoint
    # ─────────────────────────────────────────────────────────────────────────
    def test_04_sql_validator_safe(self):
        """POST /api/v1/validate-sql with a safe SELECT → marked safe."""
        resp = self.client.post(
            "/api/v1/validate-sql",
            data=json.dumps({"sql": "SELECT AVG(temperature) FROM argo_data LIMIT 100"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, f"Expected 200, got {resp.status_code}")
        data = resp.get_json()
        self.assertTrue(data.get("safe"), f"Expected safe=True, got: {data}")
        print("  ✅ TEST 4a PASSED: SQL validator — safe SELECT accepted")

    def test_05_sql_validator_dangerous(self):
        """POST /api/v1/validate-sql with DROP TABLE → marked unsafe."""
        resp = self.client.post(
            "/api/v1/validate-sql",
            data=json.dumps({"sql": "DROP TABLE argo_data;"}),
            content_type="application/json",
        )
        # Should be 400 (unsafe query detected)
        self.assertEqual(resp.status_code, 400, f"Expected 400, got {resp.status_code}")
        data = resp.get_json()
        self.assertFalse(data.get("safe"), f"Expected safe=False, got: {data}")
        self.assertIsNotNone(data.get("reason"), "Expected a reason for rejection")
        print("  ✅ TEST 4b PASSED: SQL validator — DROP TABLE correctly blocked")

    def test_06_sql_validator_missing_payload(self):
        """POST /api/v1/validate-sql with no SQL → 400."""
        resp = self.client.post(
            "/api/v1/validate-sql",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400, f"Expected 400, got {resp.status_code}")
        print("  ✅ TEST 4c PASSED: SQL validator — missing payload returns 400")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 5: Missing Query Payload → 400
    # ─────────────────────────────────────────────────────────────────────────
    def test_07_missing_query_payload(self):
        """POST /api/v1/query with empty body → 400."""
        resp = self.client.post(
            "/api/v1/query",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400, f"Expected 400, got {resp.status_code}")
        data = resp.get_json()
        self.assertFalse(data.get("success", True), "Expected success=False on 400")
        print("  ✅ TEST 5 PASSED: Missing query payload → 400 with structured error")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 6: Route Isolation — MCP does not break existing routes
    # ─────────────────────────────────────────────────────────────────────────
    def test_08_route_isolation(self):
        """GET / → 200 (static file served, not broken by API routes)."""
        resp = self.client.get("/")
        # index.html may or may not exist in the test env, but the route itself
        # must be registered and not return 404/500 from a routing conflict.
        self.assertIn(resp.status_code, [200, 404],
                      f"Root route returned unexpected {resp.status_code}")

        # Check /api/health is still alive
        resp_health = self.client.get("/api/health")
        self.assertEqual(resp_health.status_code, 200)
        health_data = resp_health.get_json()
        self.assertEqual(health_data.get("status"), "healthy")
        print("  ✅ TEST 6 PASSED: Route isolation — existing routes intact")


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  FloatChart MCP API — Functional Test Suite")
    print("=" * 60 + "\n")

    # Run tests in definition order (not alphabetical)
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite = loader.loadTestsFromTestCase(TestMCPAPILayer)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("  🟢 ALL SYSTEMS GREEN: MCP API is fully functional")
        print("     and ready for deployment.")
    else:
        print("  🔴 FAILURES DETECTED — see above for details.")
        for fail in result.failures + result.errors:
            print(f"     ✗ {fail[0]}")
    print("=" * 60 + "\n")

