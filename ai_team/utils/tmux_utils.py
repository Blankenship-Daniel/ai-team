#!/usr/bin/env python3

import subprocess
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from ai_team.utils.security_validator import SecurityValidator
from ai_team.utils.logging_config import setup_logging
from ai_team.core.context_registry import ContextRegistry

# Set up logging for this module
logger = setup_logging(__name__)


@dataclass
class TmuxWindow:
    session_name: str
    window_index: int
    window_name: str
    active: bool


@dataclass
class TmuxSession:
    name: str
    windows: List[TmuxWindow]
    attached: bool


class TmuxOrchestrator:
    def __init__(self, enable_context_registry: bool = True):
        self.safety_mode = True
        self.max_lines_capture = 1000

        # Initialize context registry for bulletproof context persistence
        self.context_registry = ContextRegistry() if enable_context_registry else None
        if self.context_registry:
            logger.info("TmuxOrchestrator initialized with context registry")

    def get_tmux_sessions(self) -> List[TmuxSession]:
        """Get all tmux sessions and their windows"""
        try:
            # Get sessions
            sessions_cmd = ["tmux", "list-sessions", "-F", "#{session_name}:#{session_attached}"]
            sessions_result = subprocess.run(sessions_cmd, capture_output=True, text=True, check=True)

            sessions = []
            for line in sessions_result.stdout.strip().split("\n"):
                if not line:
                    continue
                session_name, attached = line.split(":")

                # Get windows for this session
                windows_cmd = [
                    "tmux",
                    "list-windows",
                    "-t",
                    session_name,
                    "-F",
                    "#{window_index}:#{window_name}:#{window_active}",
                ]
                windows_result = subprocess.run(windows_cmd, capture_output=True, text=True, check=True)

                windows = []
                for window_line in windows_result.stdout.strip().split("\n"):
                    if not window_line:
                        continue
                    window_index, window_name, window_active = window_line.split(":")
                    windows.append(
                        TmuxWindow(
                            session_name=session_name,
                            window_index=int(window_index),
                            window_name=window_name,
                            active=window_active == "1",
                        )
                    )

                sessions.append(TmuxSession(name=session_name, windows=windows, attached=attached == "1"))

            return sessions
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting tmux sessions: {e}")
            return []

    def capture_window_content(self, session_name: str, window_index: int, num_lines: int = 50) -> str:
        """Safely capture the last N lines from a tmux window"""
        # Validate inputs
        valid, error = SecurityValidator.validate_session_name(session_name)
        if not valid:
            logger.error(f"Invalid session name: {error}")
            return f"Error: {error}"

        valid, error = SecurityValidator.validate_window_index(str(window_index))
        if not valid:
            logger.error(f"Invalid window index: {error}")
            return f"Error: {error}"

        if num_lines > self.max_lines_capture:
            num_lines = self.max_lines_capture

        try:
            target = f"{session_name}:{window_index}"
            cmd = ["tmux", "capture-pane", "-t", target, "-p", "-S", f"-{num_lines}"]
            logger.debug(f"Capturing window content: {target}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to capture window content: {e}")
            return f"Error capturing window content: {e}"

    def get_window_info(self, session_name: str, window_index: int) -> Dict:
        """Get detailed information about a specific window"""
        # Validate inputs
        valid, error = SecurityValidator.validate_session_name(session_name)
        if not valid:
            logger.error(f"Invalid session name: {error}")
            return {"error": f"Invalid session name: {error}"}

        valid, error = SecurityValidator.validate_window_index(str(window_index))
        if not valid:
            logger.error(f"Invalid window index: {error}")
            return {"error": f"Invalid window index: {error}"}

        logger.debug(f"Getting window info for {session_name}:{window_index}")
        try:
            target = f"{session_name}:{window_index}"
            cmd = [
                "tmux",
                "display-message",
                "-t",
                target,
                "-p",
                "#{window_name}:#{window_active}:#{window_panes}:#{window_layout}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                parts = result.stdout.strip().split(":")
                return {
                    "name": parts[0],
                    "active": parts[1] == "1",
                    "panes": int(parts[2]),
                    "layout": parts[3],
                    "content": self.capture_window_content(session_name, window_index),
                }
            else:
                return {"error": "Empty response from tmux"}
        except subprocess.CalledProcessError as e:
            return {"error": f"Could not get window info: {e}"}

    def send_keys_to_window(self, session_name: str, window_index: int, keys: str, confirm: bool = True) -> bool:
        """Safely send keys to a tmux window with validation"""
        # Validate inputs
        valid, error = SecurityValidator.validate_session_name(session_name)
        if not valid:
            logger.error(f"Invalid session name: {error}")
            return False

        valid, error = SecurityValidator.validate_window_index(str(window_index))
        if not valid:
            logger.error(f"Invalid window index: {error}")
            return False

        # Validate keys to prevent injection
        try:
            SecurityValidator.sanitize_message(keys)
        except ValueError as e:
            logger.error(f"Invalid keys: {e}")
            return False

        if self.safety_mode and confirm:
            print(f"SAFETY CHECK: About to send keys to {session_name}:{window_index}")
            response = input("Confirm? (yes/no): ")
            if response.lower() != "yes":
                print("Operation cancelled")
                return False

        try:
            target = f"{session_name}:{window_index}"
            # Use literal keys to avoid shell interpretation
            cmd = ["tmux", "send-keys", "-t", target, "-l", keys]
            logger.info(f"Sending keys to {target}")
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sending keys: {e}")
            return False

    def send_command_to_window(self, session_name: str, window_index: int, command: str, confirm: bool = True) -> bool:
        """Send a command to a window (adds Enter automatically)"""
        # Validate and sanitize command
        try:
            sanitized_command = SecurityValidator.sanitize_command(command)
        except ValueError as e:
            logger.error(f"Invalid command: {e}")
            return False

        # First send the command text - use sanitized version
        if not self.send_keys_to_window(session_name, window_index, sanitized_command, confirm):
            return False

        # Then send the actual Enter key (C-m)
        try:
            target = f"{session_name}:{window_index}"
            cmd = ["tmux", "send-keys", "-t", target, "C-m"]
            subprocess.run(cmd, check=True)
            logger.debug(f"Command sent successfully to {target}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sending Enter key: {e}")
            return False

    def get_all_windows_status(self) -> Dict[str, Any]:
        """Get status of all windows across all sessions"""
        sessions = self.get_tmux_sessions()
        status: Dict[str, Any] = {"timestamp": datetime.now().isoformat(), "sessions": []}

        for session in sessions:
            session_data: Dict[str, Any] = {"name": session.name, "attached": session.attached, "windows": []}

            for window in session.windows:
                window_info = self.get_window_info(session.name, window.window_index)
                window_data = {
                    "index": window.window_index,
                    "name": window.window_name,
                    "active": window.active,
                    "info": window_info,
                }
                session_data["windows"].append(window_data)

            status["sessions"].append(session_data)

        return status

    def find_window_by_name(self, window_name: str) -> List[Tuple[str, int]]:
        """Find windows by name across all sessions"""
        sessions = self.get_tmux_sessions()
        matches = []

        for session in sessions:
            for window in session.windows:
                if window_name.lower() in window.window_name.lower():
                    matches.append((session.name, window.window_index))

        return matches

    def create_monitoring_snapshot(self) -> str:
        """Create a comprehensive snapshot for Claude analysis"""
        status = self.get_all_windows_status()

        # Format for Claude consumption
        snapshot = f"Tmux Monitoring Snapshot - {status['timestamp']}\n"
        snapshot += "=" * 50 + "\n\n"

        for session in status["sessions"]:
            snapshot += f"Session: {session['name']} ({'ATTACHED' if session['attached'] else 'DETACHED'})\n"
            snapshot += "-" * 30 + "\n"

            for window in session["windows"]:
                snapshot += f"  Window {window['index']}: {window['name']}"
                if window["active"]:
                    snapshot += " (ACTIVE)"
                snapshot += "\n"

                if "content" in window["info"]:
                    # Get last 10 lines for overview
                    content_lines = window["info"]["content"].split("\n")
                    recent_lines = content_lines[-10:] if len(content_lines) > 10 else content_lines
                    snapshot += "    Recent output:\n"
                    for line in recent_lines:
                        if line.strip():
                            snapshot += f"    | {line}\n"
                snapshot += "\n"

        return snapshot

    def send_command_with_context(
        self,
        session_name: str,
        window_index: int,
        command: str,
        context_data: Optional[Dict] = None,
        auto_checkpoint: bool = True,
    ) -> bool:
        """
        Send command with automatic context management.

        Args:
            session_name: Tmux session name
            window_index: Window index
            command: Command to send
            context_data: Additional context to include in checkpoint
            auto_checkpoint: Whether to create checkpoint automatically

        Returns:
            True if successful, False otherwise
        """
        if not self.context_registry:
            logger.warning("Context registry not available, falling back to basic send")
            return self.send_command_to_window(session_name, window_index, command)

        try:
            # Get current working directory and other context
            current_context = {
                "command_sent": command,
                "timestamp": datetime.now().isoformat(),
                "working_directory": str(Path.cwd()),
                "session_info": {"session": session_name, "window": window_index},
            }

            # Merge additional context
            if context_data:
                current_context.update(context_data)

            # Update state
            self.context_registry.update_state(
                session_name, window_index, working_directory=str(Path.cwd()), last_command=command
            )

            # Create checkpoint if threshold reached or explicitly requested
            if auto_checkpoint and self.context_registry.should_create_checkpoint(session_name, window_index):
                checkpoint_id = self.context_registry.create_checkpoint(session_name, window_index, current_context)
                logger.info(f"Created context checkpoint {checkpoint_id[:8]} for {session_name}:{window_index}")

                # Add context header to command
                context_header = f"[CTX:{checkpoint_id[:8]}] "
                enhanced_command = context_header + command
            else:
                enhanced_command = command

            # Send the command
            success = self.send_command_to_window(session_name, window_index, enhanced_command)

            if success:
                # Update message count
                state = self.context_registry.get_state(session_name, window_index)
                state.message_count += 1
                logger.debug(f"Command sent with context to {session_name}:{window_index}")

            return success

        except Exception as e:
            logger.error(f"Error sending command with context: {e}")
            # Fallback to basic send
            return self.send_command_to_window(session_name, window_index, command)

    def restore_agent_context(self, session_name: str, window_index: int, checkpoint_id: Optional[str] = None) -> bool:
        """
        Restore agent context from checkpoint.

        Args:
            session_name: Tmux session name
            window_index: Window index
            checkpoint_id: Specific checkpoint ID, or None for latest

        Returns:
            True if context restored successfully
        """
        if not self.context_registry:
            logger.error("Context registry not available")
            return False

        try:
            if checkpoint_id:
                checkpoint = self.context_registry.restore_checkpoint(checkpoint_id)
            else:
                checkpoint = self.context_registry.get_latest_checkpoint(session_name, window_index)

            if not checkpoint:
                logger.warning(f"No checkpoint found for {session_name}:{window_index}")
                return False

            # Send context restoration message
            context_message = f"""
[CONTEXT RESTORATION]
Checkpoint: {checkpoint.id[:8]}
Timestamp: {checkpoint.timestamp}
Context Hash: {checkpoint.context_hash[:16]}

Previous context restored. Continue with your tasks.
Verification: CTX:{checkpoint.id[:8]}
"""

            return self.send_keys_to_window(session_name, window_index, context_message, confirm=False)

        except Exception as e:
            logger.error(f"Error restoring context: {e}")
            return False

    def get_context_status(self, session_name: str, window_index: int) -> Dict:
        """Get context status for an agent"""
        if not self.context_registry:
            return {"error": "Context registry not available"}

        try:
            summary = self.context_registry.get_checkpoint_summary(session_name, window_index)
            state = self.context_registry.get_state(session_name, window_index)

            return {
                "agent_id": f"{session_name}:{window_index}",
                "checkpoints": summary,
                "current_state": state.to_dict(),
                "needs_checkpoint": self.context_registry.should_create_checkpoint(session_name, window_index),
            }
        except Exception as e:
            logger.error(f"Error getting context status: {e}")
            return {"error": str(e)}

    def create_manual_checkpoint(
        self, session_name: str, window_index: int, context_data: Dict, description: Optional[str] = None
    ) -> Optional[str]:
        """
        Manually create a context checkpoint.

        Args:
            session_name: Tmux session name
            window_index: Window index
            context_data: Context data to checkpoint
            description: Optional description of the checkpoint

        Returns:
            Checkpoint ID if successful, None otherwise
        """
        if not self.context_registry:
            logger.error("Context registry not available")
            return None

        try:
            # Add metadata
            enhanced_context = {
                **context_data,
                "checkpoint_type": "manual",
                "description": description or "Manual checkpoint",
                "timestamp": datetime.now().isoformat(),
            }

            checkpoint_id = self.context_registry.create_checkpoint(session_name, window_index, enhanced_context)

            logger.info(f"Manual checkpoint {checkpoint_id[:8]} created for {session_name}:{window_index}")
            return checkpoint_id

        except Exception as e:
            logger.error(f"Error creating manual checkpoint: {e}")
            return None


if __name__ == "__main__":
    orchestrator = TmuxOrchestrator()
    status = orchestrator.get_all_windows_status()
    print(json.dumps(status, indent=2))
