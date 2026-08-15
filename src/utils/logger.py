import logging
import os
import sys
from pathlib import Path

def setup_logger(
    name: str = "attrition_system",
    log_file: str = "logs/app.log",
    level: str = "INFO"
) -> logging.Logger:
    """
    Configures and returns a centralized, thread-safe logger instance.
    Logs output simultaneously to stdout (console) and a rotated file on disk.
    
    Args:
        name (str): Logger channel name.
        log_file (str): Relative or absolute path to target log file.
        level (str): Logging severity level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        
    Returns:
        logging.Logger: Configured Python standard logger instance.
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate log handlers if function is called multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Detailed formatter for production auditing
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    logger.addHandler(console_handler)

    # 2. File Handler (UTF-8 encoded log file)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    logger.addHandler(file_handler)

    return logger

# Global default logger instance for convenient import across modules
logger = setup_logger()
