import sys
from pathlib import Path
from loguru import logger

def setup_logger():
    """Configure loguru logger: stdout + rotating file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.remove()  # remove default handler

    # stdout — clean format
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        level="INFO",
        colorize=True,
    )

    # file — full format, daily rotation, keep 7 days
    logger.add(
        "logs/pipeline_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} | {message}",
        level="DEBUG",
        rotation="00:00",
        retention="7 days",
        compression="zip",
    )

    return logger

# Module-level logger instance
log = setup_logger()
