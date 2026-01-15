"""
FloatChart - Local Database Setup
Creates the PostgreSQL database schema for local development.

Usage:
    python setup_local_db.py
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DATA_GENERATOR.env_utils import load_environment

# SQL to create the argo_data table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS argo_data (
    id SERIAL PRIMARY KEY,
    float_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    dissolved_oxygen DOUBLE PRECISION
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_argo_float_id ON argo_data(float_id);
CREATE INDEX IF NOT EXISTS idx_argo_timestamp ON argo_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_argo_location ON argo_data(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_argo_temp ON argo_data(temperature);
"""


def main():
    print("=" * 50)
    print("FloatChart - Local Database Setup")
    print("=" * 50)
    
    # Load environment
    load_environment()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("\n❌ DATABASE_URL not set!")
        print("\nPlease create a .env file with your PostgreSQL connection:")
        print("-" * 50)
        print("DATABASE_URL=postgresql://postgres:your_password@localhost:5432/argo_chatbot")
        print("-" * 50)
        print("\nOr for Supabase:")
        print("-" * 50)
        print("DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres")
        print("-" * 50)
        return 1
    
    # Mask password in output
    display_url = database_url
    if "@" in database_url:
        parts = database_url.split("@")
        user_part = parts[0].rsplit(":", 1)[0]
        display_url = f"{user_part}:****@{parts[1]}"
    
    print(f"\n📦 Connecting to: {display_url}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version()")).fetchone()
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {result[0][:50]}...")
            
            # Create table
            print(f"\n📋 Creating argo_data table...")
            conn.execute(text(CREATE_TABLE_SQL))
            conn.commit()
            print("✅ Table created successfully")
            
            # Check current data
            result = conn.execute(text("SELECT COUNT(*) FROM argo_data")).fetchone()
            count = result[0]
            
            if count > 0:
                print(f"\n📊 Current data: {count:,} records")
                
                result = conn.execute(text(
                    'SELECT MIN("timestamp"), MAX("timestamp") FROM argo_data'
                )).fetchone()
                print(f"   Date range: {result[0]} to {result[1]}")
                
                result = conn.execute(text(
                    'SELECT COUNT(DISTINCT float_id) FROM argo_data'
                )).fetchone()
                print(f"   Unique floats: {result[0]}")
            else:
                print(f"\n📊 Database is empty. Use fetch_argo_data.py to add data:")
                print("   python fetch_argo_data.py --region 'Bay of Bengal' --days 30")
        
        print("\n" + "=" * 50)
        print("✅ Setup complete!")
        print("=" * 50)
        print("\nNext steps:")
        print("  1. Fetch ARGO data:")
        print("     python fetch_argo_data.py --region 'Bay of Bengal' --days 30")
        print("")
        print("  2. Or use the GUI:")
        print("     python gui.py")
        print("")
        print("  3. Run the web app:")
        print("     cd ../ARGO_CHATBOT && python app.py")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Check your DATABASE_URL in .env")
        print("  3. Ensure the database exists")
        return 1


if __name__ == "__main__":
    sys.exit(main())
