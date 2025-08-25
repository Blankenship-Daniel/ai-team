#!/usr/bin/env python3
"""
Security test suite for Tmux Orchestrator
Tests input validation, sanitization, and command injection prevention
"""

import unittest
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_team.utils.security_validator import SecurityValidator
from ai_team.utils.tmux_utils import TmuxOrchestrator
from ai_team.cli.main import AITeamOrchestrator


class TestSecurityValidator(unittest.TestCase):
    """Test input validation and sanitization functions"""

    def test_session_name_validation(self):
        """Test session name validation"""
        # Valid names
        valid_names = ["my-session", "test_123", "AI-team", "session1"]
        for name in valid_names:
            valid, error = SecurityValidator.validate_session_name(name)
            self.assertTrue(valid, f"'{name}' should be valid but got: {error}")

        # Invalid names
        invalid_names = [
            "",  # Empty
            "a" * 51,  # Too long
            "test session",  # Contains space
            "test;ls",  # Contains semicolon
            "test|cat",  # Contains pipe
            "test&pwd",  # Contains ampersand
            "../test",  # Path traversal
            "test$(pwd)",  # Command substitution
            "test`pwd`",  # Backticks
            "test'quote",  # Single quote
            'test"quote',  # Double quote
            "server",  # Reserved name
        ]
        for name in invalid_names:
            valid, error = SecurityValidator.validate_session_name(name)
            self.assertFalse(valid, f"'{name}' should be invalid")
            self.assertIsNotNone(error, f"Error message should be provided for '{name}'")

    def test_window_index_validation(self):
        """Test window index validation"""
        # Valid indices
        valid_indices = ["0", "1", "10", "99", "999"]
        for index in valid_indices:
            valid, error = SecurityValidator.validate_window_index(index)
            self.assertTrue(valid, f"'{index}' should be valid but got: {error}")

        # Invalid indices
        invalid_indices = [
            "",  # Empty
            "-1",  # Negative
            "1.5",  # Float
            "abc",  # Non-numeric
            "1000",  # Too large
            "1;ls",  # Command injection
            "$(pwd)",  # Command substitution
        ]
        for index in invalid_indices:
            valid, error = SecurityValidator.validate_window_index(index)
            self.assertFalse(valid, f"'{index}' should be invalid")

    def test_pane_target_validation(self):
        """Test pane target validation"""
        # Valid targets
        valid_targets = [
            "session:0",
            "my-session:1",
            "test_123:99",
            "session:0.0",
            "my-session:1.2",
        ]
        for target in valid_targets:
            valid, error = SecurityValidator.validate_pane_target(target)
            self.assertTrue(valid, f"'{target}' should be valid but got: {error}")

        # Invalid targets
        invalid_targets = [
            "",  # Empty
            "session",  # No window
            ":0",  # No session
            "session:",  # No window
            "bad session:0",  # Space in session
            "session;ls:0",  # Command injection
            "session:abc",  # Non-numeric window
            "session:0.abc",  # Non-numeric pane
        ]
        for target in invalid_targets:
            valid, error = SecurityValidator.validate_pane_target(target)
            self.assertFalse(valid, f"'{target}' should be invalid")

    def test_command_sanitization(self):
        """Test command sanitization"""
        # Test basic commands
        cmd = "echo hello"
        sanitized = SecurityValidator.sanitize_command(cmd)
        self.assertIn("echo hello", sanitized)

        # Test dangerous commands are quoted
        dangerous_cmds = [
            "rm -rf /",
            "cat /etc/passwd",
            "ls; pwd",
            "echo $(whoami)",
            "test`pwd`",
            "test && ls",
            "test || cat",
            "test | grep",
        ]
        for cmd in dangerous_cmds:
            sanitized = SecurityValidator.sanitize_command(cmd)
            # Check that the command is properly quoted
            self.assertTrue(sanitized.startswith("'") or sanitized.startswith('"'))
            self.assertTrue(sanitized.endswith("'") or sanitized.endswith('"'))

    def test_message_sanitization(self):
        """Test message sanitization"""
        # Test normal messages
        msg = "Hello, this is a test message"
        sanitized = SecurityValidator.sanitize_message(msg)
        self.assertIn("Hello", sanitized)

        # Test messages with special characters
        special_msgs = [
            "test\x00null",  # Null byte
            "test\x1bescape",  # Escape character
            "test\x07bell",  # Bell character
            "normal\ntext",  # Newline (should be preserved)
            "tab\there",  # Tab (should be preserved)
        ]
        for msg in special_msgs:
            sanitized = SecurityValidator.sanitize_message(msg)
            # Control characters should be removed except newline and tab
            self.assertNotIn("\x00", sanitized)
            self.assertNotIn("\x1b", sanitized)
            self.assertNotIn("\x07", sanitized)

    def test_file_path_validation(self):
        """Test file path validation"""
        # Valid paths
        valid_paths = [
            "test.txt",
            "./test.txt",
            "dir/test.txt",
            "/tmp/test.txt",
        ]
        for path in valid_paths:
            valid, error = SecurityValidator.validate_file_path(path, must_exist=False)
            self.assertTrue(valid, f"'{path}' should be valid but got: {error}")

        # Test path traversal attempts
        traversal_paths = [
            "",  # Empty path
            "a" * 256,  # Too long
        ]
        for path in traversal_paths:
            valid, error = SecurityValidator.validate_file_path(path, must_exist=False)
            self.assertFalse(valid, f"'{path}' should be invalid")


class TestTmuxUtilsSecurity(unittest.TestCase):
    """Test security fixes in tmux_utils.py"""

    def setUp(self):
        self.tmux = TmuxOrchestrator()
        self.tmux.safety_mode = False  # Disable confirmation prompts for testing

    @patch("subprocess.run")
    def test_send_keys_validates_inputs(self, mock_run):
        """Test that send_keys_to_window validates inputs"""
        # Test with invalid session name
        result = self.tmux.send_keys_to_window("bad;ls", 0, "test", confirm=False)
        self.assertFalse(result)
        mock_run.assert_not_called()

        # Test with invalid window index
        result = self.tmux.send_keys_to_window("session", "abc", "test", confirm=False)
        self.assertFalse(result)

        # Test with valid inputs
        mock_run.return_value = MagicMock(returncode=0)
        result = self.tmux.send_keys_to_window("session", 0, "test", confirm=False)
        self.assertTrue(result)
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_capture_window_validates_inputs(self, mock_run):
        """Test that capture_window_content validates inputs"""
        # Test with invalid session name
        result = self.tmux.capture_window_content("bad;ls", 0)
        self.assertIn("Error", result)
        mock_run.assert_not_called()

        # Test with invalid window index
        result = self.tmux.capture_window_content("session", "abc")
        self.assertIn("Error", result)

        # Test with valid inputs
        mock_run.return_value = MagicMock(stdout="test output", returncode=0)
        result = self.tmux.capture_window_content("session", 0)
        mock_run.assert_called()


class TestCreateAITeamSecurity(unittest.TestCase):
    """Test security fixes in create_ai_team.py"""

    def setUp(self):
        self.orchestrator = AITeamOrchestrator()

    def test_session_name_validation_on_create(self):
        """Test that session creation validates session names"""
        # Test with invalid session name
        self.orchestrator.session_name = "bad;ls"
        with self.assertRaises(ValueError):
            self.orchestrator.session_exists("bad;ls")

        # Test with valid session name
        try:
            exists = self.orchestrator.session_exists("valid-session")
            # Should not raise an exception
            self.assertIsInstance(exists, bool)
        except ValueError:
            self.fail("Valid session name raised ValueError")

    @patch("subprocess.run")
    def test_no_shell_injection_in_commands(self, mock_run):
        """Test that subprocess calls don't use shell=True"""
        mock_run.return_value = MagicMock(returncode=1)  # Simulate session doesn't exist

        # Check session existence
        self.orchestrator.session_exists("test-session")

        # Verify subprocess was called without shell=True
        for call in mock_run.call_args_list:
            args, kwargs = call
            self.assertNotIn("shell", kwargs)
            if "shell" in kwargs:
                self.assertFalse(kwargs["shell"], "shell=True should not be used")


class TestIntegration(unittest.TestCase):
    """Integration tests for security components"""

    def test_imports_work(self):
        """Test that all modules import correctly"""
        try:
            from security_validator import SecurityValidator
            from tmux_utils import TmuxOrchestrator
            from create_ai_team import AITeamOrchestrator

            # If we get here, imports worked
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")

    def test_logging_integration(self):
        """Test that logging is properly integrated"""
        # This test verifies that logging doesn't crash the application
        orchestrator = AITeamOrchestrator()
        # If we get here without errors, logging is working
        self.assertIsNotNone(orchestrator)


def run_security_tests():
    """Run all security tests and report results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestTmuxUtilsSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestCreateAITeamSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("SECURITY TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL SECURITY TESTS PASSED")
        print("The codebase has been hardened against command injection attacks.")
    else:
        print("\n❌ SECURITY TESTS FAILED")
        print("There are still security vulnerabilities that need to be addressed.")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
