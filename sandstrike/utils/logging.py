"""
Logging utilities for Avenlis.

This module provides logging configuration and utilities for consistent
logging across the Avenlis library and CLI.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sandstrike.config import AvenlisConfig

from rich.console import Console
from rich.logging import RichHandler

# Global console instance
console = Console()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    config: Optional["AvenlisConfig"] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        config: Optional configuration instance
        
    Returns:
        Configured logger instance
    """
    if config is None:
        # Lazy import to avoid circular dependency
        from sandstrike.config import AvenlisConfig
        config = AvenlisConfig()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("avenlis")
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with rich formatting
    # Use simple debug check to avoid dependency issues
    show_path = hasattr(config, 'is_debug_enabled') and config.is_debug_enabled() if config else False
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=show_path,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    console_format = "%(message)s"
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for file
        
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str = "avenlis") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
