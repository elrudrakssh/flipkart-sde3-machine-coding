 # Configure logging
import logging

__all__ = ["base_logger"]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ'
)
base_logger = logging.getLogger(__name__)
