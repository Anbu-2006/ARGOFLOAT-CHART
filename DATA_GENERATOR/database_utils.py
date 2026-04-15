"""
FloatChart - Database Utilities for Data Management
Handles all database operations for the DATA_GENERATOR module.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

# Load environment from .env file (check multiple locations)
def load_environment():
    """Load .env from project root or current directory."""
    env_paths = [
        Path(".env"),
        Path("../.env"),
        Path("../../.env"),
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent / "ARGO_CHATBOT" / ".env",
    ]
    for p in env_paths:
        if p.exists():
            load_dotenv(p, override=False)
            return True
    load_dotenv()
    return False


def get_db_engine():
    """Create SQLAlchemy engine for database operations."""
    load_environment()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return None
    
    try:
        engine = create_engine(
            db_url,
            isolation_level="AUTOCOMMIT",
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def get_db_connection():
    """Get raw psycopg2 connection for bulk operations."""
    load_environment()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return None
    
    try:
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def init_database():
    """Initialize the argo_data table with proper schema."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create table with CockroachDB compatibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS argo_data (
                id INT8 DEFAULT unique_rowid() PRIMARY KEY,
                float_id INT8,
                timestamp TIMESTAMP,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                temperature DOUBLE PRECISION,
                salinity DOUBLE PRECISION,
                pressure DOUBLE PRECISION,
                UNIQUE(float_id, timestamp, pressure)
            )
        """)
        
        # Create indexes for common queries - OPTIMIZED for deployed performance
        # Primary indexes for individual columns
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_argo_timestamp ON argo_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_argo_float ON argo_data(float_id)",
            "CREATE INDEX IF NOT EXISTS idx_argo_location ON argo_data(latitude, longitude)",
        ]
        
        # COMPOSITE INDEXES for faster complex queries (CockroachDB compatible - NO INCLUDE clause)
        composite_indexes = [
            # For trajectory/profile queries: SELECT ... WHERE float_id = X ORDER BY timestamp
            "CREATE INDEX IF NOT EXISTS idx_argo_float_time ON argo_data(float_id, timestamp DESC)",
            # For proximity queries with time filter: bounding box + time range
            "CREATE INDEX IF NOT EXISTS idx_argo_geo_time ON argo_data(latitude, longitude, timestamp DESC)",
            # For time-series queries: timestamp range with location
            "CREATE INDEX IF NOT EXISTS idx_argo_time_geo ON argo_data(timestamp, latitude, longitude)",
            # For map latest-per-float query: covering index for DISTINCT ON queries
            "CREATE INDEX IF NOT EXISTS idx_argo_float_time_lat_lon ON argo_data(float_id, timestamp DESC, latitude, longitude)",
            # For statistics queries: temperature/salinity with location
            "CREATE INDEX IF NOT EXISTS idx_argo_geo_temp ON argo_data(latitude, longitude, temperature, salinity)",
        ]
        
        for idx_sql in indexes + composite_indexes:
            try:
                cursor.execute(idx_sql)
            except Exception:
                pass  # Index may already exist or syntax differs
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


def get_database_stats():
    """Get statistics about the current database."""
    engine = get_db_engine()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT float_id) as unique_floats,
                    MIN(timestamp) as min_date,
                    MAX(timestamp) as max_date,
                    ROUND(AVG(temperature)::numeric, 2) as avg_temp,
                    ROUND(AVG(salinity)::numeric, 2) as avg_salinity
                FROM argo_data
            """))
            row = result.fetchone()
            
            return {
                "total_records": row[0] or 0,
                "unique_floats": row[1] or 0,
                "min_date": row[2].isoformat() if row[2] else None,
                "max_date": row[3].isoformat() if row[3] else None,
                "avg_temperature": float(row[4]) if row[4] else None,
                "avg_salinity": float(row[5]) if row[5] else None
            }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None


def clear_all_data(confirm=False):
    """Clear all data from the argo_data table."""
    if not confirm:
        print("⚠️  Please confirm deletion by passing confirm=True")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM argo_data")
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ All data cleared")
        return True
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return False


def bulk_insert(data_tuples, page_size=1000):
    """
    Bulk insert data into argo_data table.
    
    Args:
        data_tuples: List of tuples (float_id, timestamp, lat, lon, temp, sal, pressure)
        page_size: Number of rows per batch
    
    Returns:
        Number of rows inserted
    """
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        
        insert_sql = """
            INSERT INTO argo_data (float_id, timestamp, latitude, longitude, temperature, salinity, pressure)
            VALUES %s
            ON CONFLICT (float_id, timestamp, pressure) DO NOTHING
        """
        
        execute_values(cursor, insert_sql, data_tuples, page_size=page_size)
        conn.commit()
        
        rows_inserted = cursor.rowcount if cursor.rowcount > 0 else len(data_tuples)
        
        cursor.close()
        conn.close()
        
        return rows_inserted
    except Exception as e:
        print(f"❌ Bulk insert error: {e}")
        return 0


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    load_environment()
    
    engine = get_db_engine()
    if engine:
        print("✅ Database connection successful!")
        
        stats = get_database_stats()
        if stats:
            print(f"\n📊 Database Statistics:")
            print(f"   Total Records: {stats['total_records']:,}")
            print(f"   Unique Floats: {stats['unique_floats']:,}")
            print(f"   Date Range: {stats['min_date']} to {stats['max_date']}")
    else:
        print("❌ Database connection failed")
