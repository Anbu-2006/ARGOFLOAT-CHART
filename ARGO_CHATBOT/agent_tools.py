"""
FloatChart Agent Tools
======================
A clean, agent-ready interface for the FloatChart ocean intelligence platform.

These functions are designed to be called by AI agents (LLMs with tool use) that want
to query the ARGO float database using natural language or structured parameters.

All functions return plain Python dicts (JSON-serializable) with consistent schemas:
  - `success` (bool): Whether the call succeeded.
  - `data` (list | dict): The result payload.
  - `error` (str | None): Human-readable error message on failure.
  - `metadata` (dict): Query context (record count, SQL used, timing, etc.).

Example usage (agent tool call):
    result = query_ocean_data("Show average temperature in Bay of Bengal for 2024")
    if result["success"]:
        print(result["data"])
"""

import time
import json
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC AGENT TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def query_ocean_data(
    question: str,
    engine=None,
    max_rows: int = 500,
) -> dict:
    """
    Ask a natural-language question about ARGO ocean float data.

    This is the primary tool for AI agents. It converts the question into SQL,
    executes it against the PostgreSQL database, and returns structured results
    with an AI-generated summary.

    Args:
        question (str):
            A natural-language question about ocean data. Examples:
            - "Show average temperature in Bay of Bengal for 2024"
            - "Find the 5 floats nearest to Chennai"
            - "What is the salinity trend in the Arabian Sea this year?"
            - "Show depth profile of float 2902115"
        engine (sqlalchemy.Engine | None):
            A pre-existing SQLAlchemy engine. If None, one is created from
            the DATABASE_URL environment variable.
        max_rows (int):
            Hard cap on the number of rows returned (default 500).
            Increase for time-series exports; decrease for quick lookups.

    Returns:
        dict with keys:
            success (bool)       — True if query succeeded.
            answer  (str)        — Concise AI-generated English summary.
            data    (list[dict]) — Tabular results, each row as a dict.
            chart_type (str)     — Suggested chart type: "line", "bar",
                                   "scatter", "map", "profile", "table".
            query_type (str)     — Detected intent: "Statistic", "Proximity",
                                   "Trajectory", "Profile", "Time-Series", etc.
            sql     (str)        — The SQL query that was executed.
            record_count (int)   — Number of rows returned.
            elapsed_ms  (float)  — Total wall-clock time in milliseconds.
            error   (str | None) — Error message if success is False.

    Example:
        >>> result = query_ocean_data("Average salinity near Mumbai last year")
        >>> print(result["answer"])
        "Average salinity near Mumbai (2024): 35.42 PSU (based on 1,203 measurements)"
    """
    start = time.time()
    try:
        from brain import get_intelligent_answer, get_engine
        if engine is None:
            engine = get_engine()

        response = get_intelligent_answer(question)

        # Enforce row cap
        if isinstance(response.get("data"), list) and len(response["data"]) > max_rows:
            response["data"] = response["data"][:max_rows]
            response["truncated"] = True

        response.setdefault("success", True)
        response["elapsed_ms"] = round((time.time() - start) * 1000, 1)
        return response

    except Exception as exc:
        return {
            "success": False,
            "answer": "Query failed.",
            "data": [],
            "error": str(exc),
            "elapsed_ms": round((time.time() - start) * 1000, 1),
        }


def build_and_validate_sql(intent: dict, db_context: dict, engine=None) -> dict:
    """
    Convert a parsed intent dictionary into a safe, validated SQL query string.

    Use this tool when you have already parsed a user question into a structured
    intent (e.g., via `parse_query_intent`) and want to generate SQL without
    executing it — useful for inspection, auditing, or dry-runs.

    Args:
        intent (dict):
            Structured intent from `parse_query_intent`. Required keys:
            - "query_type" (str): One of "Statistic", "Proximity", "Trajectory",
              "Profile", "Time-Series", "Scatter", "General".
            Optional keys: "metrics", "location_name", "latitude", "longitude",
            "time_constraint", "year", "float_id", "aggregation", "limit".
        db_context (dict):
            Database metadata dict with "min_date" and "max_date" (datetime).
            Obtain from `brain.get_database_context(engine)`.
        engine (sqlalchemy.Engine | None):
            Used for column-existence validation. Pass None to skip validation.

    Returns:
        dict with keys:
            success (bool)   — True if SQL was generated and passed safety checks.
            sql     (str)    — The generated SQL statement.
            safe    (bool)   — True if the SQL passed the safety sanitizer.
            blocked_reason (str | None)
                             — If `safe` is False, explains why the query was blocked.
            error   (str | None)

    Example:
        >>> intent = {"query_type": "Statistic", "metrics": ["temperature"],
        ...           "aggregation": "avg", "location_name": "bay of bengal"}
        >>> result = build_and_validate_sql(intent, db_context)
        >>> print(result["sql"])
        SELECT AVG(NULLIF("temperature", 'NaN')) AS "temperature" FROM argo_data ...
    """
    try:
        import sql_builder
        sql = sql_builder.build_query(intent, db_context, engine)

        safety = validate_sql_safety(sql)
        return {
            "success": safety["safe"],
            "sql": sql,
            "safe": safety["safe"],
            "blocked_reason": safety.get("reason"),
            "error": None if safety["safe"] else safety["reason"],
        }
    except Exception as exc:
        return {"success": False, "sql": "", "safe": False,
                "blocked_reason": None, "error": str(exc)}


def validate_sql_safety(sql: str) -> dict:
    """
    Run the SQL Sanitizer to check a query for destructive or unsafe operations.

    FloatChart enforces a strict read-only policy on all AI-generated SQL.
    This sanitizer is the last line of defence before any query reaches the
    database. It rejects DML/DDL statements and enforces SELECT-only access.

    Args:
        sql (str): The SQL string to validate.

    Returns:
        dict with keys:
            safe   (bool) — True if the query is considered safe to execute.
            reason (str | None)
                          — If `safe` is False, a human-readable explanation
                            of which rule was violated.
            checks (dict) — Individual check results for transparency.
    """
    from sql_sanitizer import SQLSanitizer
    return SQLSanitizer.validate(sql)


def parse_query_intent(question: str) -> dict:
    """
    Parse a natural-language ocean data question into a structured intent dict.

    Agents can use this as a two-step approach:
      1. Parse intent → inspect / override fields.
      2. Pass to `build_and_validate_sql` → execute.

    Args:
        question (str): Plain-English question about ARGO ocean data.

    Returns:
        dict with keys:
            success     (bool)
            intent      (dict) — Structured intent (query_type, metrics, etc.)
            complexity  (str)  — "simple" or "complex"
            error       (str | None)

    Intent fields:
        query_type   (str)      — "Statistic" | "Proximity" | "Trajectory" |
                                  "Profile" | "Time-Series" | "Scatter" | "General"
        metrics      (list[str])— e.g. ["temperature", "salinity"]
        location_name(str)      — e.g. "bay of bengal", "chennai"
        latitude     (float)    — Explicit lat if given
        longitude    (float)    — Explicit lon if given
        time_constraint(str)    — e.g. "2024", "March 2024", "last 6 months"
        year         (int)      — e.g. 2024
        float_id     (int)      — e.g. 2902115
        aggregation  (str)      — "avg" | "max" | "min" | "count"
        limit        (int)      — Row limit
        distance_km  (float)    — Radius for proximity queries (default 500)
    """
    try:
        from brain import classify_query_complexity, _fallback_intent_parser, get_llm, INTENT_PARSER_PROMPT
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        complexity = classify_query_complexity(question)

        try:
            llm = get_llm(query_complexity=complexity)
            prompt = PromptTemplate.from_template(INTENT_PARSER_PROMPT)
            chain = prompt | llm | StrOutputParser()
            raw = chain.invoke({"question": question})
            # Strip markdown fences if present
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            intent = json.loads(raw)
        except Exception:
            intent = _fallback_intent_parser(question)

        return {"success": True, "intent": intent, "complexity": complexity, "error": None}

    except Exception as exc:
        return {"success": False, "intent": {}, "complexity": "unknown", "error": str(exc)}


def get_floats_near_location(
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 500,
    limit: int = 10,
) -> dict:
    """
    Find the nearest ARGO floats to a geographic point or named location.

    Agents can call this directly with a city / sea name or explicit coordinates.
    Returns float positions, timestamps, and the distance to the query point.

    Args:
        location_name (str | None):
            Named location, e.g. "bay of bengal", "chennai", "mumbai".
            Supported names: all Indian coastal cities, major ocean basins,
            and 200+ international ports/regions (see brain.LOCATIONS).
        latitude  (float | None): Decimal degrees (-90 to 90). Overrides location_name.
        longitude (float | None): Decimal degrees (-180 to 180). Overrides location_name.
        radius_km (float): Search radius in kilometres (default 500).
        limit     (int):   Maximum floats to return (default 10, max 100).

    Returns:
        dict with keys:
            success      (bool)
            data         (list[dict]) — Float records sorted by distance_km.
              Each record: float_id, latitude, longitude, timestamp,
                           temperature, salinity, distance_km.
            record_count (int)
            error        (str | None)

    Example:
        >>> result = get_floats_near_location("chennai", radius_km=300, limit=5)
        >>> for f in result["data"]:
        ...     print(f["float_id"], f["distance_km"], "km away")
    """
    question = _build_proximity_question(location_name, latitude, longitude, radius_km, limit)
    return query_ocean_data(question)


def get_temperature_trend(
    location_name: str,
    year: Optional[int] = None,
    time_constraint: Optional[str] = None,
) -> dict:
    """
    Retrieve a time-series of daily average temperatures for a named ocean region.

    Args:
        location_name   (str): Named region, e.g. "bay of bengal", "arabian sea".
        year            (int | None): Filter to a specific year, e.g. 2024.
        time_constraint (str | None): Free-text time filter, e.g. "last 6 months",
                         "March 2024". Overrides `year` if both are provided.

    Returns:
        dict with keys:
            success      (bool)
            data         (list[dict]) — Daily records: day, temperature, salinity.
            chart_type   (str)        — Always "line" for this tool.
            record_count (int)
            error        (str | None)
    """
    time_str = time_constraint or (str(year) if year else "")
    question = f"Show temperature trend in {location_name}"
    if time_str:
        question += f" for {time_str}"
    return query_ocean_data(question)


def get_depth_profile(float_id: int) -> dict:
    """
    Retrieve the latest vertical depth profile (pressure vs measurements) for a float.

    Depth profiles show how temperature, salinity, and dissolved oxygen vary
    from the surface (~0 dbar) down to ~2000 dbar. Useful for visualising
    ocean stratification and thermoclines.

    Args:
        float_id (int): The 7-digit ARGO float WMO ID, e.g. 2902115.

    Returns:
        dict with keys:
            success      (bool)
            data         (list[dict]) — Sorted by pressure ASC. Fields: pressure,
                                        temperature, salinity, dissolved_oxygen,
                                        latitude, longitude, timestamp.
            chart_type   (str)        — Always "profile".
            record_count (int)
            error        (str | None)
    """
    return query_ocean_data(f"Show depth profile of float {float_id}")


def get_database_stats(engine=None) -> dict:
    """
    Return summary statistics about the local ARGO database.

    Useful for agents that need to understand the data available before querying—
    e.g., checking date ranges or confirming the database is populated.

    Args:
        engine: SQLAlchemy engine (optional; created from env if None).

    Returns:
        dict with keys:
            success         (bool)
            total_records   (int)   — Approximate total rows in argo_data.
            unique_floats   (int)   — Count of distinct float WMO IDs.
            date_range      (dict)  — {"min": ISO date, "max": ISO date}
            avg_temperature (float) — Global average surface temperature (°C).
            avg_salinity    (float) — Global average salinity (PSU).
            error           (str | None)
    """
    try:
        from brain import get_engine, get_database_context
        if engine is None:
            engine = get_engine()
        ctx = get_database_context(engine)
        if not ctx:
            return {"success": False, "error": "Database empty or unreachable."}

        from sqlalchemy import text
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT float_id) as floats,
                       ROUND(AVG("temperature")::numeric, 2) as avg_temp,
                       ROUND(AVG("salinity")::numeric,    2) as avg_sal
                FROM (SELECT * FROM argo_data LIMIT 500000) sample
            """)).fetchone()

        return {
            "success": True,
            "total_records": row[0],
            "unique_floats": row[1],
            "date_range": {
                "min": str(ctx["min_date"]),
                "max": str(ctx["max_date"]),
            },
            "avg_temperature": float(row[2]) if row[2] else None,
            "avg_salinity":    float(row[3]) if row[3] else None,
            "error": None,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_proximity_question(location_name, latitude, longitude, radius_km, limit) -> str:
    """Build a natural-language proximity question for the query engine."""
    limit_str = f"top {limit} " if limit else ""
    radius_str = f" within {radius_km} km" if radius_km else ""
    if latitude is not None and longitude is not None:
        return f"Find {limit_str}floats nearest to {latitude}°N {longitude}°E{radius_str}"
    if location_name:
        return f"Find {limit_str}floats nearest to {location_name}{radius_str}"
    return "Find nearest 10 ARGO floats"


# ─────────────────────────────────────────────────────────────────────────────
# MCP TOOL MANIFEST — Model Context Protocol compliant tool discovery
# ─────────────────────────────────────────────────────────────────────────────
#
# This manifest conforms to the Anthropic Model Context Protocol (MCP)
# specification for the `tools/list` response.  Each tool is described with:
#
#   • name         – Unique, snake_case tool identifier.
#   • description  – Human-readable explanation for the LLM.
#   • inputSchema  – A JSON Schema (draft-07) object describing accepted
#                    parameters, including `type`, `properties`, `required`,
#                    and optional `default` values.
#
# An MCP-compatible client (e.g., Claude Desktop, any MCP SDK consumer)
# can fetch GET /api/v1/tools to discover these tools and autonomously
# query ARGO float data without any manual configuration.
# ─────────────────────────────────────────────────────────────────────────────


def get_tool_manifest() -> dict:
    """
    Return the MCP-compliant tool manifest for FloatChart.

    This function is the single source of truth for tool discovery by AI
    agents.  It follows the Anthropic Model Context Protocol (MCP) schema
    so that Claude — and any other MCP-compatible orchestrator — can
    autonomously call FloatChart tools to query ARGO ocean float data.

    The returned dict mirrors the ``tools/list`` response shape defined by
    the MCP specification (2025-03-26):

        {
            "tools": [
                {
                    "name": "...",
                    "description": "...",
                    "inputSchema": {          # JSON Schema (draft-07)
                        "type": "object",
                        "properties": { ... },
                        "required": [ ... ]
                    }
                },
                ...
            ]
        }

    Returns:
        dict: A JSON-serializable dictionary with a single key ``"tools"``
              containing a list of MCP tool definitions.
    """
    return {
        "tools": [
            # ── Primary query tool ──────────────────────────────────────
            {
                "name": "query_ocean_data",
                "description": (
                    "Ask a natural-language question about ARGO ocean float "
                    "data. Converts the question into safe, read-only SQL, "
                    "executes it against the PostgreSQL/CockroachDB database, "
                    "and returns structured JSON with tabular data, an AI-"
                    "generated English summary, suggested chart type, and "
                    "the executed SQL for transparency."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": (
                                "Plain-English question about ocean data. "
                                "Examples: 'Show average temperature in Bay "
                                "of Bengal for 2024', 'Find the 5 floats "
                                "nearest to Chennai', 'Salinity trend in "
                                "Arabian Sea this year'."
                            ),
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (hard cap). Default 500, max 2000.",
                            "default": 500,
                        },
                    },
                    "required": ["question"],
                },
            },
            # ── SQL safety validator ────────────────────────────────────
            {
                "name": "validate_sql_safety",
                "description": (
                    "Run the FloatChart SQL Sanitizer on a raw SQL string "
                    "to determine if it is safe to execute. Returns a "
                    "verdict (safe/blocked) with the specific rule violated, "
                    "if any. Only SELECT and CTE queries are allowed; all "
                    "DML/DDL operations are rejected."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "The raw SQL query string to validate for safety.",
                        },
                    },
                    "required": ["sql_query"],
                },
            },
            # ── Proximity search ────────────────────────────────────────
            {
                "name": "get_floats_near_location",
                "description": (
                    "Find the nearest ARGO floats to a geographic point or "
                    "named location. Returns float positions, timestamps, "
                    "and distance to the query point."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location_name": {
                            "type": "string",
                            "description": "Named location, e.g. 'bay of bengal', 'chennai', 'mumbai'.",
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Decimal degrees (-90 to 90). Overrides location_name if provided.",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Decimal degrees (-180 to 180). Overrides location_name if provided.",
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometres.",
                            "default": 500,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of floats to return.",
                            "default": 10,
                        },
                    },
                    "required": [],
                },
            },
            # ── Temperature trend ───────────────────────────────────────
            {
                "name": "get_temperature_trend",
                "description": (
                    "Retrieve a daily average temperature time-series for a "
                    "named ocean region. Returns data suitable for line charts."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location_name": {
                            "type": "string",
                            "description": "Named region, e.g. 'bay of bengal', 'arabian sea'.",
                        },
                        "year": {
                            "type": "integer",
                            "description": "Filter to a specific year, e.g. 2024.",
                        },
                        "time_constraint": {
                            "type": "string",
                            "description": "Free-text time filter, e.g. 'last 6 months', 'March 2024'. Overrides year.",
                        },
                    },
                    "required": ["location_name"],
                },
            },
            # ── Depth profile ───────────────────────────────────────────
            {
                "name": "get_depth_profile",
                "description": (
                    "Retrieve the latest vertical depth profile (pressure vs "
                    "temperature/salinity/oxygen) for a specific ARGO float. "
                    "Shows ocean stratification from surface to ~2000 dbar."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "float_id": {
                            "type": "integer",
                            "description": "7-digit ARGO float WMO ID, e.g. 2902115.",
                        },
                    },
                    "required": ["float_id"],
                },
            },
            # ── Database statistics ─────────────────────────────────────
            {
                "name": "get_database_stats",
                "description": (
                    "Return summary statistics about the local ARGO database — "
                    "total records, unique float count, date range, and global "
                    "average temperature/salinity. Useful for understanding data "
                    "coverage before querying."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            # ── Intent parser (advanced) ────────────────────────────────
            {
                "name": "parse_query_intent",
                "description": (
                    "Parse a natural-language ocean data question into a "
                    "structured intent dict (query_type, metrics, location, "
                    "time constraints). Useful for two-step workflows: parse "
                    "intent → inspect/override → build SQL."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Plain-English question about ARGO ocean data.",
                        },
                    },
                    "required": ["question"],
                },
            },
        ]
    }


# Legacy alias — kept for backwards compatibility with any external scripts
# that may reference the old constant.
TOOL_MANIFEST = get_tool_manifest()
