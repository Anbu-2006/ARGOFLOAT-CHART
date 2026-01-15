"""Configuration settings for the data generator."""
from datetime import datetime, timezone

# Argovis API - Official REST API for ARGO data
# Documentation: https://argovis-api.colorado.edu/docs/
ARGOVIS_BASE_URL = "https://argovis-api.colorado.edu"

# Geographic and depth constraints - Indian Ocean region
LATITUDE_RANGE = (-20.0, 25.0)
LONGITUDE_RANGE = (50.0, 100.0)
PRESSURE_RANGE = (0.0, 2000.0)
REGION_LABEL = "Indian Ocean (50°E-100°E, 20°S-25°N)"

# Baseline date for initial backfill
# Set to recent date for quick data fetch
DEFAULT_START_DATE = datetime(2025, 12, 1, tzinfo=timezone.utc)

# Paths used by the generator
STATE_FILE_PATH = "update_state.json"
LOG_FILE_PATH = "data_generator.log"

# Network settings
REQUEST_TIMEOUT = 180  # seconds - Argovis can take time for large requests

# Columns we expect to pull and store in Postgres
CANONICAL_COLUMNS = [
    "float_id",
    "timestamp",
    "latitude",
    "longitude",
    "pressure",
    "temperature",
    "salinity",
    "chlorophyll",
    "dissolved_oxygen"
]
