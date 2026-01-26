"""
Ifremer ARGO Data Fetcher
Fetches complete ARGO float data from Ifremer ERDDAP and uploads to Neon database
Uses weekly chunks to handle large data volumes
"""

import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import time
import sys

# Neon Database Connection
NEON_URL = "postgresql://neondb_owner:npg_oX6y9EBAqUYW@ep-lively-bread-a1z8k07p-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Ifremer ERDDAP
IFREMER_BASE = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"

# Fields to fetch (core fields only for stability)
FIELDS = "platform_number,time,latitude,longitude,pres,temp,psal"

def test_connection():
    """Test both Ifremer and Neon connections"""
    print("=" * 60)
    print("Testing Connections...")
    print("=" * 60)
    
    # Test Ifremer with small request
    try:
        r = requests.get(f"{IFREMER_BASE}?{FIELDS}&time>=2024-01-01&time<=2024-01-01T00:30:00Z", timeout=30)
        if r.status_code == 200:
            lines = r.text.strip().split('\n')
            print(f"[OK] Ifremer ERDDAP: OK ({len(lines)-2} test records)")
        else:
            print(f"[FAIL] Ifremer ERDDAP: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Ifremer ERDDAP: {e}")
        return False
    
    # Test Neon
    try:
        conn = psycopg2.connect(NEON_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM argo_data")
        count = cur.fetchone()[0]
        print(f"[OK] Neon Database: OK ({count:,} existing records)")
        conn.close()
    except psycopg2.errors.UndefinedTable:
        print(f"[OK] Neon Database: OK (table will be created)")
    except Exception as e:
        print(f"[FAIL] Neon Database: {e}")
        return False
    
    return True


def clear_database():
    """Clear all existing data from Neon"""
    print("\n" + "=" * 60)
    print("Clearing existing data from Neon...")
    print("=" * 60)
    
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    
    # Drop and recreate table with proper schema (no doxy/chla for now)
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
    cur.execute("CREATE INDEX idx_argo_timestamp ON argo_data(timestamp)")
    cur.execute("CREATE INDEX idx_argo_float_id ON argo_data(float_id)")
    cur.execute("CREATE INDEX idx_argo_location ON argo_data(latitude, longitude)")
    
    conn.commit()
    conn.close()
    print("[OK] Database cleared and table recreated with indexes")


def fetch_month_data(year, month):
    """Fetch one month of data from Ifremer in DAILY chunks"""
    start_date = datetime(year, month, 1)
    
    # Calculate end date (last day of month)
    if month == 12:
        end_date = datetime(year, 12, 31)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    all_records = []
    current = start_date
    
    while current <= end_date:
        # Fetch one day at a time
        day_start = current.strftime("%Y-%m-%dT00:00:00Z")
        day_end = current.strftime("%Y-%m-%dT23:59:59Z")
        
        url = f"{IFREMER_BASE}?{FIELDS}&time>={day_start}&time<={day_end}"
        
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(url, timeout=120)
                if response.status_code == 200:
                    records = parse_csv_data(response.text)
                    all_records.extend(records)
                    break
                elif response.status_code == 404:
                    break  # No data for this day
            except Exception:
                if attempt < 2:
                    time.sleep(2)
                continue
        
        current += timedelta(days=1)
    
    return all_records


def parse_csv_data(csv_text):
    """Parse CSV data into records"""
    lines = csv_text.strip().split('\n')
    if len(lines) < 3:
        return []
    
    records = []
    for line in lines[2:]:  # Skip header rows
        try:
            parts = line.split(',')
            if len(parts) >= 7:
                float_id = parts[0].strip()
                timestamp = parts[1].strip().replace('T', ' ').replace('Z', '')
                lat = float(parts[2]) if parts[2] else None
                lon = float(parts[3]) if parts[3] else None
                pres = float(parts[4]) if parts[4] and parts[4] != 'NaN' else None
                temp = float(parts[5]) if parts[5] and parts[5] != 'NaN' else None
                sal = float(parts[6]) if len(parts) > 6 and parts[6] and parts[6] != 'NaN' else None
                
                if float_id and lat is not None and lon is not None:
                    records.append((float_id, timestamp, lat, lon, pres, temp, sal))
        except (ValueError, IndexError):
            continue
    
    return records


def upload_batch(conn, records):
    """Upload a batch of records to Neon in smaller chunks"""
    if not records:
        return 0
    
    cur = conn.cursor()
    uploaded = 0
    chunk_size = 500  # Smaller chunks for stability
    
    query = """
        INSERT INTO argo_data (float_id, timestamp, latitude, longitude, pressure, temperature, salinity)
        VALUES %s
        ON CONFLICT (float_id, timestamp, pressure) DO NOTHING
    """
    
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            execute_values(cur, query, chunk, page_size=500)
            conn.commit()
            uploaded += len(chunk)
        except Exception as e:
            conn.rollback()
            # Try one by one for problematic chunks
            for record in chunk:
                try:
                    cur.execute("""
                        INSERT INTO argo_data (float_id, timestamp, latitude, longitude, pressure, temperature, salinity)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (float_id, timestamp, pressure) DO NOTHING
                    """, record)
                    conn.commit()
                    uploaded += 1
                except:
                    conn.rollback()
    
    return uploaded


def fetch_and_upload(start_year=2020, end_year=2026):
    """Main function to fetch all data and upload"""
    print("\n" + "=" * 60)
    print(f"Fetching ARGO data from Ifremer ({start_year}-{end_year})")
    print("=" * 60)
    
    total_records = 0
    start_time = time.time()
    
    for year in range(start_year, end_year + 1):
        print(f"\n[YEAR {year}]")
        year_records = 0
        
        for month in range(1, 13):
            # Skip future months
            now = datetime.now()
            if year > now.year or (year == now.year and month > now.month):
                continue
            
            print(f"  {year}-{month:02d}...", end=" ", flush=True)
            
            # Reconnect for each month to avoid connection issues
            try:
                conn = psycopg2.connect(NEON_URL)
            except Exception as e:
                print(f"[DB ERROR] {e}")
                time.sleep(5)
                try:
                    conn = psycopg2.connect(NEON_URL)
                except:
                    print("[SKIP]")
                    continue
            
            records = fetch_month_data(year, month)
            if records:
                uploaded = upload_batch(conn, records)
                year_records += uploaded
                print(f"[OK] {uploaded:,} records")
            else:
                print("[NO DATA]")
            
            conn.close()
            time.sleep(0.5)  # Be nice to servers
        
        total_records += year_records
        print(f"  Year {year} total: {year_records:,} records")
        
        # Progress update
        elapsed = time.time() - start_time
        print(f"  Running total: {total_records:,} | Elapsed: {elapsed/60:.1f} min")
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"[COMPLETE]")
    print(f"   Total records: {total_records:,}")
    print(f"   Time elapsed: {elapsed/60:.1f} minutes")
    print("=" * 60)
    
    return total_records


def verify_data():
    """Verify the uploaded data"""
    print("\n" + "=" * 60)
    print("Verifying uploaded data...")
    print("=" * 60)
    
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM argo_data")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT float_id) FROM argo_data")
    floats = cur.fetchone()[0]
    
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM argo_data")
    date_range = cur.fetchone()
    
    cur.execute("SELECT MIN(temperature), MAX(temperature), AVG(temperature) FROM argo_data WHERE temperature IS NOT NULL")
    temp = cur.fetchone()
    
    cur.execute("SELECT MIN(salinity), MAX(salinity), AVG(salinity) FROM argo_data WHERE salinity IS NOT NULL")
    sal = cur.fetchone()
    
    conn.close()
    
    print(f"Total Records: {total:,}")
    print(f"Unique Floats: {floats:,}")
    print(f"Date Range: {date_range[0]} to {date_range[1]}")
    if temp[0]:
        print(f"Temperature: {temp[0]:.2f}C to {temp[1]:.2f}C (avg: {temp[2]:.2f}C)")
    if sal[0]:
        print(f"Salinity: {sal[0]:.2f} to {sal[1]:.2f} PSU (avg: {sal[2]:.2f} PSU)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IFREMER ARGO DATA FETCHER")
    print("=" * 60)
    
    # Test connections first
    if not test_connection():
        print("\n[FAIL] Connection test failed. Aborting.")
        sys.exit(1)
    
    # Ask for confirmation
    print("\n[WARNING] This will:")
    print("   1. DELETE all existing data in Neon database")
    print("   2. Download fresh data from Ifremer (2020-2026)")
    print("   3. Upload to Neon database")
    print("\n   This may take 30-60 minutes.")
    
    confirm = input("\nProceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        sys.exit(0)
    
    # Clear database
    clear_database()
    
    # Fetch and upload
    fetch_and_upload(2020, 2026)
    
    # Verify
    verify_data()
    
    print("\n[DONE] All complete!")
