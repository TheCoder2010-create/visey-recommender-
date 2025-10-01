"""Centralized logging configuration for the Visey Recommender service."""

import logging
import sys
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    level: str = "INFO",
    json_logs: bool = True,
    service_name: str = "visey-recommender"
) -> None:
    """Configure structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to output JSON formatted logs
        service_name: Name of the service for log context
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FUNC_NAME]
        ),
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Add service context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to caller's module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)