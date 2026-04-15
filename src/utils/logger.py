"""
Logging Utility Module
======================
Provides structured logging for the entire application.

Features:
- JSON structured logging
- Multiple log levels
- Contextual information
- Performance tracking
"""

import logging
import structlog
from pathlib import Path
from typing import Any, Dict
from src.config.settings import get_config

config = get_config()


def setup_logging() -> structlog.BoundLogger:
    """
    Configure structured logging for the application.
    
    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    
    # Create log directory if it doesn't exist
    log_dir = Path(config.log_dir)
    log_dir.mkdir(exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pipeline_agent.log"),
            logging.StreamHandler()
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if config.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = "pipeline_agent") -> structlog.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        structlog.BoundLogger: Logger instance
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding contextual information to logs.
    
    Example:
        with LogContext(pipeline_id="pipe_123", step="validation"):
            logger.info("Processing data")
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize log context with key-value pairs."""
        self.context = kwargs
        self.logger = get_logger()
    
    def __enter__(self):
        """Enter context and bind values."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and clear values."""
        structlog.contextvars.clear_contextvars()
        return False


def log_function_call(func):
    """
    Decorator to log function calls with parameters and results.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with logging
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        
        logger.info(
            f"Calling {func_name}",
            function=func_name,
            args=str(args)[:200],
            kwargs=str(kwargs)[:200]
        )
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func_name} completed successfully", function=func_name)
            return result
        except Exception as e:
            logger.error(
                f"{func_name} failed",
                function=func_name,
                error=str(e),
                exc_info=True
            )
            raise
    
    return wrapper