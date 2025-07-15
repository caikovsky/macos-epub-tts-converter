"""
Logging configuration and utilities for the TTS application.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create a copy of the record to avoid modifying the original
        colored_record = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            func=record.funcName
        )
        
        # Color the level name
        colored_record.levelname = f"{level_color}{record.levelname}{reset_color}"
        
        return super().format(colored_record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True
) -> logging.Logger:
    """
    Sets up the logging configuration for the TTS application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
        enable_colors: Whether to enable colored console output
        
    Returns:
        Configured logger instance
    """
    # Create main logger
    logger = logging.getLogger("tts")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if enable_colors and sys.stdout.isatty():
            console_format = "%(asctime)s | %(levelname)s | %(message)s"
            console_formatter = ColoredFormatter(
                console_format,
                datefmt="%H:%M:%S"
            )
        else:
            console_format = "%(asctime)s | %(levelname)s | %(message)s"
            console_formatter = logging.Formatter(
                console_format,
                datefmt="%H:%M:%S"
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Use rotating file handler to prevent log files from growing too large
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_format = "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        file_formatter = logging.Formatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def create_logger(name: str) -> logging.Logger:
    """
    Creates a child logger with the given name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Child logger instance
    """
    return logging.getLogger(f"tts.{name}")


class ProgressLogger:
    """
    A logger that works well with progress bars and provides structured progress updates.
    """
    
    def __init__(self, logger: logging.Logger, total: int, description: str = "Processing"):
        self.logger = logger
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = datetime.now()
        
        # Log start
        self.logger.info(f"Starting {description}: {total} items to process")
    
    def update(self, increment: int = 1, message: Optional[str] = None) -> None:
        """
        Updates the progress counter and logs progress.
        
        Args:
            increment: Amount to increment the counter
            message: Optional message to log
        """
        self.current += increment
        
        # Calculate progress percentage
        progress = (self.current / self.total) * 100
        
        # Calculate elapsed time and ETA
        elapsed = datetime.now() - self.start_time
        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
            eta_str = str(eta).split('.')[0]  # Remove microseconds
        else:
            eta_str = "Unknown"
        
        # Log progress at key milestones
        milestones = [10, 25, 50, 75, 90, 100]
        for milestone in milestones:
            if abs(progress - milestone) < (100 / self.total):  # Within one item's worth
                self.logger.info(
                    f"{self.description}: {self.current}/{self.total} ({progress:.1f}%) - "
                    f"ETA: {eta_str}"
                )
                break
        
        # Log custom message if provided
        if message:
            self.logger.debug(f"{self.description} [{self.current}/{self.total}]: {message}")
    
    def finish(self, message: Optional[str] = None) -> None:
        """
        Logs completion message.
        
        Args:
            message: Optional completion message
        """
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        
        completion_msg = f"{self.description} completed: {self.total} items in {elapsed_str}"
        if message:
            completion_msg += f" - {message}"
        
        self.logger.info(completion_msg)


def log_system_info(logger: logging.Logger) -> None:
    """
    Logs system information for debugging purposes.
    
    Args:
        logger: Logger instance to use
    """
    import platform
    
    logger.info("System Information:")
    logger.info(f"  Platform: {platform.system()} {platform.release()}")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  CPU cores: {os.cpu_count()}")
    logger.info(f"  Working directory: {os.getcwd()}")


def log_exception(logger: logging.Logger, exception: Exception, context: str = "") -> None:
    """
    Logs an exception with context information.
    
    Args:
        logger: Logger instance to use
        exception: Exception to log
        context: Additional context information
    """
    context_msg = f" in {context}" if context else ""
    logger.error(f"Exception{context_msg}: {type(exception).__name__}: {exception}")
    logger.debug("Exception details:", exc_info=True)


def setup_default_logging() -> logging.Logger:
    """
    Sets up default logging configuration for the TTS application.
    
    Returns:
        Main logger instance
    """
    # Create logs directory
    logs_dir = os.path.join(os.getcwd(), "logs")
    
    # Generate log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"tts_{timestamp}.log")
    
    # Set up logging
    logger = setup_logging(
        log_level="INFO",
        log_file=log_file,
        enable_console=True,
        enable_colors=True
    )
    
    return logger


# Global logger instance
main_logger = setup_default_logging() 