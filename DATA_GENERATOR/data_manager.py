"""
FloatChart - Data Manager API
Provides API endpoints for web-based data management.
"""

import os
import sys
import threading
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import pandas as pd
import requests
from io import StringIO

# Create blueprint for data management routes
data_manager_bp = Blueprint('data_manager', __name__)

# ERDDAP Servers
ERDDAP_SERVERS = {
    "ifremer": "https://erddap.ifremer.fr/erddap/tabledap",
    "noaa": "https://coastwatch.pfeg.noaa.gov/erddap/tabledap",
}
DATASET_ID = "ArgoFloats"

# Predefined regions
REGIONS = {
    "india_waters": {"name": "India Waters", "bounds": (-10, 25, 50, 100)},
    "bay_of_bengal": {"name": "Bay of Bengal", "bounds": (5, 22, 80, 95)},
    "arabian_sea": {"name": "Arabian Sea", "bounds": (5, 25, 50, 75)},
    "indian_ocean": {"name": "Indian Ocean", "bounds": (-40, 25, 30, 120)},
    "mediterranean": {"name": "Mediterranean", "bounds": (30, 46, -6, 36)},
    "pacific": {"name": "Pacific Ocean", "bounds": (-60, 60, 100, 180)},
    "atlantic": {"name": "Atlantic Ocean", "bounds": (-60, 60, -80, 0)},
}

# Global state for tracking fetch progress
_fetch_state = {
    "running": False,
    "progress": 0,
    "message": "",
    "total_records": 0,
    "error": None
}


@data_manager_bp.route('/api/data-manager/regions')
def get_available_regions():
    """Get list of available regions for data fetching."""
    regions_list = [
        {"id": key, "name": val["name"], "bounds": val["bounds"]}
        for key, val in REGIONS.items()
    ]
    return jsonify({"regions": regions_list})


@data_manager_bp.route('/api/data-manager/stats')
def get_database_stats():
    """Get current database statistics."""
    from database_utils import get_database_stats as get_stats
    
    stats = get_stats()
    if not stats:
        return jsonify({"error": "Database not connected"}), 500
    
    return jsonify(stats)


@data_manager_bp.route('/api/data-manager/fetch-progress')
def get_fetch_progress():
    """Get current fetch operation progress."""
    return jsonify(_fetch_state)


@data_manager_bp.route('/api/data-manager/fetch', methods=['POST'])
def start_fetch():
    """Start a data fetch operation."""
    global _fetch_state
    
    if _fetch_state["running"]:
        return jsonify({"error": "Fetch already in progress"}), 400
    
    data = request.get_json() or {}
    region_id = data.get("region", "india_waters")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    server = data.get("server", "ifremer")
    
    # Validate region
    if region_id not in REGIONS:
        return jsonify({"error": f"Unknown region: {region_id}"}), 400
    
    # Parse dates
    try:
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.now() - timedelta(days=30)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now()
    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400
    
    # Start fetch in background thread
    thread = threading.Thread(
        target=_run_fetch,
        args=(region_id, start_dt, end_dt, server),
        daemon=True
    )
    thread.start()
    
    return jsonify({"status": "started", "message": "Fetch operation started"})


def _run_fetch(region_id: str, start_dt: datetime, end_dt: datetime, server: str):
    """Background fetch operation."""
    global _fetch_state
    
    _fetch_state = {
        "running": True,
        "progress": 0,
        "message": "Initializing...",
        "total_records": 0,
        "error": None
    }
    
    try:
        from database_utils import get_db_connection, bulk_insert
        
        region = REGIONS[region_id]
        lat_min, lat_max, lon_min, lon_max = region["bounds"]
        base_url = ERDDAP_SERVERS.get(server, ERDDAP_SERVERS["ifremer"])
        
        _fetch_state["message"] = f"Fetching from {region['name']}..."
        
        # Calculate total chunks
        total_days = (end_dt - start_dt).days
        chunk_days = 30
        total_chunks = max(1, total_days // chunk_days + 1)
        
        current_date = start_dt
        chunks_done = 0
        total_uploaded = 0
        
        while current_date < end_dt:
            chunk_end = min(current_date + timedelta(days=chunk_days), end_dt)
            chunks_done += 1
            
            _fetch_state["progress"] = int((chunks_done / total_chunks) * 100)
            _fetch_state["message"] = f"Fetching {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}..."
            
            # Fetch data from ERDDAP
            start_str = current_date.strftime("%Y-%m-%dT00:00:00Z")
            end_str = chunk_end.strftime("%Y-%m-%dT23:59:59Z")
            
            if "ifremer" in base_url:
                columns = "platform_number,time,latitude,longitude,temp,psal,pres"
            else:
                columns = "float_id,time,latitude,longitude,temp,psal,pres"
            
            url = (
                f"{base_url}/{DATASET_ID}.csv?"
                f"{columns}"
                f"&time>={start_str}&time<={end_str}"
                f"&latitude>={lat_min}&latitude<={lat_max}"
                f"&longitude>={lon_min}&longitude<={lon_max}"
                f"&orderBy(%22time%22)"
            )
            
            try:
                response = requests.get(url, timeout=120)
                if response.status_code == 200:
                    df = pd.read_csv(StringIO(response.text), skiprows=[1])
                    
                    if not df.empty:
                        # Rename columns
                        df = df.rename(columns={
                            "platform_number": "float_id",
                            "time": "timestamp",
                            "temp": "temperature",
                            "psal": "salinity",
                            "pres": "pressure"
                        })
                        
                        # Clean float_id
                        df["float_id"] = df["float_id"].astype(str).str.extract(r'(\d+)')
                        df["float_id"] = pd.to_numeric(df["float_id"], errors='coerce')
                        df = df.dropna(subset=["float_id", "latitude", "longitude", "timestamp"])
                        
                        # Prepare data tuples
                        values = []
                        for _, row in df.iterrows():
                            try:
                                val = (
                                    int(row["float_id"]),
                                    row["timestamp"],
                                    float(row["latitude"]),
                                    float(row["longitude"]),
                                    float(row["temperature"]) if pd.notna(row.get("temperature")) else None,
                                    float(row["salinity"]) if pd.notna(row.get("salinity")) else None,
                                    float(row["pressure"]) if pd.notna(row.get("pressure")) else 0.0,
                                )
                                values.append(val)
                            except:
                                pass
                        
                        if values:
                            inserted = bulk_insert(values)
                            total_uploaded += inserted
                            _fetch_state["total_records"] = total_uploaded
            except Exception as e:
                # Continue on errors
                _fetch_state["message"] = f"Error on chunk, continuing... ({str(e)[:50]})"
            
            current_date = chunk_end + timedelta(days=1)
        
        _fetch_state["progress"] = 100
        _fetch_state["message"] = f"Complete! Uploaded {total_uploaded:,} records"
        _fetch_state["running"] = False
        
    except Exception as e:
        _fetch_state["error"] = str(e)
        _fetch_state["message"] = f"Error: {str(e)}"
        _fetch_state["running"] = False


@data_manager_bp.route('/api/data-manager/clear', methods=['POST'])
def clear_database():
    """Clear all data from database."""
    from database_utils import clear_all_data
    
    data = request.get_json() or {}
    confirm = data.get("confirm", False)
    
    if not confirm:
        return jsonify({"error": "Please confirm deletion by setting confirm=true"}), 400
    
    success = clear_all_data(confirm=True)
    
    if success:
        return jsonify({"status": "success", "message": "All data cleared"})
    else:
        return jsonify({"error": "Failed to clear data"}), 500


@data_manager_bp.route('/api/data-manager/init-db', methods=['POST'])
def initialize_database():
    """Initialize the database schema."""
    from database_utils import init_database
    
    success = init_database()
    
    if success:
        return jsonify({"status": "success", "message": "Database initialized"})
    else:
        return jsonify({"error": "Failed to initialize database"}), 500
