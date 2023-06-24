from os import getenv
from dotenv import load_dotenv
import logging
from pathlib import Path

load_dotenv()

# Get backup dir
backup_dir: Path | None = Path(getenv('BACKUP_DIR', None)) if getenv('BACKUP_DIR', None) else None

# Create the backup dir if it doesn't exist
if backup_dir and not backup_dir.exists():
    backup_dir.mkdir(exist_ok=True)

# Create the logs dir if it doesn't exist
logs_dir: Path = Path(getenv('LOGS_DIR', None)) if getenv('LOGS_DIR', None) else Path('/data/logs')  # Change to None after setting up Logging region
if not logs_dir.exists():
    logs_dir.mkdir(exist_ok=True)

# region Logging
# Create a logger instance
log = logging.getLogger('main.py')

# AIOGram logging
# logging.basicConfig(level=logging.DEBUG)

# Create log formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create console logging handler and set its level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

# Create file logging handler and set its level
fh = logging.FileHandler(r'/data/logs/misis-admission-backend.log')
fh.setFormatter(formatter)
log.addHandler(fh)

# region Set logging level
logging_level_lower = getenv('LOGGING_LEVEL').lower()
if logging_level_lower == 'debug':
    log.setLevel(logging.DEBUG)
    log.critical("Log level set to debug")
elif logging_level_lower == 'info':
    log.setLevel(logging.INFO)
    log.critical("Log level set to info")
elif logging_level_lower == 'warning':
    log.setLevel(logging.WARNING)
    log.critical("Log level set to warning")
elif logging_level_lower == 'error':
    log.setLevel(logging.ERROR)
    log.critical("Log level set to error")
elif logging_level_lower == 'critical':
    log.setLevel(logging.CRITICAL)
    log.critical("Log level set to critical")
# endregion
# endregion
