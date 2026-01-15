"""
FloatChart - Data Pipeline for Local PostgreSQL
Fetches real ARGO float data from ERDDAP and loads into local PostgreSQL database.

Usage:
    python fetch_argo_data.py --region "Bay of Bengal" --days 30
    python fetch_argo_data.py --lat 13.0 --lon 80.0 --radius 500 --days 60
"""

import os
import sys
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from typing import Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DATA_GENERATOR.env_utils import load_environment
from DATA_GENERATOR.config import REGION_LABEL

# ERDDAP Server for ARGO data
ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap"
DATASET_ID = "ArgoFloats"

# Region coordinates (lat_min, lat_max, lon_min, lon_max)
REGIONS = {
    "indian ocean": (-40, 25, 30, 120),
    "bay of bengal": (5, 22, 80, 95),
    "arabian sea": (5, 25, 50, 75),
    "pacific ocean": (-60, 60, 100, 180),
    "atlantic ocean": (-60, 60, -80, 0),
    "mediterranean sea": (30, 46, -6, 36),
    "south china sea": (0, 25, 100, 121),
    "caribbean sea": (10, 22, -88, -60),
}


def get_db_engine():
    """Create database engine from environment."""
    load_environment()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL not set. Please create a .env file with:\n"
            "DATABASE_URL=postgresql://user:password@localhost:5432/dbname"
        )
    return create_engine(database_url)


def fetch_argo_data(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    start_date: datetime,
    end_date: datetime,
    max_records: int = 10000
) -> Optional[pd.DataFrame]:
    """
    Fetch ARGO float data from ERDDAP server.
    
    Args:
        lat_min, lat_max: Latitude bounds
        lon_min, lon_max: Longitude bounds
        start_date, end_date: Time range
        max_records: Maximum records to fetch
    
    Returns:
        DataFrame with ARGO float data or None if failed
    """
    # Format dates for ERDDAP
    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Build ERDDAP query URL
    url = (
        f"{ERDDAP_BASE}/{DATASET_ID}.csv?"
        f"float_id,time,latitude,longitude,temp,psal,pres"
        f"&time>={start_str}&time<={end_str}"
        f"&latitude>={lat_min}&latitude<={lat_max}"
        f"&longitude>={lon_min}&longitude<={lon_max}"
        f"&orderBy(%22time%22)"
    )
    
    print(f"Fetching data from ERDDAP...")
    print(f"  Region: ({lat_min}, {lat_max}) x ({lon_min}, {lon_max})")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")
    
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Parse CSV response
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), skiprows=[1])  # Skip units row
        
        if df.empty:
            print("  No data found for this query.")
            return None
        
        # Rename columns to match our schema
        column_map = {
            "float_id": "float_id",
            "time": "timestamp",
            "latitude": "latitude",
            "longitude": "longitude",
            "temp": "temperature",
            "psal": "salinity",
            "pres": "pressure"
        }
        df = df.rename(columns=column_map)
        
        # Clean data
        df = df.dropna(subset=["latitude", "longitude"])
        df["float_id"] = df["float_id"].astype(str).str.extract(r'(\d+)').astype(int)
        
        print(f"  Fetched {len(df)} records from {df['float_id'].nunique()} floats")
        return df[:max_records]
        
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"  Error processing data: {e}")
        return None


def load_to_database(df: pd.DataFrame, engine, replace: bool = False) -> int:
    """
    Load DataFrame into PostgreSQL database.
    
    Args:
        df: DataFrame with ARGO data
        engine: SQLAlchemy engine
        replace: If True, replace existing data. If False, append.
    
    Returns:
        Number of records inserted
    """
    if df is None or df.empty:
        return 0
    
    table_name = "argo_data"
    mode = "replace" if replace else "append"
    
    print(f"Loading {len(df)} records to database...")
    
    try:
        df.to_sql(table_name, engine, if_exists=mode, index=False)
        print(f"  Successfully loaded {len(df)} records")
        return len(df)
    except Exception as e:
        print(f"  Error loading to database: {e}")
        return 0


def get_db_stats(engine) -> Tuple[int, Optional[datetime], Optional[datetime]]:
    """Get current database statistics."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                'SELECT COUNT(*), MIN("timestamp"), MAX("timestamp") FROM argo_data'
            )).fetchone()
            return result[0], result[1], result[2]
    except Exception:
        return 0, None, None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch ARGO float data and load into PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_argo_data.py --region "Bay of Bengal" --days 30
  python fetch_argo_data.py --region "Arabian Sea" --days 90
  python fetch_argo_data.py --lat 13.0 --lon 80.0 --radius 500 --days 60
  python fetch_argo_data.py --all-regions --days 7
        """
    )
    
    # Region options
    parser.add_argument("--region", type=str, help="Named region (e.g., 'Bay of Bengal')")
    parser.add_argument("--all-regions", action="store_true", help="Fetch from all regions")
    
    # Custom coordinates
    parser.add_argument("--lat", type=float, help="Center latitude")
    parser.add_argument("--lon", type=float, help="Center longitude")
    parser.add_argument("--radius", type=float, default=300, help="Radius in km (default: 300)")
    
    # Bounds
    parser.add_argument("--lat-min", type=float, help="Minimum latitude")
    parser.add_argument("--lat-max", type=float, help="Maximum latitude")
    parser.add_argument("--lon-min", type=float, help="Minimum longitude")
    parser.add_argument("--lon-max", type=float, help="Maximum longitude")
    
    # Time range
    parser.add_argument("--days", type=int, default=30, help="Days of data to fetch (default: 30)")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    
    # Options
    parser.add_argument("--max-records", type=int, default=10000, help="Max records per region")
    parser.add_argument("--replace", action="store_true", help="Replace existing data")
    parser.add_argument("--stats", action="store_true", help="Show database stats only")
    
    args = parser.parse_args()
    
    # Initialize database
    try:
        engine = get_db_engine()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1
    
    # Show stats only
    if args.stats:
        count, min_date, max_date = get_db_stats(engine)
        print(f"\n📊 Database Statistics:")
        print(f"   Total records: {count:,}")
        print(f"   Date range: {min_date} to {max_date}")
        return 0
    
    # Determine date range
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=args.days)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    total_loaded = 0
    
    # Fetch from all regions
    if args.all_regions:
        for region_name, bounds in REGIONS.items():
            print(f"\n🌊 Fetching: {region_name.title()}")
            df = fetch_argo_data(
                bounds[0], bounds[1], bounds[2], bounds[3],
                start_date, end_date, args.max_records
            )
            if df is not None:
                loaded = load_to_database(df, engine, replace=False)
                total_loaded += loaded
    
    # Fetch from named region
    elif args.region:
        region_key = args.region.lower()
        if region_key not in REGIONS:
            print(f"❌ Unknown region: {args.region}")
            print(f"   Available: {', '.join(REGIONS.keys())}")
            return 1
        
        bounds = REGIONS[region_key]
        print(f"\n🌊 Fetching: {args.region}")
        df = fetch_argo_data(
            bounds[0], bounds[1], bounds[2], bounds[3],
            start_date, end_date, args.max_records
        )
        if df is not None:
            total_loaded = load_to_database(df, engine, args.replace)
    
    # Fetch from custom coordinates
    elif args.lat and args.lon:
        # Calculate bounds from center + radius
        km_per_deg = 111  # Approximate
        lat_delta = args.radius / km_per_deg
        lon_delta = args.radius / (km_per_deg * abs(math.cos(math.radians(args.lat))))
        
        lat_min = args.lat - lat_delta
        lat_max = args.lat + lat_delta
        lon_min = args.lon - lon_delta
        lon_max = args.lon + lon_delta
        
        print(f"\n🌊 Fetching: ({args.lat}, {args.lon}) ± {args.radius}km")
        df = fetch_argo_data(
            lat_min, lat_max, lon_min, lon_max,
            start_date, end_date, args.max_records
        )
        if df is not None:
            total_loaded = load_to_database(df, engine, args.replace)
    
    # Fetch from explicit bounds
    elif args.lat_min and args.lat_max and args.lon_min and args.lon_max:
        print(f"\n🌊 Fetching custom bounds")
        df = fetch_argo_data(
            args.lat_min, args.lat_max, args.lon_min, args.lon_max,
            start_date, end_date, args.max_records
        )
        if df is not None:
            total_loaded = load_to_database(df, engine, args.replace)
    
    else:
        parser.print_help()
        return 1
    
    # Final stats
    count, min_date, max_date = get_db_stats(engine)
    print(f"\n✅ Complete! Loaded {total_loaded:,} new records")
    print(f"📊 Total database records: {count:,}")
    
    return 0


if __name__ == "__main__":
    import math
    sys.exit(main())
