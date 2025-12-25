import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = "logs/system.log"):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
