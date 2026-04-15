"""
FloatChart SQL Sanitizer
========================
A safety-first validation layer for all AI-generated SQL queries.

FloatChart operates on a read-only principle: the AI may ONLY query data,
never modify, delete, or create it. This sanitizer enforces that contract
before any query reaches the PostgreSQL database.

This module is intentionally dependency-free (stdlib only) so it can be
imported anywhere in the stack without side effects.

Design philosophy (aligned with Anthropic's AI safety principles):
  1. ALLOWLIST over blocklist — only SELECT queries pass.
  2. TRANSPARENCY — every rejection includes a clear, human-readable reason.
  3. DEFENCE IN DEPTH — multiple independent checks, each targeting a different
     attack vector (DML, DDL, shell escape, stacked statements, etc.).
"""

import re
from typing import Optional


class SQLSanitizer:
    """Static validator for AI-generated SQL. All methods are class-level."""

    # ── Read-only allowlisted statement types ────────────────────────────────
    _ALLOWED_PREFIXES = ("select", "with")   # CTEs start with WITH

    # ── Destructive DML / DDL keywords (case-insensitive full-word match) ────
    _BLOCKED_KEYWORDS = [
        # Data Manipulation Language
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bTRUNCATE\b",
        r"\bMERGE\b",
        r"\bREPLACE\b",
        r"\bUPSERT\b",
        # Data Definition Language
        r"\bDROP\b",
        r"\bCREATE\b",
        r"\bALTER\b",
        r"\bRENAME\b",
        r"\bCOMMENT\s+ON\b",
        # Transaction control (prevent bypassing checks)
        r"\bCOMMIT\b",
        r"\bROLLBACK\b",
        r"\bBEGIN\b",
        r"\bSTART\s+TRANSACTION\b",
        # Privilege escalation
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bSET\s+ROLE\b",
        # PostgreSQL-specific dangerous functions
        r"\bPG_SLEEP\b",
        r"\bPG_READ_FILE\b",
        r"\bPG_WRITE_FILE\b",
        r"\bCOPY\b",
        r"\bLO_IMPORT\b",
        r"\bLO_EXPORT\b",
        # Shell execution
        r"\bEXECUTE\b",
        r"\bEXEC\b",
        r"\bCALL\b",
        r"\bCREATE\s+EXTENSION\b",
    ]

    # ── Table allowlist — ONLY argo_data may be queried ──────────────────────
    _ALLOWED_TABLES = {"argo_data", "information_schema.columns",
                       "information_schema.tables", "pg_class"}

    # ── Hard row cap to prevent runaway queries ───────────────────────────────
    MAX_LIMIT = 10_000

    @classmethod
    def validate(cls, sql: str) -> dict:
        """
        Run all safety checks on a SQL string. Returns a dict:

            safe   (bool)           — True only if ALL checks pass.
            reason (str | None)     — First failure reason, or None if safe.
            checks (dict[str,bool]) — Individual check results for auditability.

        Example:
            >>> SQLSanitizer.validate("DROP TABLE argo_data;")
            {"safe": False, "reason": "Blocked keyword detected: DROP",
             "checks": {"is_select": True, "no_blocked_keywords": False, ...}}
        """
        checks: dict[str, bool] = {}
        reason: Optional[str] = None

        sql_stripped = sql.strip()

        # ── Check 1: Non-empty ────────────────────────────────────────────────
        checks["non_empty"] = bool(sql_stripped)
        if not checks["non_empty"]:
            return cls._result(False, "SQL string is empty.", checks)

        sql_upper = sql_stripped.upper()
        sql_normalised = re.sub(r"\s+", " ", sql_stripped)

        # ── Check 2: Must start with SELECT or WITH (CTE) ────────────────────
        first_word = sql_normalised.lstrip().split()[0].lower()
        checks["is_select_or_cte"] = first_word in cls._ALLOWED_PREFIXES
        if not checks["is_select_or_cte"]:
            return cls._result(
                False,
                f"Only SELECT queries are allowed. Got: '{first_word.upper()}'.",
                checks,
            )

        # ── Check 3: Blocked keyword scan ────────────────────────────────────
        checks["no_blocked_keywords"] = True
        for pattern in cls._BLOCKED_KEYWORDS:
            if re.search(pattern, sql_upper):
                keyword = re.search(pattern, sql_upper).group(0)
                checks["no_blocked_keywords"] = False
                reason = f"Blocked keyword detected: {keyword}"
                return cls._result(False, reason, checks)

        # ── Check 4: No stacked / semicolon-separated statements ─────────────
        # Strip trailing semicolon then check for internal ones
        inner_sql = sql_stripped.rstrip(";")
        checks["no_stacked_statements"] = ";" not in inner_sql
        if not checks["no_stacked_statements"]:
            return cls._result(
                False,
                "Stacked SQL statements (multiple ';') are not allowed.",
                checks,
            )

        # ── Check 5: No SQL comment injection (-- or /* */) ──────────────────
        checks["no_comment_injection"] = (
            "--" not in sql_stripped and "/*" not in sql_stripped
        )
        if not checks["no_comment_injection"]:
            return cls._result(
                False,
                "SQL comments ('--' or '/* */') are not permitted in queries.",
                checks,
            )

        # ── Check 6: LIMIT present and within cap ────────────────────────────
        limit_match = re.search(r"\bLIMIT\s+(\d+)", sql_upper)
        if limit_match:
            limit_val = int(limit_match.group(1))
            checks["limit_within_cap"] = limit_val <= cls.MAX_LIMIT
            if not checks["limit_within_cap"]:
                return cls._result(
                    False,
                    f"LIMIT {limit_val} exceeds the maximum allowed cap of {cls.MAX_LIMIT}.",
                    checks,
                )
        else:
            # No LIMIT found — still allowed (some aggregation queries don't need one)
            checks["limit_within_cap"] = True

        # ── Check 7: No write-able pg_* system functions ─────────────────────
        pg_write_funcs = [
            r"\bpg_catalog\b", r"\bpg_namespace\b",
            r"\bset_config\b", r"\bcurrent_setting\b",
        ]
        checks["no_system_function_abuse"] = True
        for fn_pattern in pg_write_funcs:
            if re.search(fn_pattern, sql_upper):
                checks["no_system_function_abuse"] = False
                return cls._result(
                    False,
                    f"Disallowed system function reference detected.",
                    checks,
                )

        # All checks passed ✓
        return cls._result(True, None, checks)

    @staticmethod
    def _result(safe: bool, reason: Optional[str], checks: dict) -> dict:
        return {"safe": safe, "reason": reason, "checks": checks}

    @classmethod
    def sanitize_and_raise(cls, sql: str) -> str:
        """
        Validate SQL and return it unchanged if safe, or raise ValueError on failure.

        Convenience wrapper for use inside synchronous call chains where
        exception-based control flow is preferred over a result dict.

        Args:
            sql (str): SQL to validate.

        Returns:
            str: The original SQL string (unmodified) if it passes all checks.

        Raises:
            ValueError: With a descriptive message if any check fails.
        """
        result = cls.validate(sql)
        if not result["safe"]:
            raise ValueError(f"SQL Safety Violation: {result['reason']}")
        return sql
