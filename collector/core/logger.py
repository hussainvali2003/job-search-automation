import logging
import sys
from rich.logging import RichHandler

def setup_logger(name: str = "job_radar", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a rich logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger

logger = setup_logger()
