#!/usr/bin/env python3
"""
Test script to verify logging is working correctly
"""

from logging_config import setup_logging
from ai_team.utils.security_validator import SecurityValidator
import subprocess

# Test logging setup
logger = setup_logging("test_logging")


def test_logging():
    """Test all logging levels and features"""

    print("\n=== Testing Logging System ===\n")

    # Test different log levels
    logger.debug("This is a DEBUG message - detailed diagnostic info")
    logger.info("This is an INFO message - general informational message")
    logger.warning("This is a WARNING message - something unexpected happened")
    logger.error("This is an ERROR message - a serious problem occurred")

    # Test security validation with logging
    print("\n--- Testing Security Validation ---")

    # Valid session name
    valid, error = SecurityValidator.validate_session_name("test-session")
    print(f"Valid session 'test-session': {valid}")

    # Invalid session name
    valid, error = SecurityValidator.validate_session_name("rm -rf /")
    print(f"Invalid session 'rm -rf /': {valid}, Error: {error}")

    # Test command sanitization
    try:
        safe_cmd = SecurityValidator.sanitize_command("echo 'Hello World'")
        print(f"Sanitized command: {safe_cmd}")
    except ValueError as e:
        print(f"Command sanitization failed: {e}")

    # Test subprocess logging
    print("\n--- Testing Subprocess Logging ---")
    from logging_config import log_subprocess_call

    try:
        cmd = ["echo", "Test subprocess logging"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        log_subprocess_call(logger, cmd, result)
        print("Subprocess executed successfully")
    except Exception as e:
        log_subprocess_call(logger, cmd, error=e)
        print(f"Subprocess failed: {e}")

    print("\n=== Check ./logs/ directory for log files ===")
    print("- test_logging.log (all messages)")
    print("- test_logging_errors.log (errors only)")


if __name__ == "__main__":
    test_logging()
