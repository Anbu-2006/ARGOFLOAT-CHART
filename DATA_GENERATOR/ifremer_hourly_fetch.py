"""
Ifremer ARGO Data Fetcher - Hourly Chunks
Downloads data from Ifremer ERDDAP in small hourly chunks to avoid timeouts
"""
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import time
import sys

# Database config
DB_URL = "postgresql://neondb_owner:npg_oX6y9EBAqUYW@ep-lively-bread-a1z8k07p-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Ifremer ERDDAP base URL
BASE_URL = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"
FIELDS = "platform_number,time,latitude,longitude,pres,temp,psal"

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DB_URL)

def setup_table():
    """Create/recreate the argo_data table"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS argo_data CASCADE")
    cur.execute("""
        CREATE TABLE argo_data (
            id SERIAL PRIMARY KEY,
            float_id VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            pressure FLOAT,
            temperature FLOAT,
            salinity FLOAT,
            UNIQUE(float_id, timestamp, pressure)
        )
    """)
    
    # Create indexes
    cur.execute("CREATE INDEX idx_argo_float_id ON argo_data(float_id)")
    cur.execute("CREATE INDEX idx_argo_timestamp ON argo_data(timestamp)")
    cur.execute("CREATE INDEX idx_argo_location ON argo_data(latitude, longitude)")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table created successfully")

def fetch_hour(start_time, end_time, retry=3):
    """Fetch data for a specific hour"""
    url = f"{BASE_URL}?{FIELDS}&time>={start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}&time<{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    for attempt in range(retry):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) > 2:  # Has data (header + units + data)
                    return lines[2:]  # Skip header and units
                return []
            elif response.status_code == 404:
                return []  # No data for this period
            else:
                print(f"    HTTP {response.status_code}, retry {attempt + 1}")
        except requests.exceptions.Timeout:
            print(f"    Timeout, retry {attempt + 1}")
        except Exception as e:
            print(f"    Error: {str(e)[:50]}, retry {attempt + 1}")
        time.sleep(2 * (attempt + 1))
    
    return None  # Failed after retries

def parse_row(line):
    """Parse a CSV line into a record"""
    try:
        parts = line.split(',')
        if len(parts) >= 7:
            float_id = parts[0].strip()
            timestamp = parts[1].strip()
            lat = float(parts[2]) if parts[2] else None
            lon = float(parts[3]) if parts[3] else None
            pres = float(parts[4]) if parts[4] else None
            temp = float(parts[5]) if parts[5] else None
            sal = float(parts[6]) if parts[6] else None
            
            if float_id and timestamp and lat is not None and lon is not None:
                return (float_id, timestamp, lat, lon, pres, temp, sal)
    except Exception:
        pass
    return None

def upload_batch(records, conn):
    """Upload a batch of records to database"""
    if not records:
        return 0
    
    cur = conn.cursor()
    try:
        execute_values(
            cur,
            """INSERT INTO argo_data (float_id, timestamp, latitude, longitude, pressure, temperature, salinity)
               VALUES %s ON CONFLICT (float_id, timestamp, pressure) DO NOTHING""",
            records,
            page_size=500
        )
        conn.commit()
        return len(records)
    except Exception as e:
        conn.rollback()
        print(f"    Upload error: {str(e)[:50]}")
        return 0
    finally:
        cur.close()

def get_current_count():
    """Get current record count"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM argo_data")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except:
        return 0

def fetch_date_range(start_date, end_date):
    """Fetch data for a date range in hourly chunks"""
    total_uploaded = 0
    current = start_date
    
    conn = get_db_connection()
    
    while current < end_date:
        hour_end = current + timedelta(hours=1)
        
        print(f"  {current.strftime('%Y-%m-%d %H:%M')} - {hour_end.strftime('%H:%M')}", end=" ")
        sys.stdout.flush()
        
        lines = fetch_hour(current, hour_end)
        
        if lines is None:
            print("❌ FAILED")
        elif len(lines) == 0:
            print("(no data)")
        else:
            # Parse and upload
            records = [parse_row(line) for line in lines]
            records = [r for r in records if r is not None]
            
            uploaded = upload_batch(records, conn)
            total_uploaded += uploaded
            print(f"✅ {uploaded:,} records")
        
        current = hour_end
        time.sleep(0.5)  # Rate limiting
    
    conn.close()
    return total_uploaded

def main():
    print("=" * 60)
    print("IFREMER ARGO DATA FETCHER - Hourly Chunks")
    print("=" * 60)
    
    # Setup table
    print("\n📦 Setting up database table...")
    setup_table()
    
    # Define date ranges - fetch last 2 years of data
    # Start with recent data first
    years_to_fetch = [
        (datetime(2024, 1, 1), datetime(2024, 12, 31)),
        (datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2022, 1, 1), datetime(2022, 12, 31)),
    ]
    
    total = 0
    
    for start, end in years_to_fetch:
        print(f"\n📅 Fetching {start.year}...")
        
        # Process month by month
        current_month = start
        while current_month < end:
            month_end = min(
                datetime(current_month.year, current_month.month + 1, 1) if current_month.month < 12 
                else datetime(current_month.year + 1, 1, 1),
                end
            )
            
            print(f"\n📆 Month: {current_month.strftime('%B %Y')}")
            uploaded = fetch_date_range(current_month, month_end)
            total += uploaded
            
            current_count = get_current_count()
            print(f"   Month total: {uploaded:,} | Database total: {current_count:,}")
            
            current_month = month_end
    
    # Final count
    final_count = get_current_count()
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Total records in database: {final_count:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
