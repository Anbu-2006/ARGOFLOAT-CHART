"""Configuration settings for the data generator."""
from datetime import datetime, timezone

# ERDDAP servers to try (in order of preference)
# Ifremer is primary, NOAA PMEL as backup
ERDDAP_SERVERS = [
    {
        "url": "https://erddap.ifremer.fr/erddap/tabledap/",
        "dataset": "ArgoFloats-synthetic-BGC",
        "name": "Ifremer (France)"
    },
    {
        "url": "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/",
        "dataset": "ArgoFloats",
        "name": "NOAA CoastWatch (USA)"
    }
]

# Default server settings
ERDDAP_BASE_URL = ERDDAP_SERVERS[0]["url"]
DATASET_ID = ERDDAP_SERVERS[0]["dataset"]

# Geographic and depth constraints aligned with existing application expectations.
LATITUDE_RANGE = (-20.0, 25.0)
LONGITUDE_RANGE = (50.0, 100.0)
PRESSURE_RANGE = (0.0, 2000.0)
REGION_LABEL = "Indian Ocean (50°E-100°E, 20°S-25°N)"

# Baseline date for initial backfill.
# TESTING: Using recent date for quick test. Change back to 2020 for full data.
DEFAULT_START_DATE = datetime(2025, 12, 1, tzinfo=timezone.utc)  # Just 1.5 months of data

# Paths used by the generator.
STATE_FILE_PATH = "update_state.json"
LOG_FILE_PATH = "data_generator.log"

# Network and persistence settings.
REQUEST_TIMEOUT = 120  # seconds (reduced for faster failure detection)

# Columns we expect to pull from ERDDAP and store in Postgres.
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
