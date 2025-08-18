"""
Tmux Session Manager Implementation
Extracted from create_ai_team.py lines 187-278
Implements ITmuxSessionManager protocol
"""

import subprocess
import logging
from interfaces import ITmuxSessionManager
from security_validator import SecurityValidator
from logging_config import setup_logging, log_subprocess_call

logger = setup_logging(__name__)


class TmuxSessionManager:
    """Manages tmux sessions following ITmuxSessionManager protocol"""

    def __init__(self, session_name: str = "ai-team", working_dir: str = None):
        """Initialize tmux session manager"""
        import os

        self.session_name = session_name
        self.working_dir = working_dir or os.getcwd()
        self.validator = SecurityValidator()

    def session_exists(self, session_name: str) -> bool:
        """Check if a tmux session already exists"""
        # Validate session name first
        valid, error = SecurityValidator.validate_session_name(session_name)
        if not valid:
            logger.error(f"Invalid session name: {error}")
            raise ValueError(f"Invalid session name: {error}")

        logger.debug(f"Checking if session '{session_name}' exists")
        try:
            cmd = ["tmux", "has-session", "-t", session_name]
            result = subprocess.run(cmd, check=True, capture_output=True)
            log_subprocess_call(logger, cmd, result)
            logger.debug(f"Session '{session_name}' exists")
            return True
        except subprocess.CalledProcessError as e:
            # This is expected behavior when session doesn't exist - log as debug, not error
            logger.debug(f"Session '{session_name}' does not exist (tmux has-session returned {e.returncode})")
            return False

    def create_tmux_session(self) -> bool:
        """Create the main tmux session for the AI team"""
        try:
            # Validate session name
            valid, error = SecurityValidator.validate_session_name(self.session_name)
            if not valid:
                logger.error(f"Invalid session name: {error}")
                return False

            if self.session_exists(self.session_name):
                logger.warning(f"Session '{self.session_name}' already exists. Killing it first...")
                cmd = ["tmux", "kill-session", "-t", self.session_name]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

            # Create new session with orchestrator
            cmd = ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "Orchestrator", "-c", self.working_dir]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            log_subprocess_call(logger, cmd, result)

            logger.info(f"Created session '{self.session_name}' with orchestrator window")
            logger.info(f"Created session '{self.session_name}' with orchestrator window")
            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to create tmux session: {e}")
            logger.error(f"Error creating tmux session: {e}")
            return False

    def create_agent_panes(self) -> bool:
        """Create panes for each AI agent in a split layout"""
        try:
            # Split the main window horizontally to create top and bottom sections
            # Top: Orchestrator, Bottom: Three agents side by side
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0", "-v", "-p", "60", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created horizontal split (Orchestrator top, agents bottom)")

            # Split the bottom pane vertically to create first two agent panes
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0.1", "-h", "-p", "66", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created first vertical split for agent panes")

            # Split again to create third agent pane
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0.2", "-h", "-p", "50", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created second vertical split for third agent pane")

            # Set pane titles
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.0", "-T", "Orchestrator"], check=True)

            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.1", "-T", "Alex-Purist"], check=True)

            subprocess.run(
                ["tmux", "select-pane", "-t", f"{self.session_name}:0.2", "-T", "Morgan-Pragmatist"], check=True
            )

            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.3", "-T", "Sam-Janitor"], check=True)

            logger.info("Set pane titles")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating agent panes: {e}")
            return False
