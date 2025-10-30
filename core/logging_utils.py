""" Logging utilities """

import json
import logging
from pathlib import Path
from typing import Dict, Any

def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger('podcast_factory')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file, mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    # For JSONL, we could override but simplified
    return logger