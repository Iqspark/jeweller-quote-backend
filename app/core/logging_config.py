import logging
import os
from logging.handlers import RotatingFileHandler

# ── Config ────────────────────────────────────────────────────────────────────
LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR     = os.getenv("LOG_DIR", "logs")
LOG_FILE    = os.path.join(LOG_DIR, "app.log")
ERROR_FILE  = os.path.join(LOG_DIR, "error.log")

# Max 5MB per file, keep last 5 files
MAX_BYTES   = 5 * 1024 * 1024
BACKUP_COUNT = 5

# ── Format ────────────────────────────────────────────────────────────────────
LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Call once at app startup to configure all handlers."""

    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── Handlers ──────────────────────────────────────────────────────────────

    # 1. Console — all levels
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # 2. app.log — all levels, rotated
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    # 3. error.log — ERROR and above only
    error_handler = RotatingFileHandler(
        ERROR_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # ── Root logger ───────────────────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        f"Logging initialised | level={LOG_LEVEL} | file={LOG_FILE} | errors={ERROR_FILE}"
    )
