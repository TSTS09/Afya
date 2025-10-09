#!/usr/bin/env python3
"""
Logging Utilities for Healthcare Transmission System
===================================================

Centralized logging configuration with structured logging
and healthcare data privacy considerations.
"""

import logging
import logging.handlers
import sys
from typing import Optional
from pathlib import Path


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Configure handler only if not already configured
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger


def setup_file_logging(
    log_file_path: str,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    level: str = "INFO"
) -> logging.Logger:
    """Setup file-based logging with rotation"""
    logger = logging.getLogger("healthcare_transmission")
    
    # Create log directory if it doesn't exist
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.setLevel(getattr(logging, level.upper()))
    
    return logger


def sanitize_log_message(message: str) -> str:
    """Sanitize log messages to remove sensitive healthcare data"""
    # This is a basic implementation - in production, you'd want more sophisticated
    # PII detection and masking
    import re
    
    # Mask potential phone numbers
    message = re.sub(r'\+?\d{10,15}', '***PHONE***', message)
    
    # Mask potential national IDs (adjust pattern for your region)
    message = re.sub(r'\b\d{8,13}\b', '***ID***', message)
    
    # Mask potential email addresses
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***', message)
    
    return message


class HealthcareLogger:
    """Healthcare-specific logger with PII protection"""
    
    def __init__(self, name: str, sanitize_logs: bool = True):
        self.logger = get_logger(name)
        self.sanitize_logs = sanitize_logs
    
    def _sanitize_if_needed(self, message: str) -> str:
        """Sanitize message if protection is enabled"""
        if self.sanitize_logs:
            return sanitize_log_message(message)
        return message
    
    def info(self, message: str):
        """Log info message with optional sanitization"""
        self.logger.info(self._sanitize_if_needed(message))
    
    def error(self, message: str):
        """Log error message with optional sanitization"""
        self.logger.error(self._sanitize_if_needed(message))
    
    def warning(self, message: str):
        """Log warning message with optional sanitization"""
        self.logger.warning(self._sanitize_if_needed(message))
    
    def debug(self, message: str):
        """Log debug message with optional sanitization"""
        self.logger.debug(self._sanitize_if_needed(message))