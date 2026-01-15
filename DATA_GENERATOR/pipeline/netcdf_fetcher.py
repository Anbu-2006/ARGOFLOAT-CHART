"""Utility functions to download ARGO observations from ERDDAP as NetCDF."""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Tuple, Optional

import requests
import xarray as xr

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from DATA_GENERATOR.config import (
    ERDDAP_SERVERS,
    LATITUDE_RANGE,
    LONGITUDE_RANGE,
    PRESSURE_RANGE,
    REQUEST_TIMEOUT,
)


# Variables for Ifremer BGC dataset
VARIABLES_BGC: Tuple[str, ...] = (
    "platform_number",
    "time",
    "latitude",
    "longitude",
    "pres",
    "temp",
    "psal",
    "chla",
    "doxy",
)

# Variables for NOAA standard ARGO dataset (different column names)
VARIABLES_NOAA: Tuple[str, ...] = (
    "platform_number",
    "time",
    "latitude",
    "longitude",
    "pres",
    "temp",
    "psal",
)


def build_erddap_url(start: datetime, end: datetime, base_url: str, dataset_id: str, variables: Tuple[str, ...]) -> str:
    """Construct the ERDDAP NetCDF query URL for the configured dataset and region."""
    start_utc = start.astimezone(timezone.utc).replace(microsecond=0)
    end_utc = end.astimezone(timezone.utc).replace(microsecond=0)
    start_iso = start_utc.isoformat().replace("+00:00", "Z")
    end_iso = end_utc.isoformat().replace("+00:00", "Z")
    lat_min, lat_max = LATITUDE_RANGE
    lon_min, lon_max = LONGITUDE_RANGE
    pres_min, pres_max = PRESSURE_RANGE
    var_str = ",".join(variables)
    query = (
        f"time>={start_iso}&time<={end_iso}"
        f"&latitude>={lat_min}&latitude<={lat_max}"
        f"&longitude>={lon_min}&longitude<={lon_max}"
        f"&pres>={pres_min}&pres<={pres_max}"
    )
    return f"{base_url}{dataset_id}.nc?{var_str}&{query}"


def fetch_netcdf_dataset(start: datetime, end: datetime, progress_callback=None) -> xr.Dataset:
    """Download a NetCDF dataset from ERDDAP for the given time range.
    
    Tries multiple ERDDAP servers if the primary one fails.

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
    xr.Dataset
        The downloaded dataset ready for further processing.
    """
    last_error = None
    
    for server in ERDDAP_SERVERS:
        server_name = server["name"]
        base_url = server["url"]
        dataset_id = server["dataset"]
        
        # Choose variables based on dataset type
        if "BGC" in dataset_id:
            variables = VARIABLES_BGC
        else:
            variables = VARIABLES_NOAA
        
        if progress_callback:
            progress_callback(f"Trying {server_name}...")
        
        try:
            url = build_erddap_url(start, end, base_url, dataset_id, variables)
            print(f"Fetching from {server_name}: {url[:100]}...")
            
            response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        tmp.write(chunk)
                temp_path = tmp.name

            try:
                dataset = xr.open_dataset(temp_path)
                # Store temp path for cleanup later
                dataset.attrs["_local_temp_path"] = temp_path
                print(f"Successfully fetched data from {server_name}")
                if progress_callback:
                    progress_callback(f"Success! Data from {server_name}")
                return dataset
            except Exception as e:
                os.remove(temp_path)
                raise e
                
        except requests.exceptions.Timeout:
            last_error = f"{server_name} timed out after {REQUEST_TIMEOUT}s"
            print(f"Server {server_name} timed out, trying next...")
            continue
        except requests.exceptions.RequestException as e:
            last_error = f"{server_name}: {str(e)}"
            print(f"Server {server_name} failed: {e}, trying next...")
            continue
        except Exception as e:
            last_error = f"{server_name}: {str(e)}"
            print(f"Error with {server_name}: {e}, trying next...")
            continue
    
    # All servers failed
    raise RuntimeError(f"All ERDDAP servers failed. Last error: {last_error}")
