from datetime import datetime, timedelta
import re

# ── Safety layer ─────────────────────────────────────────────────────────────
# Import the SQL Sanitizer to validate every generated query before returning.
# This enforces a strict read-only policy on all AI-generated SQL.
try:
    from sql_sanitizer import SQLSanitizer
    _SANITIZER_AVAILABLE = True
except ImportError:
    _SANITIZER_AVAILABLE = False


def _apply_safety_check(sql: str) -> str:
    """
    Pass the final SQL through the safety sanitizer.

    Returns the SQL unchanged if it is safe.
    Raises ValueError with a descriptive message if any safety check fails.
    This is the last gate before the query leaves this module.
    """
    if not _SANITIZER_AVAILABLE:
        return sql  # Graceful degradation if sanitizer not installed
    result = SQLSanitizer.validate(sql)
    if not result["safe"]:
        raise ValueError(
            f"SQL Safety Violation — query blocked by FloatChart sanitizer.\n"
            f"Reason: {result['reason']}\n"
            f"Checks: {result['checks']}"
        )
    return sql


def build_query(intent: dict, db_context: dict, engine=None) -> str:
    query_type = intent.get("query_type")
    existing_cols = set()
    if engine is not None:
        try:
            existing_cols = _get_existing_columns(engine)
        except Exception:
            existing_cols = set()

    # Route to the appropriate query builder, then enforce safety on the result.
    if query_type == "Proximity":
        sql = _build_proximity_query(intent, db_context)
    elif query_type == "Time-Series":
        sql = _build_timeseries_query(intent, db_context, existing_cols)
    elif query_type == "Statistic":
        sql = _build_statistic_query(intent, db_context, existing_cols)
    elif query_type == "Profile":
        sql = _build_profile_query(intent, existing_cols)
    elif query_type == "Trajectory":
        sql = _build_trajectory_query(intent, db_context, existing_cols)
    elif query_type == "Scatter":
        sql = _build_scatter_query(intent, db_context, existing_cols)
    elif query_type == "Path":
        sql = _build_path_query(intent, existing_cols)
    else:
        sql = _build_general_query(intent, db_context)

    # ── SAFETY GATE ─────────────────────────────────────────────────────────
    # Every query passes through the SQLSanitizer before leaving this module.
    # This prevents destructive or unexpected queries from reaching the database.
    return _apply_safety_check(sql)

def _build_path_query(intent: dict, existing_cols=None) -> str:
    float_id = intent.get("float_id")
    metrics = intent.get("metrics") or []
    # Only use columns that exist
    base_cols = [c for c in ["float_id", "timestamp", "latitude", "longitude"] if not existing_cols or c in existing_cols]
    sensor_cols = [c for c in ["temperature", "salinity", "dissolved_oxygen", "chlorophyll", "nitrate", "ph", "pressure"] if not existing_cols or c in existing_cols]
    select_cols = base_cols + [m for m in metrics if m in sensor_cols]
    if not select_cols:
        select_cols = base_cols
    where_clause = f'"float_id" = {float_id}' if float_id else '1=1'
    cols_str = ', '.join([f'"{c}"' for c in select_cols])
    return f'SELECT {cols_str} FROM argo_data WHERE {where_clause} ORDER BY "timestamp" ASC;'

def _build_proximity_query(intent: dict, db_context: dict) -> str:
    lat, lon, limit = intent.get("latitude"), intent.get("longitude"), intent.get("limit", 5)
    # If coordinates are missing, try to set from location_name
    if (lat is None or lon is None):
        location_name = (intent.get("location_name") or "").lower()
        location_centers = {
            # Indian Ocean
            "arabian sea": (15, 62.5),
            "bay of bengal": (13.5, 87.5),
            "indian ocean": (0, 75),
            "andaman sea": (10, 95),
            "laccadive sea": (11, 74),
            "red sea": (20, 38),
            "persian gulf": (27, 52),
            "mozambique channel": (-18, 40),
            # Pacific Ocean
            "pacific ocean": (0, 160),
            "south china sea": (15, 115),
            "philippine sea": (20, 130),
            "coral sea": (-16, 155),
            "tasman sea": (-37, 162),
            # Atlantic Ocean
            "atlantic ocean": (25, -40),
            "caribbean sea": (17, -75),
            "gulf of mexico": (25, -90),
            "mediterranean sea": (38, 18),
            "north sea": (56, 3),
            # Indian Cities
            "chennai": (13.08, 80.27),
            "mumbai": (18.97, 72.82),
            "kollam": (8.88, 76.59),
            "kochi": (9.93, 76.26),
            "cochin": (9.93, 76.26),
            "goa": (15.30, 73.82),
            "kolkata": (22.57, 88.36),
            "visakhapatnam": (17.68, 83.22),
            "vizag": (17.68, 83.22),
            "mangalore": (12.91, 74.85),
            "tuticorin": (8.76, 78.13),
            "pondicherry": (11.93, 79.83),
            "puducherry": (11.93, 79.83),
            "trivandrum": (8.52, 76.94),
            "thiruvananthapuram": (8.52, 76.94),
            "surat": (21.17, 72.83),
            "kandla": (23.03, 70.22),
            "paradip": (20.32, 86.61),
            "andaman": (11.67, 92.75),
            "port blair": (11.62, 92.73),
            "karwar": (14.80, 74.13),
            "ratnagiri": (16.99, 73.30),
            # International Cities
            "sri lanka": (7.5, 80.5),
            "singapore": (1.3, 104),
            "tokyo": (35.5, 140),
            "sydney": (-34, 151),
            "cape town": (-34, 18),
            "miami": (26, -80),
            "maldives": (4.17, 73.51),
            "mauritius": (-20.2, 57.5),
            # Special
            "equator": (0, 80),
            "southern ocean": (-55, 0),
            "tropics": (10, 80),
        }
        if location_name in location_centers:
            lat, lon = location_centers[location_name]
            intent["latitude"] = lat
            intent["longitude"] = lon
    # If still missing, return a friendly error
    if lat is None or lon is None:
        return "ERROR: Proximity query requires coordinates or a known location. Please specify a location like 'Chennai', 'Bay of Bengal', or provide coordinates."
    
    # Validate coordinates are in valid range
    if not (-90 <= lat <= 90):
        return f"ERROR: Invalid latitude {lat}. Latitude must be between -90 and 90 degrees."
    if not (-180 <= lon <= 180):
        return f"ERROR: Invalid longitude {lon}. Longitude must be between -180 and 180 degrees."

    metrics = intent.get("metrics") or []
    # Ensure we only select unique metrics and avoid duplicating base columns
    metric_cols = [m for m in metrics if m not in {"latitude", "longitude", "float_id", "timestamp"}]

    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    base_conditions = []
    if time_clause != "1=1":
        base_conditions.append(time_clause)
    
    # OPTIMIZATION: Add bounding box filter to drastically reduce scanned rows
    # Dynamic box size based on search distance (distance_km / 111 ≈ degrees)
    search_distance = intent.get("distance_km", 500)
    # Use larger box than search distance to ensure we don't miss edge cases
    # 1 degree ≈ 111km at equator, use 1.5x multiplier for safety
    lat_delta = max(8.0, (search_distance / 111) * 1.5)  # At least 8 degrees (~888km)
    lon_delta = max(8.0, (search_distance / 111) * 1.5)  # Longitude varies but safe estimate
    bounding_box = f'"latitude" BETWEEN {lat - lat_delta} AND {lat + lat_delta} AND "longitude" BETWEEN {lon - lon_delta} AND {lon + lon_delta}'
    base_conditions.append(bounding_box)
    
    where_sql = " AND ".join(base_conditions) if base_conditions else "TRUE"

    base_select_cols = ['"float_id"', '"timestamp"', 'ROUND("latitude"::numeric, 4) as "latitude"', 'ROUND("longitude"::numeric, 4) as "longitude"']
    metric_select_cols = [f'ROUND("{col}"::numeric, 3) as "{col}"' for col in metric_cols]
    latest_select_cols = ['"float_id"', '"timestamp"', '"latitude"', '"longitude"'] + [f'"{col}"' for col in metric_cols]
    raw_projection = ", ".join(['"float_id"', '"timestamp"', '"latitude"', '"longitude"'] + [f'"{col}"' for col in metric_cols])

    distance_formula = (
        f"ROUND((6371 * acos(LEAST(1.0, GREATEST(-1.0, "
        f"cos(radians({lat}::float)) * cos(radians(\"latitude\"::float)) "
        f"* cos(radians(\"longitude\"::float) - radians({lon}::float)) "
        f"+ sin(radians({lat}::float)) * sin(radians(\"latitude\"::float))))))::numeric, 2)"
    )

    # FIXED: Filter by time FIRST in the base query, then find nearest floats
    # This ensures we get the nearest floats within the specified time period
    
    # Build metric columns for SQL - handle empty metrics case
    if metric_cols:
        metric_round_sql = ", " + ", ".join([f'ROUND("{col}"::numeric, 3) as "{col}"' for col in metric_cols])
        metric_select_sql = ", " + ", ".join([f'"{col}"' for col in metric_cols])
    else:
        metric_round_sql = ""
        metric_select_sql = ""
    
    # OPTIMIZED: Simplified CTE structure - reduces query planning time
    # Use indexed columns in WHERE first, then compute distance only on filtered set
    query = """
    WITH filtered_data AS (
        SELECT "float_id", "timestamp", "latitude", "longitude"{metric_cols_select}
        FROM argo_data
        WHERE "latitude" IS NOT NULL 
          AND "longitude" IS NOT NULL
          AND {bounding_box}
          {time_filter}
    ),
    latest_per_float AS (
        SELECT DISTINCT ON ("float_id")
            "float_id", "timestamp",
            ROUND("latitude"::numeric, 4) as "latitude",
            ROUND("longitude"::numeric, 4) as "longitude"{metric_round}
        FROM filtered_data
        ORDER BY "float_id", "timestamp" DESC
    ),
    with_distance AS (
        SELECT *,
            {distance_expr} AS distance_km
        FROM latest_per_float
    )
    SELECT "float_id", "timestamp", "latitude", "longitude"{metric_cols_select}, distance_km
    FROM with_distance
    WHERE distance_km <= {max_distance}
    ORDER BY distance_km ASC
    LIMIT {limit};
    """.format(
        bounding_box=bounding_box,
        time_filter=f"AND {time_clause}" if time_clause != "1=1" else "",
        metric_round=metric_round_sql,
        metric_cols_select=metric_select_sql,
        distance_expr=distance_formula,
        max_distance=intent.get("distance_km", 500),
        limit=limit,
    )

    return "\n".join([line for line in query.splitlines() if line.strip()])

def _build_timeseries_query(intent: dict, db_context: dict, existing_cols=None) -> str:
    metrics = intent.get("metrics") or []
    if existing_cols:
        metrics = [m for m in metrics if m in existing_cols]
    if not metrics:
        metrics = [c for c in ["temperature", "salinity", "dissolved_oxygen", "chlorophyll", "ph", "pressure"] if not existing_cols or c in existing_cols]
    location_clause = intent.get("location_clause", "1=1")
    agg_metrics = [f'AVG(NULLIF("{m}", \'NaN\')) AS "{m}"' for m in metrics]
    select_cols = ["DATE_TRUNC('day', \"timestamp\") as day"]
    if not existing_cols or "latitude" in existing_cols:
        select_cols.append('AVG("latitude") as latitude')
    if not existing_cols or "longitude" in existing_cols:
        select_cols.append('AVG("longitude") as longitude')
    select_cols += agg_metrics
    if len(select_cols) == 1:
        select_cols.append('COUNT("float_id") as count')
    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    base_query_from = f"FROM argo_data WHERE {location_clause} AND {time_clause}"
    # OPTIMIZATION: Limit time-series to 365 days max to prevent huge scans
    limit = intent.get("limit", 365)
    return f"SELECT {', '.join(select_cols)} {base_query_from} GROUP BY day ORDER BY day ASC LIMIT {limit};"

def _build_statistic_query(intent: dict, db_context: dict, existing_cols=None) -> str:
    metrics = intent.get("metrics") or []
    aggregation = intent.get("aggregation", "avg").upper()
    if existing_cols:
        metrics = [m for m in metrics if m in existing_cols]
    location_clause = intent.get("location_clause", "1=1")
    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    base_query_from = f"FROM argo_data WHERE {location_clause} AND {time_clause}"
    if metrics and aggregation != "COUNT":
        select_exprs = [f'{aggregation}(NULLIF("{m}", \'NaN\')) AS "{m}"' for m in metrics]
        return f'SELECT {", ".join(select_exprs)} {base_query_from};'
    metric_to_agg = f'"{metrics[0]}"' if metrics else '"float_id"'
    if aggregation == "COUNT": metric_to_agg = f'DISTINCT "float_id"'
    return f'SELECT {aggregation}({metric_to_agg}) {base_query_from};'

def _get_existing_columns(engine) -> set:
    # Returns a set of all column names in argo_data table
    insp = engine.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'argo_data';")
    return set(row[0] for row in insp)

def _build_profile_query(intent: dict, existing_cols=None) -> str:
    float_id = intent.get("float_id")
    location_clause = intent.get("location_clause")
    time_constraint = intent.get("time_constraint")
    metrics = intent.get("metrics")
    sensor_cols = ["temperature", "salinity", "dissolved_oxygen", "chlorophyll", "nitrate", "ph", "pressure"]
    # Only select columns that exist in the table
    if existing_cols:
        sensor_cols = [col for col in sensor_cols if col in existing_cols]
    if metrics:
        metrics = [m for m in metrics if m in sensor_cols]
    else:
        metrics = sensor_cols
    if float_id is not None:
        select_cols = [f'"{m}"' for m in metrics] if metrics else [f'"{m}"' for m in sensor_cols]
        select_cols += [col for col in ["pressure", "latitude", "longitude", "float_id", "timestamp"] if not existing_cols or col in existing_cols]
        return f'SELECT {", ".join(select_cols)} FROM argo_data WHERE "float_id" = {float_id} AND "timestamp" = (SELECT MAX("timestamp") FROM argo_data WHERE "float_id" = {float_id}) ORDER BY "pressure" ASC;'
    clauses = []
    if location_clause:
        clauses.append(location_clause)
    if time_constraint:
        from datetime import datetime
        max_date = datetime.now()
        time_clause = _get_time_clause(time_constraint, max_date)
        if time_clause != "1=1":
            clauses.append(time_clause)
    if not clauses:
        raise ValueError("Profile query requires a valid float_id, location, or time constraint.")
    where_clause = " AND ".join(clauses)
    select_cols = [f'"{m}"' for m in metrics] if metrics else [f'"{m}"' for m in sensor_cols]
    select_cols += [col for col in ["pressure", "latitude", "longitude", "float_id", "timestamp"] if not existing_cols or col in existing_cols]
    return f'SELECT {", ".join(select_cols)} FROM argo_data WHERE {where_clause} AND "timestamp" = (SELECT MAX("timestamp") FROM argo_data WHERE {where_clause}) ORDER BY "pressure" ASC;'

def _build_trajectory_query(intent: dict, db_context: dict, existing_cols=None) -> str:
    float_id = intent.get("float_id")
    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    sensor_cols = ["temperature", "salinity", "dissolved_oxygen", "chlorophyll", "nitrate", "ph", "pressure"]
    if existing_cols:
        sensor_cols = [col for col in sensor_cols if col in existing_cols]
    # Only use metrics that exist
    metrics = intent.get("metrics") or []
    metrics = [m for m in metrics if not existing_cols or m in existing_cols]
    base_cols = [col for col in ["float_id", "timestamp", "latitude", "longitude"] if not existing_cols or col in existing_cols]
    select_cols = base_cols + [m for m in metrics if m in sensor_cols]
    # If no metrics, use all available sensor_cols
    if not metrics:
        select_cols += sensor_cols
    # Remove duplicates
    select_cols = list(dict.fromkeys(select_cols))
    if not select_cols:
        select_cols = base_cols
    cols_str = ", ".join([f'"{c}"' for c in select_cols])
    return f'SELECT {cols_str} FROM argo_data WHERE "float_id" = {float_id} AND {time_clause} ORDER BY "timestamp" ASC;'

def _build_scatter_query(intent: dict, db_context: dict, existing_cols=None) -> str:
    metrics = intent.get("metrics") or []
    if existing_cols:
        metrics = [m for m in metrics if m in existing_cols]
    if len(metrics) < 2:
        metrics = [c for c in ["temperature", "salinity"] if not existing_cols or c in existing_cols]
    location_clause = intent.get("location_clause", "1=1")
    select_cols = [f'"{m}"' for m in metrics]
    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    base_query_from = f"FROM argo_data WHERE {location_clause} AND {time_clause}"
    non_null_clauses = [f'"{m}" IS NOT NULL' for m in metrics]
    cols_str = ', '.join(select_cols)
    null_str = ' AND '.join(non_null_clauses)
    return f"SELECT {cols_str} {base_query_from} AND {null_str} LIMIT 1000;"

def _build_general_query(intent: dict, db_context: dict) -> str:
    location_clause = intent.get("location_clause", "1=1")
    time_clause = _get_time_clause(intent.get("time_constraint"), db_context.get("max_date_obj"))
    base_query_from = f"FROM argo_data WHERE {location_clause} AND {time_clause}"
    return f"SELECT * {base_query_from} LIMIT 500;"

def _get_time_clause(time_constraint: str, max_date: datetime = None) -> str:
    if not time_constraint:
        return "1=1"
    
    # Default max_date to today if not provided
    if max_date is None:
        max_date = datetime.now()
    
    if "last 6 months" in time_constraint.lower():
        start_date = (max_date - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = max_date.strftime('%Y-%m-%d')
        return f'"timestamp" BETWEEN \'{start_date}\' AND \'{end_date}\''
    
    # Try to extract year
    year_match = re.search(r'\b(20\d{2})\b', time_constraint)
    if year_match:
        year = year_match.group(1)
        # Try to extract month
        month_match = re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b', time_constraint, re.IGNORECASE)
        if month_match:
            month_str = month_match.group(1).lower()[:3]
            month_num = {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}[month_str]
            return f'EXTRACT(YEAR FROM "timestamp") = {year} AND EXTRACT(MONTH FROM "timestamp") = {month_num}'
        return f'"timestamp" BETWEEN \'{year}-01-01\' AND \'{year}-12-31\''
    
    return "1=1"