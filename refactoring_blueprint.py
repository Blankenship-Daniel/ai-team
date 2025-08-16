#!/usr/bin/env python3
"""
SecurityValidator Refactoring Blueprint
Template for SOLID principle extraction from god classes

This file demonstrates the pattern for:
1. Protocol interface adherence
2. Dependency injection integration
3. Type safety with generics
4. Clean separation of concerns
5. Comprehensive testing approach
"""

from typing import Tuple, Optional, List
from interfaces import ISecurityValidator, ValidationResult
from security_validator import SecurityValidator
from dependency_container import get_container
from logging_config import setup_logging

logger = setup_logging(__name__)


class SecurityValidatorAdapter(ISecurityValidator):
    """
    Adapter pattern implementation that wraps existing SecurityValidator

    This demonstrates how to gradually migrate from static methods to
    clean interface-based dependency injection without breaking existing code.

    REFACTORING PATTERN:
    1. Create Protocol interface (✅ done in interfaces.py)
    2. Create adapter that implements Protocol (this class)
    3. Register adapter in DI container
    4. Replace direct calls with DI resolution
    5. Test comprehensively
    6. Migrate implementation details incrementally
    """

    def __init__(self):
        """Initialize with clean state - no static dependencies"""
        logger.debug("SecurityValidatorAdapter initialized")

    def validate_session_name(self, session_name: str) -> ValidationResult:
        """
        Validate tmux session name for security

        Delegates to existing implementation while providing clean interface.
        In future iterations, we can migrate the logic here directly.
        """
        return SecurityValidator.validate_session_name(session_name)

    def validate_pane_target(self, pane_target: str) -> ValidationResult:
        """Validate tmux pane target"""
        return SecurityValidator.validate_pane_target(pane_target)

    def sanitize_message(self, message: str) -> str:
        """Sanitize message for safe transmission"""
        return SecurityValidator.sanitize_message(message)

    def validate_file_path(self, file_path: str, must_exist: bool = False) -> ValidationResult:
        """Validate file path for safety"""
        return SecurityValidator.validate_file_path(file_path, must_exist)


class EnhancedSecurityValidator(ISecurityValidator):
    """
    Enhanced security validator with additional SOLID principles

    This demonstrates the target architecture:
    - Single Responsibility: Only validation logic
    - Open/Closed: Extensible via composition
    - Liskov Substitution: Full ISecurityValidator compliance
    - Interface Segregation: Focused interface
    - Dependency Inversion: Depends on abstractions
    """

    def __init__(self, max_session_length: int = 50, max_message_length: int = 5000):
        """
        Initialize with configurable limits

        Configuration injection follows Dependency Inversion Principle
        """
        self.max_session_length = max_session_length
        self.max_message_length = max_message_length
        self._validation_rules: List[callable] = []
        logger.debug(
            f"EnhancedSecurityValidator initialized with limits: "
            f"session={max_session_length}, message={max_message_length}"
        )

    def add_validation_rule(self, rule: callable) -> None:
        """
        Add custom validation rule (Open/Closed Principle)

        Allows extension without modification of core logic
        """
        self._validation_rules.append(rule)
        logger.debug(f"Added custom validation rule: {rule.__name__}")

    def validate_session_name(self, session_name: str) -> ValidationResult:
        """Enhanced session name validation with extensibility"""
        # Core validation
        if not session_name:
            return False, "Session name cannot be empty"

        if len(session_name) > self.max_session_length:
            return False, f"Session name exceeds maximum length of {self.max_session_length}"

        # Apply custom rules
        for rule in self._validation_rules:
            try:
                valid, error = rule(session_name)
                if not valid:
                    return False, error
            except Exception as e:
                logger.error(f"Validation rule {rule.__name__} failed: {e}")
                return False, f"Validation rule error: {str(e)}"

        # Delegate to existing implementation for compatibility
        return SecurityValidator.validate_session_name(session_name)

    def validate_pane_target(self, pane_target: str) -> ValidationResult:
        """Enhanced pane target validation"""
        return SecurityValidator.validate_pane_target(pane_target)

    def sanitize_message(self, message: str) -> str:
        """Enhanced message sanitization"""
        if len(message) > self.max_message_length:
            # Truncate instead of failing for better UX
            truncated = message[: self.max_message_length]
            logger.warning(f"Message truncated from {len(message)} to {self.max_message_length} chars")
            return SecurityValidator.sanitize_message(truncated)

        return SecurityValidator.sanitize_message(message)

    def validate_file_path(self, file_path: str, must_exist: bool = False) -> ValidationResult:
        """Enhanced file path validation"""
        return SecurityValidator.validate_file_path(file_path, must_exist)


# Factory for creating security validators
class SecurityValidatorFactory:
    """
    Factory for creating security validator instances

    Demonstrates Factory pattern for complex object creation
    Following Single Responsibility and Open/Closed principles
    """

    @staticmethod
    def create_basic_validator() -> ISecurityValidator:
        """Create basic security validator"""
        return SecurityValidatorAdapter()

    @staticmethod
    def create_enhanced_validator(max_session_length: int = 50, max_message_length: int = 5000) -> ISecurityValidator:
        """Create enhanced security validator with custom limits"""
        return EnhancedSecurityValidator(max_session_length, max_message_length)

    @staticmethod
    def create_strict_validator() -> ISecurityValidator:
        """Create strict validator with tighter limits"""
        validator = EnhancedSecurityValidator(max_session_length=30, max_message_length=1000)

        # Add strict validation rules
        def no_special_chars_rule(session_name: str) -> ValidationResult:
            if any(char in session_name for char in ["@", "#", "$", "%"]):
                return False, "Session name cannot contain special characters"
            return True, None

        validator.add_validation_rule(no_special_chars_rule)
        return validator


def configure_security_validators() -> None:
    """
    Configure security validators in dependency container

    This demonstrates how to register different implementations
    for different use cases while maintaining clean interfaces
    """
    container = get_container()

    # Register basic validator as default
    container.register_singleton(ISecurityValidator, SecurityValidatorFactory.create_basic_validator)

    logger.info("Configured security validators in DI container")


def demonstrate_usage() -> None:
    """
    Demonstrate the refactored security validation usage

    This shows how client code becomes cleaner and more testable
    """
    # Old approach (tightly coupled)
    # valid, error = SecurityValidator.validate_session_name("test-session")

    # New approach (dependency injection)
    container = get_container()
    validator = container.resolve(ISecurityValidator)

    # Same interface, but now testable and configurable
    valid, error = validator.validate_session_name("test-session")
    print(f"Validation result: {valid}, error: {error}")

    # Can easily swap implementations
    enhanced_validator = SecurityValidatorFactory.create_enhanced_validator()
    valid, error = enhanced_validator.validate_session_name("test-session")
    print(f"Enhanced validation result: {valid}, error: {error}")


if __name__ == "__main__":
    # Demonstrate the refactoring pattern
    configure_security_validators()
    demonstrate_usage()
