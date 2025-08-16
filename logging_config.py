#!/usr/bin/env python3
"""
Centralized logging configuration for Tmux Orchestrator
Provides structured logging with file rotation and proper log levels
"""

import logging
import logging.handlers
import os
from pathlib import Path

from typing import Optional

def setup_logging(name: str, log_dir: Optional[str] = None, console_level: str = "INFO", file_level: str = "DEBUG") -> logging.Logger:
    """
    Set up a logger with both console and rotating file handlers
    
    Args:
        name: Logger name (usually __name__ from calling module)
        log_dir: Directory for log files (defaults to ./logs)
        console_level: Logging level for console output
        file_level: Logging level for file output
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Rotating file handler (10MB per file, keep 5 backups)
    log_file = os.path.join(log_dir, f'{name.replace(".", "_")}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Also create a separate error log file
    error_log_file = os.path.join(log_dir, f'{name.replace(".", "_")}_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    return logger

def log_subprocess_call(logger: logging.Logger, cmd: list, result=None, error=None):
    """
    Log subprocess calls in a structured way
    
    Args:
        logger: Logger instance to use
        cmd: Command list passed to subprocess
        result: Result from subprocess if successful
        error: Exception if subprocess failed
    """
    safe_cmd = ' '.join(str(c) for c in cmd)
    
    if error:
        logger.error(f"Subprocess failed: {safe_cmd}", extra={
            'command': cmd,
            'error': str(error),
            'error_type': type(error).__name__
        })
    else:
        logger.debug(f"Subprocess succeeded: {safe_cmd}", extra={
            'command': cmd,
            'returncode': getattr(result, 'returncode', None),
            'stdout_lines': len(result.stdout.splitlines()) if hasattr(result, 'stdout') and result.stdout else 0
        })