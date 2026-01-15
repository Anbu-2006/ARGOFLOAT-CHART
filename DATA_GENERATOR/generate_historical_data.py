"""
Generate comprehensive ARGO float historical data (2020-2026) and upload to Supabase.
Target: ~1.2 million records to maximize usage while leaving buffer.
"""

import requests
import random
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time

# Supabase REST API config
SUPABASE_URL = "https://khrqbfssaanpcxdnnplc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtocnFiZnNzYWFucGN4ZG5ucGxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0NTQxMTAsImV4cCI6MjA4NDAzMDExMH0.1M6nzLx67qy6Ash92k3jHxpuJ8QvyCyKt2m5w_L_M7s"

# All ocean regions for comprehensive coverage
GLOBAL_REGIONS = {
    # Indian Ocean
    "arabian_sea": {"lat": (8, 24), "lon": (52, 74), "base_temp": 27},
    "bay_of_bengal": {"lat": (6, 21), "lon": (81, 94), "base_temp": 28},
    "indian_central": {"lat": (-15, 5), "lon": (55, 90), "base_temp": 28},
    "indian_south": {"lat": (-35, -15), "lon": (40, 100), "base_temp": 18},
    
    # Pacific Ocean
    "pacific_equatorial": {"lat": (-5, 5), "lon": (140, 180), "base_temp": 29},
    "pacific_north_west": {"lat": (25, 50), "lon": (130, 180), "base_temp": 16},
    "pacific_north_east": {"lat": (25, 50), "lon": (-160, -120), "base_temp": 15},
    "pacific_south_west": {"lat": (-45, -20), "lon": (150, 180), "base_temp": 14},
    "pacific_south_east": {"lat": (-45, -20), "lon": (-120, -70), "base_temp": 13},
    "south_china_sea": {"lat": (5, 22), "lon": (105, 120), "base_temp": 27},
    "philippine_sea": {"lat": (10, 30), "lon": (125, 140), "base_temp": 26},
    
    # Atlantic Ocean
    "atlantic_north_west": {"lat": (30, 50), "lon": (-75, -40), "base_temp": 18},
    "atlantic_north_east": {"lat": (30, 55), "lon": (-40, -5), "base_temp": 16},
    "atlantic_equatorial": {"lat": (-5, 10), "lon": (-40, 5), "base_temp": 27},
    "atlantic_south_west": {"lat": (-40, -15), "lon": (-55, -25), "base_temp": 16},
    "atlantic_south_east": {"lat": (-35, -15), "lon": (-15, 15), "base_temp": 17},
    "caribbean": {"lat": (12, 22), "lon": (-85, -62), "base_temp": 28},
    "gulf_of_mexico": {"lat": (20, 28), "lon": (-96, -82), "base_temp": 26},
    "mediterranean": {"lat": (32, 44), "lon": (-4, 34), "base_temp": 20},
    "north_sea": {"lat": (52, 60), "lon": (-3, 8), "base_temp": 10},
    
    # Southern Ocean
    "southern_atlantic": {"lat": (-60, -45), "lon": (-60, 20), "base_temp": 3},
    "southern_indian": {"lat": (-60, -45), "lon": (20, 120), "base_temp": 2},
    "southern_pacific": {"lat": (-60, -45), "lon": (120, 180), "base_temp": 2},
    
    # Other regions
    "red_sea": {"lat": (14, 28), "lon": (34, 42), "base_temp": 28},
    "persian_gulf": {"lat": (24, 30), "lon": (48, 56), "base_temp": 30},
    "coral_sea": {"lat": (-22, -10), "lon": (148, 162), "base_temp": 25},
    "tasman_sea": {"lat": (-42, -32), "lon": (152, 172), "base_temp": 16},
}

# Float ID counter
FLOAT_ID_START = 2800000

def get_current_count():
    """Get current record count from Supabase"""
    headers = {"apikey": SUPABASE_KEY, "Prefer": "count=exact"}
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/argo_data?select=count", headers=headers)
        if response.status_code in [200, 206]:
            return int(response.headers.get('content-range', '*/0').split('/')[-1])
    except:
        pass
    return 0

def generate_float_trajectory(float_id, region_config, start_date, num_profiles):
    """Generate realistic ARGO float trajectory with depth profiles"""
    records = []
    lat_min, lat_max = region_config["lat"]
    lon_min, lon_max = region_config["lon"]
    base_temp = region_config["base_temp"]
    
    # Random start position within region
    lat = random.uniform(lat_min, lat_max)
    lon = random.uniform(lon_min, lon_max)
    
    # Standard ARGO pressure levels (dbar)
    pressure_levels = [5, 10, 20, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000]
    
    current_time = start_date
    
    for _ in range(num_profiles):
        # Float drift (realistic ocean current movement)
        lat += random.uniform(-0.25, 0.25)
        lon += random.uniform(-0.25, 0.25)
        
        # Keep within bounds
        lat = max(lat_min + 0.5, min(lat_max - 0.5, lat))
        lon = max(lon_min + 0.5, min(lon_max - 0.5, lon))
        
        # ARGO floats surface every 5-10 days
        current_time += timedelta(days=random.randint(5, 10))
        
        # Seasonal temperature variation
        month = current_time.month
        seasonal_offset = 3 * math.sin((month - 3) * math.pi / 6)  # Peak in summer
        
        # Generate vertical profile
        for pressure in pressure_levels:
            # Temperature profile with depth
            if pressure < 50:
                temp = base_temp + seasonal_offset + random.uniform(-1, 1)
            elif pressure < 300:
                temp = base_temp - (pressure / 40) + seasonal_offset * 0.5 + random.uniform(-0.5, 0.5)
            else:
                temp = max(1.5, 8 - (pressure / 300) + random.uniform(-0.3, 0.3))
            
            # Salinity profile
            if pressure < 100:
                salinity = 34.5 + random.uniform(-0.4, 0.4)
            elif pressure < 500:
                salinity = 34.7 + random.uniform(-0.2, 0.2)
            else:
                salinity = 34.9 + random.uniform(-0.1, 0.1)
            
            # Dissolved oxygen (decreases with depth, minimum layer around 500m)
            if pressure < 100:
                oxygen = 220 + random.uniform(-15, 15)
            elif pressure < 600:
                oxygen = max(40, 180 - pressure * 0.25 + random.uniform(-10, 10))
            else:
                oxygen = max(60, 80 + (pressure - 600) * 0.05 + random.uniform(-10, 10))
            
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
    """Upload a batch of records to Supabase"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/argo_data",
            headers=headers,
            json=records,
            timeout=30
        )
        return response.status_code in [200, 201]
    except:
        return False

import math

def main():
    print("=" * 70)
    print("ARGO Float Historical Data Generator (2020-2026)")
    print("=" * 70)
    
    initial_count = get_current_count()
    print(f"\nCurrent records: {initial_count:,}")
    print(f"Target: Add ~1,200,000 more records")
    print(f"Date range: January 2020 - January 2026 (6 years)")
    
    # Time periods (generate data for each year)
    years = [
        (datetime(2020, 1, 1), datetime(2020, 12, 31)),
        (datetime(2021, 1, 1), datetime(2021, 12, 31)),
        (datetime(2022, 1, 1), datetime(2022, 12, 31)),
        (datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2024, 1, 1), datetime(2024, 12, 31)),
        (datetime(2025, 1, 1), datetime(2026, 1, 15)),
    ]
    
    all_records = []
    float_id = FLOAT_ID_START
    
    print(f"\nGenerating floats for {len(GLOBAL_REGIONS)} ocean regions across 6 years...")
    
    for year_start, year_end in years:
        year_label = year_start.strftime("%Y")
        year_records = []
        
        for region_name, config in GLOBAL_REGIONS.items():
            # 3-5 floats per region per year
            num_floats = random.randint(3, 5)
            
            for _ in range(num_floats):
                # Start somewhere within the year
                start_offset = random.randint(0, 180)
                start_date = year_start + timedelta(days=start_offset)
                
                # Each float does 20-35 profiles per year
                num_profiles = random.randint(20, 35)
                
                float_records = generate_float_trajectory(
                    float_id=float_id,
                    region_config=config,
                    start_date=start_date,
                    num_profiles=num_profiles
                )
                year_records.extend(float_records)
                float_id += 1
        
        all_records.extend(year_records)
        print(f"  {year_label}: {len(year_records):,} records generated")
    
    print(f"\n{'=' * 70}")
    print(f"Total records generated: {len(all_records):,}")
    print(f"Total floats created: {float_id - FLOAT_ID_START:,}")
    print(f"{'=' * 70}")
    
    # Upload in batches
    batch_size = 1000
    batches = [all_records[i:i+batch_size] for i in range(0, len(all_records), batch_size)]
    
    print(f"\nUploading {len(batches)} batches to Supabase...")
    
    success_count = 0
    failed_batches = []
    
    for i, batch in enumerate(batches, 1):
        if upload_batch(batch):
            success_count += len(batch)
            if i % 50 == 0 or i == len(batches):
                print(f"  Progress: {i}/{len(batches)} batches ({success_count:,} records uploaded)")
        else:
            failed_batches.append(i)
            print(f"  Batch {i} FAILED")
        
        # Small delay to avoid rate limiting
        if i % 100 == 0:
            time.sleep(1)
    
    # Get final count
    time.sleep(2)
    final_count = get_current_count()
    
    print(f"\n{'=' * 70}")
    print(f"UPLOAD COMPLETE!")
    print(f"  Before: {initial_count:,} records")
    print(f"  Added:  {success_count:,} records")
    print(f"  After:  {final_count:,} records")
    if failed_batches:
        print(f"  Failed batches: {len(failed_batches)}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
