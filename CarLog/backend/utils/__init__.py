"""
Utility Module for CarLog Backend
---------------------------------
Contains helper functions and reusable utilities for the CarLog app.
Used across routes and services for logging, formatting, and validation.
"""

import datetime
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("carlog_backend.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_request(route_name: str, vin: str):
    """Log when a route is accessed with a VIN."""
    logger.info(f"Accessed route '{route_name}' with VIN: {vin}")

def format_date(timestamp=None):
    """Return a human-readable date/time string."""
    if timestamp is None:
        timestamp = datetime.datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
