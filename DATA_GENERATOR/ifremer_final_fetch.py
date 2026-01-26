"""
Ifremer ARGO Data Fetcher - Final Robust Version
Downloads data with automatic resume, handles intermittent connectivity
"""
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import time
import sys
import random

# Database config
DB_URL = "postgresql://neondb_owner:npg_oX6y9EBAqUYW@ep-lively-bread-a1z8k07p-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Ifremer ERDDAP base URL
BASE_URL = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"
FIELDS = "platform_number,time,latitude,longitude,pres,temp,psal"

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DB_URL)

def ensure_table():
    """Ensure the argo_data table exists"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS argo_data (
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
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_argo_float_id ON argo_data(float_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_argo_timestamp ON argo_data(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_argo_location ON argo_data(latitude, longitude)")
    
    conn.commit()
    cur.close()
    conn.close()

def get_last_timestamp():
    """Get the last timestamp in the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM argo_data")
        result = cur.fetchone()[0]
        cur.close()
        conn.close()
        return result
    except:
        return None

def fetch_period(session, start_time, end_time, max_retries=10):
    """Fetch data for a time period with robust retry logic"""
    url = f"{BASE_URL}?{FIELDS}&time>={start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}&time<{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=180)
            
            if response.status_code == 200:
                content = response.text
                lines = content.strip().split('\n')
                if len(lines) > 2:
                    return lines[2:]  # Skip header and units
                return []
            elif response.status_code == 404:
                return []
            else:
                print(f"HTTP {response.status_code}", end=" ")
                
        except requests.exceptions.SSLError:
            print(f"SSL", end=" ")
        except requests.exceptions.ConnectionError:
            print(f"Conn", end=" ")
        except requests.exceptions.Timeout:
            print(f"Timeout", end=" ")
        except requests.exceptions.ChunkedEncodingError:
            print(f"Chunk", end=" ")
        except Exception as e:
            print(f"{type(e).__name__[:10]}", end=" ")
        
        wait_time = min(5 * (2 ** attempt) + random.random() * 5, 120)
        print(f"wait {wait_time:.0f}s", end=" ")
        sys.stdout.flush()
        time.sleep(wait_time)
    
    return None

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
    except:
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
        print(f"DB:{str(e)[:20]}", end=" ")
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

def fetch_day(day_start, session, conn):
    """Fetch a full day of data in 30-minute chunks"""
    total = 0
    current = day_start
    day_end = day_start + timedelta(days=1)
    
    while current < day_end:
        period_end = current + timedelta(minutes=30)
        
        print(f"  {current.strftime('%H:%M')}", end=" ")
        sys.stdout.flush()
        
        lines = fetch_period(session, current, period_end)
        
        if lines is None:
            print("FAIL", end=" | ")
        elif len(lines) == 0:
            print("empty", end=" | ")
        else:
            records = [parse_row(line) for line in lines]
            records = [r for r in records if r is not None]
            uploaded = upload_batch(records, conn)
            total += uploaded
            print(f"{uploaded:,}", end=" | ")
        
        sys.stdout.flush()
        current = period_end
        time.sleep(0.5)
    
    return total

def main():
    print("=" * 60)
    print("IFREMER ARGO DATA FETCHER - Final Version")
    print("=" * 60)
    
    ensure_table()
    
    initial_count = get_current_count()
    print(f"\n📊 Current records: {initial_count:,}")
    
    # Determine start date
    last_ts = get_last_timestamp()
    if last_ts:
        # Start from the next 30-min period after last timestamp
        start_date = datetime(last_ts.year, last_ts.month, last_ts.day)
        start_date += timedelta(days=1)  # Start from next day to be safe
        print(f"📅 Resuming from: {start_date.strftime('%Y-%m-%d')}")
    else:
        start_date = datetime(2024, 1, 1)
        print(f"📅 Starting from: {start_date}")
    
    # Define date range to fetch - for now let's get 2024
    end_date = datetime(2024, 12, 31)
    
    # Create session
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    # Connect to database
    conn = get_db_connection()
    
    current_day = start_date
    while current_day < end_date:
        print(f"\n📆 {current_day.strftime('%Y-%m-%d')}: ", end="")
        
        day_total = fetch_day(current_day, session, conn)
        
        db_count = get_current_count()
        print(f"\n   Day total: {day_total:,} | DB total: {db_count:,}")
        
        current_day += timedelta(days=1)
        
        # Brief pause between days
        time.sleep(1)
    
    conn.close()
    
    final_count = get_current_count()
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Total records: {final_count:,}")
    print(f"   New records added: {final_count - initial_count:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
