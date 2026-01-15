"""
Generate massive ARGO float data - targeting 1M+ additional records.
More floats per region, more years of data, denser profiles.
"""

import requests
import random
import json
import math
from datetime import datetime, timedelta
import time

SUPABASE_URL = "https://khrqbfssaanpcxdnnplc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtocnFiZnNzYWFucGN4ZG5ucGxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0NTQxMTAsImV4cCI6MjA4NDAzMDExMH0.1M6nzLx67qy6Ash92k3jHxpuJ8QvyCyKt2m5w_L_M7s"

# Extended regions with more coverage
REGIONS = {
    # Indian Ocean (dense coverage)
    "arabian_sea_north": {"lat": (18, 25), "lon": (55, 70), "base_temp": 26},
    "arabian_sea_south": {"lat": (5, 18), "lon": (50, 70), "base_temp": 28},
    "bay_of_bengal_north": {"lat": (15, 22), "lon": (85, 92), "base_temp": 28},
    "bay_of_bengal_south": {"lat": (5, 15), "lon": (80, 92), "base_temp": 29},
    "indian_equatorial": {"lat": (-5, 5), "lon": (55, 95), "base_temp": 29},
    "indian_subtropical": {"lat": (-30, -15), "lon": (50, 100), "base_temp": 20},
    "mozambique_channel": {"lat": (-25, -12), "lon": (35, 48), "base_temp": 25},
    
    # Pacific Ocean (largest ocean)
    "kuroshio_current": {"lat": (25, 40), "lon": (125, 150), "base_temp": 22},
    "pacific_warm_pool": {"lat": (-8, 8), "lon": (140, 180), "base_temp": 29},
    "coral_triangle": {"lat": (-10, 10), "lon": (100, 135), "base_temp": 28},
    "east_pacific": {"lat": (-5, 15), "lon": (-130, -80), "base_temp": 25},
    "california_current": {"lat": (25, 45), "lon": (-130, -115), "base_temp": 16},
    "humboldt_current": {"lat": (-40, -15), "lon": (-85, -70), "base_temp": 15},
    "south_pacific_gyre": {"lat": (-35, -15), "lon": (-140, -100), "base_temp": 20},
    
    # Atlantic Ocean
    "gulf_stream": {"lat": (30, 45), "lon": (-78, -50), "base_temp": 22},
    "sargasso_sea": {"lat": (25, 35), "lon": (-70, -40), "base_temp": 24},
    "canary_current": {"lat": (20, 35), "lon": (-25, -10), "base_temp": 20},
    "benguela_current": {"lat": (-30, -15), "lon": (5, 18), "base_temp": 16},
    "brazil_current": {"lat": (-35, -20), "lon": (-50, -35), "base_temp": 22},
    "caribbean_west": {"lat": (15, 22), "lon": (-88, -78), "base_temp": 28},
    "caribbean_east": {"lat": (12, 20), "lon": (-70, -58), "base_temp": 27},
    "med_west": {"lat": (35, 42), "lon": (-5, 10), "base_temp": 18},
    "med_east": {"lat": (32, 40), "lon": (15, 35), "base_temp": 22},
    
    # Southern Ocean
    "antarctic_circumpolar_atlantic": {"lat": (-58, -48), "lon": (-50, 20), "base_temp": 3},
    "antarctic_circumpolar_indian": {"lat": (-58, -48), "lon": (20, 120), "base_temp": 2},
    "antarctic_circumpolar_pacific": {"lat": (-58, -48), "lon": (120, 180), "base_temp": 2},
    
    # Arctic & sub-arctic
    "nordic_seas": {"lat": (62, 75), "lon": (-20, 20), "base_temp": 6},
    "labrador_sea": {"lat": (55, 65), "lon": (-60, -45), "base_temp": 4},
    "bering_sea": {"lat": (52, 62), "lon": (165, 180), "base_temp": 5},
}

FLOAT_ID_START = 2700000

def get_count():
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/argo_data?select=count", 
                        headers={"apikey": SUPABASE_KEY, "Prefer": "count=exact"})
        return int(r.headers.get('content-range', '*/0').split('/')[-1])
    except:
        return 0

def generate_profiles(float_id, config, start_date, num_profiles):
    records = []
    lat_min, lat_max = config["lat"]
    lon_min, lon_max = config["lon"]
    base_temp = config["base_temp"]
    
    lat = random.uniform(lat_min, lat_max)
    lon = random.uniform(lon_min, lon_max)
    
    # More pressure levels for detailed profiles
    pressures = [2, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 400, 500, 700, 1000, 1500, 2000]
    
    current_time = start_date
    
    for _ in range(num_profiles):
        lat += random.uniform(-0.2, 0.2)
        lon += random.uniform(-0.2, 0.2)
        lat = max(lat_min, min(lat_max, lat))
        lon = max(lon_min, min(lon_max, lon))
        
        current_time += timedelta(days=random.randint(5, 10))
        month = current_time.month
        seasonal = 3 * math.sin((month - 3) * math.pi / 6)
        
        for pressure in pressures:
            if pressure < 50:
                temp = base_temp + seasonal + random.uniform(-1, 1)
            elif pressure < 300:
                temp = base_temp - pressure/40 + seasonal*0.5 + random.uniform(-0.5, 0.5)
            else:
                temp = max(1.5, 8 - pressure/300 + random.uniform(-0.3, 0.3))
            
            salinity = 34.5 + (pressure/1000)*0.5 + random.uniform(-0.3, 0.3)
            
            if pressure < 100:
                oxygen = 220 + random.uniform(-15, 15)
            elif pressure < 600:
                oxygen = max(40, 180 - pressure*0.25 + random.uniform(-10, 10))
            else:
                oxygen = max(60, 80 + (pressure-600)*0.05 + random.uniform(-10, 10))
            
            records.append({
                "float_id": float_id,
                "timestamp": current_time.isoformat(),
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "pressure": pressure,
                "temperature": round(temp, 2),
                "salinity": round(salinity, 3),
                "dissolved_oxygen": round(oxygen, 1)
            })
    
    return records

def upload_batch(records):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/argo_data", headers=headers, json=records, timeout=30)
        return r.status_code in [200, 201]
    except:
        return False

def main():
    print("=" * 70)
    print("MASSIVE DATA GENERATOR - Targeting 1M+ Records")
    print("=" * 70)
    
    initial = get_count()
    print(f"\nCurrent: {initial:,} records")
    
    # Generate 6 years of data with more floats
    years = [
        (datetime(2020, 1, 1), datetime(2020, 12, 31)),
        (datetime(2021, 1, 1), datetime(2021, 12, 31)),
        (datetime(2022, 1, 1), datetime(2022, 12, 31)),
        (datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2024, 1, 1), datetime(2024, 12, 31)),
        (datetime(2025, 1, 1), datetime(2026, 1, 15)),
    ]
    
    float_id = FLOAT_ID_START
    total_uploaded = 0
    
    for year_start, year_end in years:
        year = year_start.year
        print(f"\n--- Generating {year} ---")
        
        year_records = []
        
        for region_name, config in REGIONS.items():
            # 8-12 floats per region per year
            num_floats = random.randint(8, 12)
            
            for _ in range(num_floats):
                start_offset = random.randint(0, 150)
                start_date = year_start + timedelta(days=start_offset)
                num_profiles = random.randint(25, 40)
                
                records = generate_profiles(float_id, config, start_date, num_profiles)
                year_records.extend(records)
                float_id += 1
        
        print(f"  Generated: {len(year_records):,} records")
        
        # Upload in batches
        batch_size = 1000
        batches = [year_records[i:i+batch_size] for i in range(0, len(year_records), batch_size)]
        
        success = 0
        for i, batch in enumerate(batches, 1):
            if upload_batch(batch):
                success += len(batch)
            if i % 50 == 0:
                print(f"    Uploaded {i}/{len(batches)} batches")
            if i % 100 == 0:
                time.sleep(0.5)
        
        total_uploaded += success
        print(f"  Uploaded: {success:,} records")
    
    time.sleep(2)
    final = get_count()
    
    print(f"\n{'=' * 70}")
    print(f"COMPLETE!")
    print(f"  Before: {initial:,}")
    print(f"  Added:  {total_uploaded:,}")
    print(f"  Total:  {final:,}")
    print(f"  Floats: {float_id - FLOAT_ID_START:,}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
