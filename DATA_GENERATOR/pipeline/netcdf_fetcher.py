"""Utility functions to download ARGO observations from Argovis API."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable

import pandas as pd
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DATA_GENERATOR.config import (
    LATITUDE_RANGE,
    LONGITUDE_RANGE,
    REQUEST_TIMEOUT,
)

# Argovis API - Official REST API for ARGO data
# Documentation: https://argovis-api.colorado.edu/docs/
ARGOVIS_BASE_URL = "https://argovis-api.colorado.edu"


def fetch_argo_data(
    start: datetime,
    end: datetime,
    progress_callback: Optional[Callable[[str], None]] = None
) -> pd.DataFrame:
    """Download ARGO float data from Argovis API for the given time range.
    
    Parameters
    ----------
    start : datetime
        Inclusive start timestamp (UTC).
    end : datetime
        Inclusive end timestamp (UTC).
    progress_callback : callable, optional
        Function to call with status updates.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: float_id, timestamp, latitude, longitude, 
        pressure, temperature, salinity, dissolved_oxygen, chlorophyll
    """
    def log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)
        print(msg)
    
    # Convert to UTC ISO format
    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)
    
    lat_min, lat_max = LATITUDE_RANGE
    lon_min, lon_max = LONGITUDE_RANGE
    
    # Build bounding box: [[lon_min, lat_min], [lon_max, lat_max]]
    box = f"[[{lon_min},{lat_min}],[{lon_max},{lat_max}]]"
    
    url = f"{ARGOVIS_BASE_URL}/argo"
    params = {
        "startDate": start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDate": end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "box": box,
        "data": "pressure,temperature,salinity,doxy,chla"
    }
    
    log(f"🌐 Fetching from Argovis API...")
    log(f"📅 Date range: {start_utc.date()} to {end_utc.date()}")
    log(f"📍 Region: {lat_min}°-{lat_max}° lat, {lon_min}°-{lon_max}° lon")
    
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        profiles = response.json()
        
        if isinstance(profiles, dict) and "message" in profiles:
            raise RuntimeError(f"API Error: {profiles['message']}")
        
        log(f"✅ Received {len(profiles)} profiles from Argovis")
        
        if not profiles:
            return pd.DataFrame()
        
        # Convert profiles to flat records
        records = []
        for profile in profiles:
            float_id = profile.get("_id", "").split("_")[0]
            timestamp = profile.get("timestamp")
            
            geo = profile.get("geolocation", {})
            coords = geo.get("coordinates", [None, None])
            longitude = coords[0]
            latitude = coords[1]
            
            # Get data arrays
            data = profile.get("data", [])
            data_info = profile.get("data_info", [[]])
            
            # Map data arrays by name
            var_names = data_info[0] if data_info else []
            data_map = {}
            for i, name in enumerate(var_names):
                if i < len(data):
                    data_map[name] = data[i]
            
            pressure_arr = data_map.get("pressure", [])
            temp_arr = data_map.get("temperature", [])
            sal_arr = data_map.get("salinity", [])
            doxy_arr = data_map.get("doxy", [])
            chla_arr = data_map.get("chla", [])
            
            # Create a record for each depth level
            num_levels = len(pressure_arr) if pressure_arr else 0
            
            for i in range(num_levels):
                pressure = pressure_arr[i] if i < len(pressure_arr) else None
                temperature = temp_arr[i] if i < len(temp_arr) else None
                salinity = sal_arr[i] if i < len(sal_arr) else None
                dissolved_oxygen = doxy_arr[i] if i < len(doxy_arr) else None
                chlorophyll = chla_arr[i] if i < len(chla_arr) else None
                
                # Skip if no valid measurements
                if temperature is None and salinity is None:
                    continue
                
                records.append({
                    "float_id": int(float_id) if float_id.isdigit() else float_id,
                    "timestamp": timestamp,
                    "latitude": latitude,
                    "longitude": longitude,
                    "pressure": pressure,
                    "temperature": temperature,
                    "salinity": salinity,
                    "dissolved_oxygen": dissolved_oxygen,
                    "chlorophyll": chlorophyll,
                })
        
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            
            # Convert numeric columns
            numeric_cols = ["latitude", "longitude", "pressure", "temperature", 
                          "salinity", "dissolved_oxygen", "chlorophyll"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Remove duplicates
            df = df.drop_duplicates(
                subset=["float_id", "timestamp", "pressure"], 
                keep="last"
            )
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        log(f"📊 Processed {len(df)} measurement records")
        return df
        
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Argovis API timed out after {REQUEST_TIMEOUT}s")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Argovis API request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Error processing Argovis data: {e}")


# Legacy function for compatibility
def fetch_netcdf_dataset(start: datetime, end: datetime, progress_callback=None):
    """Legacy wrapper - now uses Argovis API instead of NetCDF.
    
    Returns a simple object with the dataframe accessible for transformation.
    """
    df = fetch_argo_data(start, end, progress_callback)
    
    # Create a simple wrapper object that mimics xarray.Dataset behavior
    class DataWrapper:
        def __init__(self, dataframe: pd.DataFrame):
            self._df = dataframe
            self.attrs = {}
        
        def to_dataframe(self):
            return self._df.copy()
        
        def close(self):
            pass
    
    return DataWrapper(df)
