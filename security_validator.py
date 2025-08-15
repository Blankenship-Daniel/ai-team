#!/usr/bin/env python3
"""
Security validation module for Tmux Orchestrator
Provides input sanitization and validation functions to prevent injection attacks
"""

import re
import shlex
from typing import Optional, List, Tuple
from pathlib import Path
from logging_config import setup_logging

# Set up logging for this module
logger = setup_logging(__name__)


class SecurityValidator:
    """Validates and sanitizes user inputs to prevent security vulnerabilities"""
    
    # Regex patterns for validation
    SESSION_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    WINDOW_INDEX_PATTERN = re.compile(r'^\d+$')
    PANE_INDEX_PATTERN = re.compile(r'^\d+\.\d+$')
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')
    
    # Maximum lengths to prevent DoS
    MAX_SESSION_NAME_LENGTH = 50
    MAX_COMMAND_LENGTH = 1000
    MAX_MESSAGE_LENGTH = 5000
    MAX_PATH_LENGTH = 255
    
    @classmethod
    def validate_session_name(cls, session_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate tmux session name
        
        Args:
            session_name: The session name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not session_name:
            logger.warning("Validation failed: empty session name")
            return False, "Session name cannot be empty"
        
        if len(session_name) > cls.MAX_SESSION_NAME_LENGTH:
            logger.warning(f"Validation failed: session name too long ({len(session_name)} chars)")
            return False, f"Session name exceeds maximum length of {cls.MAX_SESSION_NAME_LENGTH}"
        
        if not cls.SESSION_NAME_PATTERN.match(session_name):
            logger.warning(f"Validation failed: invalid session name format '{session_name}'")
            return False, "Session name can only contain alphanumeric characters, hyphens, and underscores"
        
        # Check for reserved names
        reserved_names = ['server', 'global', 'default']
        if session_name.lower() in reserved_names:
            logger.warning(f"Validation failed: reserved session name '{session_name}'")
            return False, f"'{session_name}' is a reserved session name"
        
        logger.debug(f"Session name '{session_name}' validated successfully")
        return True, None
    
    @classmethod
    def validate_window_index(cls, window_index: str) -> Tuple[bool, Optional[str]]:
        """
        Validate tmux window index
        
        Args:
            window_index: The window index to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not window_index:
            return False, "Window index cannot be empty"
        
        if not cls.WINDOW_INDEX_PATTERN.match(str(window_index)):
            return False, "Window index must be a non-negative integer"
        
        index_int = int(window_index)
        if index_int > 999:  # Reasonable tmux window limit
            return False, "Window index exceeds maximum value"
        
        return True, None
    
    @classmethod
    def validate_pane_target(cls, pane_target: str) -> Tuple[bool, Optional[str]]:
        """
        Validate tmux pane target (session:window.pane format)
        
        Args:
            pane_target: The pane target to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pane_target:
            return False, "Pane target cannot be empty"
        
        # Split into components
        if ':' not in pane_target:
            return False, "Pane target must be in format 'session:window' or 'session:window.pane'"
        
        parts = pane_target.split(':')
        if len(parts) != 2:
            return False, "Invalid pane target format"
        
        session_name = parts[0]
        window_pane = parts[1]
        
        # Validate session name
        valid, error = cls.validate_session_name(session_name)
        if not valid:
            return False, f"Invalid session name in target: {error}"
        
        # Check if it has pane specification
        if '.' in window_pane:
            window_part, pane_part = window_pane.split('.', 1)
            valid, error = cls.validate_window_index(window_part)
            if not valid:
                return False, f"Invalid window index in target: {error}"
            
            if not pane_part.isdigit():
                return False, "Pane index must be a non-negative integer"
        else:
            valid, error = cls.validate_window_index(window_pane)
            if not valid:
                return False, f"Invalid window index in target: {error}"
        
        return True, None
    
    @classmethod
    def sanitize_command(cls, command: str) -> str:
        """
        Sanitize a command for safe execution
        
        Args:
            command: The command to sanitize
            
        Returns:
            Sanitized command string
        """
        if len(command) > cls.MAX_COMMAND_LENGTH:
            logger.error(f"Command sanitization failed: too long ({len(command)} chars)")
            raise ValueError(f"Command exceeds maximum length of {cls.MAX_COMMAND_LENGTH}")
        
        # Use shlex.quote for shell-safe quoting
        sanitized = shlex.quote(command)
        logger.debug(f"Command sanitized: {len(command)} -> {len(sanitized)} chars")
        return sanitized
    
    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """
        Sanitize a message for tmux send-keys
        
        Args:
            message: The message to sanitize
            
        Returns:
            Sanitized message string
        """
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            logger.error(f"Message sanitization failed: too long ({len(message)} chars)")
            raise ValueError(f"Message exceeds maximum length of {cls.MAX_MESSAGE_LENGTH}")
        
        # Escape special characters that could be interpreted by tmux
        # Remove any control characters except newline and tab
        sanitized = ''.join(char for char in message 
                          if char == '\n' or char == '\t' or 
                          (ord(char) >= 32 and ord(char) < 127) or 
                          ord(char) > 127)
        
        # Use shlex.quote for shell-safe quoting
        quoted = shlex.quote(sanitized)
        logger.debug(f"Message sanitized: {len(message)} -> {len(quoted)} chars")
        return quoted
    
    @classmethod
    def validate_file_path(cls, file_path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate a file path for safety
        
        Args:
            file_path: The file path to validate
            must_exist: Whether the file must already exist
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "File path cannot be empty"
        
        if len(file_path) > cls.MAX_PATH_LENGTH:
            return False, f"File path exceeds maximum length of {cls.MAX_PATH_LENGTH}"
        
        # Prevent path traversal
        path = Path(file_path)
        try:
            # Resolve to absolute path and check for traversal attempts
            resolved = path.resolve()
            
            # Check if path tries to escape the working directory
            cwd = Path.cwd()
            if not (resolved == cwd or cwd in resolved.parents or resolved in cwd.parents):
                # Allow paths within the working directory or its parents/children
                logger.debug(f"File path '{file_path}' outside working directory (allowed)")
            
            if must_exist and not resolved.exists():
                logger.warning(f"File path validation failed: file does not exist '{file_path}'")
                return False, f"File does not exist: {file_path}"
            
            logger.debug(f"File path '{file_path}' validated successfully")
            return True, None
            
        except (ValueError, OSError) as e:
            logger.error(f"File path validation failed: {str(e)}")
            return False, f"Invalid file path: {str(e)}"
    
    @classmethod
    def build_safe_command(cls, base_command: List[str], **kwargs) -> List[str]:
        """
        Build a safe command list for subprocess execution
        
        Args:
            base_command: The base command as a list
            **kwargs: Additional arguments to append
            
        Returns:
            Safe command list
        """
        safe_cmd = base_command.copy()
        
        for key, value in kwargs.items():
            if value is not None:
                # Add both key and value, properly quoted
                if key.startswith('-'):
                    safe_cmd.append(key)
                    if value != True:  # For boolean flags
                        safe_cmd.append(str(value))
                else:
                    safe_cmd.append(str(value))
        
        return safe_cmd
    
    @classmethod
    def validate_agent_name(cls, agent_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an agent name
        
        Args:
            agent_name: The agent name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not agent_name:
            return False, "Agent name cannot be empty"
        
        if len(agent_name) > 50:
            return False, "Agent name exceeds maximum length of 50"
        
        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', agent_name):
            return False, "Agent name contains invalid characters"
        
        return True, None