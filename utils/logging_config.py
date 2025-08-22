"""
Logging configuration utility for the super-writer project
Configures logging to use print() as the output method
"""

import logging
import sys
from typing import Optional


class PrintHandler(logging.Handler):
    """Custom handler that uses print() instead of standard stream output"""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with print() output
    
    Args:
        name: Logger name (None for root logger)
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
    
    Returns:
        Configured logger instance
    """
    if format_string is None:
        # Simple format that mimics typical print statements
        format_string = '%(levelname)s: %(message)s'
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create print handler
    handler = PrintHandler()
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate outputs
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a pre-configured logger
    
    Args:
        name: Logger name (typically __name__ from the calling module)
    
    Returns:
        Logger instance
    """
    # If logger already exists with handlers, return it
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    # Otherwise, set it up with default configuration
    return setup_logger(name)


# Configure root logger with basic settings
def configure_root_logger(level: int = logging.INFO):
    """Configure the root logger for the entire application"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add print handler
    handler = PrintHandler()
    handler.setLevel(level)
    
    # Use a simple format for root logger
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    root_logger.propagate = False


# Initialize root logger on import
configure_root_logger()