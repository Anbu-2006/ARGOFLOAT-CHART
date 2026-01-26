"""
Ifremer ARGO Data Fetcher - Resilient Version
Downloads data with automatic resume capability and robust error handling
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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

def create_session():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

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
    
    # Create indexes if not exists
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

def fetch_hour(session, start_time, end_time):
    """Fetch data for a specific hour with robust error handling"""
    url = f"{BASE_URL}?{FIELDS}&time>={start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}&time<{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    for attempt in range(5):
        try:
            response = session.get(url, timeout=180, stream=True)
            
            if response.status_code == 200:
                # Read with timeout protection
                content = ""
                for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                    if chunk:
                        content += chunk
                
                lines = content.strip().split('\n')
                if len(lines) > 2:
                    return lines[2:]  # Skip header and units
                return []
            elif response.status_code == 404:
                return []
            else:
                print(f"    HTTP {response.status_code}", end="")
                
        except requests.exceptions.ChunkedEncodingError:
            print(f"    Chunk error", end="")
        except requests.exceptions.ConnectionError:
            print(f"    Conn error", end="")
        except requests.exceptions.Timeout:
            print(f"    Timeout", end="")
        except Exception as e:
            print(f"    {type(e).__name__}", end="")
        
        wait_time = 5 * (attempt + 1)
        print(f", wait {wait_time}s", end="")
        sys.stdout.flush()
        time.sleep(wait_time)
    
    return None  # Failed after all retries

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
        print(f"    DB error: {str(e)[:30]}", end="")
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

def fetch_date_range(start_date, end_date, session):
    """Fetch data for a date range in hourly chunks"""
    total_uploaded = 0
    current = start_date
    errors = 0
    max_consecutive_errors = 10
    
    conn = get_db_connection()
    
    while current < end_date:
        hour_end = current + timedelta(hours=1)
        
        print(f"  {current.strftime('%Y-%m-%d %H:%M')}", end=" ")
        sys.stdout.flush()
        
        lines = fetch_hour(session, current, hour_end)
        
        if lines is None:
            print(" ❌")
            errors += 1
            if errors >= max_consecutive_errors:
                print(f"⚠️  Too many errors, pausing for 2 minutes...")
                time.sleep(120)
                errors = 0
                session = create_session()  # Create new session
        elif len(lines) == 0:
            print(" (empty)")
            errors = 0
        else:
            records = [parse_row(line) for line in lines]
            records = [r for r in records if r is not None]
            
            uploaded = upload_batch(records, conn)
            total_uploaded += uploaded
            print(f" ✅ {uploaded:,}")
            errors = 0
        
        current = hour_end
        time.sleep(0.3)  # Rate limiting
    
    conn.close()
    return total_uploaded

def main():
    print("=" * 60)
    print("IFREMER ARGO DATA FETCHER - Resilient Version")
    print("=" * 60)
    
    # Ensure table exists
    print("\n📦 Checking database table...")
    ensure_table()
    
    # Check existing data
    initial_count = get_current_count()
    print(f"📊 Current records: {initial_count:,}")
    
    # Check if we should resume
    last_ts = get_last_timestamp()
    if last_ts:
        print(f"📅 Last timestamp: {last_ts}")
        # Start from the hour after the last timestamp
        resume_from = datetime(last_ts.year, last_ts.month, last_ts.day, last_ts.hour) + timedelta(hours=1)
        print(f"▶️  Resuming from: {resume_from}")
    else:
        resume_from = datetime(2024, 1, 1)
        print(f"▶️  Starting fresh from: {resume_from}")
    
    # Create session
    session = create_session()
    
    # Define end date
    end_date = datetime(2024, 12, 31, 23, 59, 59)
    
    # Process month by month
    current = resume_from
    while current < end_date:
        month_end = min(
            datetime(current.year, current.month + 1, 1) if current.month < 12 
            else datetime(current.year + 1, 1, 1),
            end_date
        )
        
        print(f"\n📆 {current.strftime('%B %Y')}")
        uploaded = fetch_date_range(current, month_end, session)
        
        current_count = get_current_count()
        print(f"   Month: {uploaded:,} | Total: {current_count:,}")
        
        current = month_end
    
    # Final count
    final_count = get_current_count()
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Total records: {final_count:,}")
    print(f"   New records added: {final_count - initial_count:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
