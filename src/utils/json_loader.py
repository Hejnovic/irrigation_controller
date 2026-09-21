import json
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


def  load_json_file(file: Path):
    if not file.is_file():
        logger.warning(f"Provided path is not a file - path: {file}")
        return
    with open(file, 'r') as f:
        try:
            data = json.load(f)
            return data 
        except json.JSONDecodeError as e:
            logger.error(f"Provided file is not parsable JSON with {e.msg}, line: {e.lineno}, column: {e.colno}")
            return e