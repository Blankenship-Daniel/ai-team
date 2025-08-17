#!/usr/bin/env python3
"""
Tests for tmux operations and agent interactions
Priority: Test tmux operations and agent communication
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path

from tmux_utils import TmuxOrchestrator
from context_registry import ContextRegistry


class TestTmuxOperations:
    """Test actual tmux operations with proper mocking"""

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_send_command_to_window_success(self, mock_subprocess):
        """Test successful command sending"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        orchestrator.safety_mode = False

        # Mock successful subprocess calls
        mock_subprocess.return_value = Mock(returncode=0)

        # Test command sending
        result = orchestrator.send_command_to_window("test-session", 0, "ls -la")

        assert result is True
        assert mock_subprocess.call_count == 2  # send text + send Enter

        # Verify the calls
        calls = mock_subprocess.call_args_list

        # First call should send the literal text
        first_call = calls[0]
        assert "send-keys" in first_call[0][0]
        assert "-l" in first_call[0][0]  # Literal flag
        assert "test-session:0" in first_call[0][0]

        # Second call should send Enter
        second_call = calls[1]
        assert "send-keys" in second_call[0][0]
        assert "C-m" in second_call[0][0]  # Enter key

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_send_command_with_context(self, mock_subprocess):
        """Test context-aware command sending"""
        orchestrator = TmuxOrchestrator(enable_context_registry=True)
        orchestrator.safety_mode = False

        # Mock successful subprocess calls
        mock_subprocess.return_value = Mock(returncode=0)

        # Test command with context
        context_data = {"task": "testing", "phase": "unit_tests"}
        result = orchestrator.send_command_with_context("test-session", 0, "pytest", context_data)

        assert result is True

        # Verify checkpoint was created
        registry = orchestrator.context_registry
        state = registry.get_state("test-session", 0)
        assert state.message_count >= 1
        assert state.metadata.get("last_command") == "pytest"

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_capture_window_content(self, mock_subprocess):
        """Test window content capture"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Mock tmux capture-pane output
        mock_subprocess.return_value = Mock(stdout="Line 1\nLine 2\nLine 3\n", returncode=0)

        result = orchestrator.capture_window_content("test-session", 0, num_lines=10)

        assert result == "Line 1\nLine 2\nLine 3\n"

        # Verify correct tmux command
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "capture-pane" in call_args
        assert "-t" in call_args
        assert "test-session:0" in call_args
        assert "-S" in call_args
        assert "-10" in call_args

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_get_window_info(self, mock_subprocess):
        """Test getting detailed window information"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Mock tmux display-message output
        mock_subprocess.side_effect = [
            Mock(stdout="alex:0:2:main-vertical", returncode=0),  # window info
            Mock(stdout="Recent content\nMore content\n", returncode=0),  # content capture
        ]

        result = orchestrator.get_window_info("test-session", 1)

        assert result["name"] == "alex"
        assert result["active"] is False
        assert result["panes"] == 2
        assert result["layout"] == "main-vertical"
        assert "Recent content" in result["content"]

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_subprocess_error_handling(self, mock_subprocess):
        """Test handling of subprocess errors"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Mock subprocess failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(returncode=1, cmd=["tmux", "send-keys"])

        result = orchestrator.send_keys_to_window("test-session", 0, "test", confirm=False)

        assert result is False

    @pytest.mark.tmux
    @pytest.mark.slow
    def test_real_tmux_session_creation(self, tmux_available):
        """Test with real tmux (only if available)"""
        if not tmux_available:
            pytest.skip("tmux not available")

        # Create a test session
        test_session = "pytest-test-session"

        try:
            # Create session
            subprocess.run(["tmux", "new-session", "-d", "-s", test_session], check=True)

            # Test orchestrator can see it
            orchestrator = TmuxOrchestrator(enable_context_registry=False)
            sessions = orchestrator.get_tmux_sessions()

            session_names = [s.name for s in sessions]
            assert test_session in session_names

        finally:
            # Cleanup: kill test session
            try:
                subprocess.run(["tmux", "kill-session", "-t", test_session], check=False)
            except:
                pass


class TestAgentCommunication:
    """Test agent-to-agent communication patterns"""

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_orchestrator_to_agent_message(self, mock_subprocess):
        """Test orchestrator sending message to agent"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        orchestrator.safety_mode = False

        mock_subprocess.return_value = Mock(returncode=0)

        # Test sending task assignment
        message = "Alex, please implement authentication system. Focus on security and proper error handling."
        result = orchestrator.send_keys_to_window("ai-team", 1, message, confirm=False)

        assert result is True

        # Verify message was sent
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "send-keys" in call_args
        assert "ai-team:1" in call_args

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_agent_status_reporting(self, mock_subprocess):
        """Test agent reporting status back"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Mock agent window content (status report)
        mock_subprocess.return_value = Mock(
            stdout="""
Alex (pane 1): Authentication system 80% complete
- OAuth2 integration: DONE
- JWT token handling: DONE
- Password hashing: IN PROGRESS
- Input validation: PENDING
- Tests: PENDING

Next: Complete password hashing, then write comprehensive tests.
Git: 3 commits, all tests passing
""",
            returncode=0,
        )

        content = orchestrator.capture_window_content("ai-team", 1)

        # Verify we can parse agent status
        assert "Authentication system 80% complete" in content
        assert "OAuth2 integration: DONE" in content
        assert "PENDING" in content
        assert "Git: 3 commits" in content

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_context_restoration_flow(self, mock_subprocess):
        """Test context restoration when agent loses context"""
        orchestrator = TmuxOrchestrator(enable_context_registry=True)
        orchestrator.safety_mode = False

        mock_subprocess.return_value = Mock(returncode=0)

        # Create initial checkpoint
        context_data = {
            "current_task": "authentication system",
            "progress": "80%",
            "files_modified": ["auth.py", "tests/test_auth.py"],
            "next_steps": ["password hashing", "comprehensive tests"],
        }

        checkpoint_id = orchestrator.create_manual_checkpoint("ai-team", 1, context_data, "Before context loss")

        # Simulate context restoration
        result = orchestrator.restore_agent_context("ai-team", 1, checkpoint_id)

        assert result is True

        # Verify restoration message was sent
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        assert "send-keys" in call_args
        assert checkpoint_id[:8] in " ".join(call_args)  # Checkpoint ID in message

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_multi_agent_coordination(self, mock_subprocess):
        """Test coordination between multiple agents"""
        orchestrator = TmuxOrchestrator(enable_context_registry=True)
        orchestrator.safety_mode = False

        mock_subprocess.return_value = Mock(returncode=0)

        # Orchestrator coordinates tasks between agents
        agents = [
            ("ai-team", 1, "Alex", "Implement backend authentication"),
            ("ai-team", 2, "Morgan", "Create frontend login UI"),
            ("ai-team", 3, "Sam", "Write integration tests"),
        ]

        # Send tasks to each agent
        for session, window, agent, task in agents:
            message = f"{agent}, {task}. Coordinate with team on shared interfaces."
            result = orchestrator.send_command_with_context(
                session, window, message, {"agent": agent, "task": task, "coordination": True}
            )
            assert result is True

        # Verify all agents received tasks
        assert mock_subprocess.call_count >= 6  # 3 agents × 2 calls each (text + enter)

    @pytest.mark.unit
    def test_context_status_monitoring(self):
        """Test monitoring context status across agents"""
        orchestrator = TmuxOrchestrator(enable_context_registry=True)

        # Create checkpoints for different agents
        alex_context = {"role": "architect", "task": "backend", "progress": 80}
        morgan_context = {"role": "shipper", "task": "frontend", "progress": 60}

        orchestrator.create_manual_checkpoint("ai-team", 1, alex_context)
        orchestrator.create_manual_checkpoint("ai-team", 2, morgan_context)

        # Check status for each agent
        alex_status = orchestrator.get_context_status("ai-team", 1)
        morgan_status = orchestrator.get_context_status("ai-team", 2)

        assert alex_status["agent_id"] == "ai-team:1"
        assert alex_status["checkpoints"]["total_checkpoints"] >= 1
        assert morgan_status["agent_id"] == "ai-team:2"
        assert morgan_status["checkpoints"]["total_checkpoints"] >= 1


class TestErrorRecovery:
    """Test error recovery and resilience"""

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_tmux_command_failure_recovery(self, mock_subprocess):
        """Test recovery from tmux command failures"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        orchestrator.safety_mode = False

        # First call fails, second succeeds
        mock_subprocess.side_effect = [subprocess.CalledProcessError(1, "tmux"), Mock(returncode=0)]

        # Should handle the failure gracefully
        result = orchestrator.send_keys_to_window("test", 0, "test", confirm=False)
        assert result is False  # First attempt fails

        # Retry should work
        result = orchestrator.send_keys_to_window("test", 0, "test", confirm=False)
        assert result is True

    @pytest.mark.unit
    def test_context_registry_fallback(self):
        """Test fallback when context registry fails"""
        orchestrator = TmuxOrchestrator(enable_context_registry=True)
        orchestrator.safety_mode = False  # Disable confirmation prompts

        # Simulate registry failure
        orchestrator.context_registry = None

        with patch("subprocess.run", return_value=Mock(returncode=0)):
            # Should fall back to basic command sending
            result = orchestrator.send_command_with_context("test", 0, "ls")
            assert result is True  # Should succeed via fallback

    @pytest.mark.unit
    def test_invalid_session_handling(self):
        """Test handling of invalid session names"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Test various invalid inputs
        invalid_sessions = ["", "session with spaces", "../../../etc/passwd"]

        for session in invalid_sessions:
            result = orchestrator.capture_window_content(session, 0)
            assert "Error:" in result

            result = orchestrator.send_keys_to_window(session, 0, "test", confirm=False)
            assert result is False

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_monitoring_snapshot_creation(self, mock_subprocess):
        """Test comprehensive monitoring snapshot creation"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)

        # Mock tmux session data
        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "list-sessions" in cmd:
                return Mock(stdout="ai-team:1\n", returncode=0)
            elif "list-windows" in cmd:
                return Mock(stdout="0:orchestrator:1\n1:alex:0\n", returncode=0)
            elif "display-message" in cmd:
                return Mock(stdout="alex:0:1:main-horizontal", returncode=0)
            elif "capture-pane" in cmd:
                return Mock(stdout="Agent working on task...\n", returncode=0)
            return Mock(returncode=0)

        mock_subprocess.side_effect = mock_run

        # Create monitoring snapshot
        snapshot = orchestrator.create_monitoring_snapshot()

        assert "Tmux Monitoring Snapshot" in snapshot
        assert "ai-team" in snapshot
        assert "orchestrator" in snapshot
        assert "alex" in snapshot
        assert "Agent working on task" in snapshot


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
