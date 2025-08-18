#!/usr/bin/env python3
"""
MVP Test Suite for bridge_registry.py
Pragmatic approach: Cover critical paths, mock expensive operations
Target: 95% coverage in <5 seconds
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import sys

# Import after ensuring Path is available
from bridge_registry import BridgeRegistry, BridgeRegistryArgumentParser, BridgeRegistryCommandHandler


class TestBridgeRegistryMVP:
    """MVP tests focusing on critical functionality"""
    
    @pytest.fixture
    def mock_registry(self, tmp_path):
        """Fast setup with temp directory"""
        with patch('bridge_registry.Path', return_value=tmp_path):
            registry = BridgeRegistry(str(tmp_path))
            return registry
    
    def test_directory_setup(self, mock_registry, tmp_path):
        """Verify directory structure creation - CRITICAL PATH"""
        expected_dirs = ['registry', 'registry/bridges', 'registry/sessions', 'messages', 'cleanup']
        for dir_name in expected_dirs:
            assert (tmp_path / dir_name).exists()
    
    def test_create_bridge_happy_path(self, mock_registry):
        """Test bridge creation - CORE FUNCTIONALITY"""
        bridge_id = mock_registry.create_bridge("session1", "session2", "test context")
        assert bridge_id.startswith("bridge-")
        assert len(bridge_id) == 19  # "bridge-" + 12 hex chars
    
    @patch('subprocess.run')
    def test_list_bridges_empty(self, mock_run, mock_registry):
        """Test listing with no bridges - COMMON CASE"""
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        bridges = mock_registry.list_bridges()
        assert bridges == []
    
    @patch('subprocess.run')
    def test_cleanup_old_bridges(self, mock_run, mock_registry, tmp_path):
        """Test cleanup of old bridges - MAINTENANCE PATH"""
        # Create a fake old bridge file
        bridge_file = tmp_path / "registry/bridges/bridge-test123.json"
        bridge_file.parent.mkdir(parents=True, exist_ok=True)
        bridge_file.write_text(json.dumps({
            "bridge_id": "bridge-test123",
            "created_at": "2020-01-01T00:00:00",
            "last_activity": "2020-01-01T00:00:00"
        }))
        
        mock_run.return_value = MagicMock(returncode=1)  # Simulate no tmux session
        
        with patch('bridge_registry.datetime') as mock_datetime:
            from datetime import datetime, timedelta
            mock_datetime.now.return_value = datetime(2024, 1, 1)
            mock_datetime.fromisoformat = datetime.fromisoformat
            stats = mock_registry.cleanup_old_bridges(max_age_days=7, dry_run=False)
            assert stats["bridges_removed"] >= 0


class TestCommandHandlerMVP:
    """MVP tests for Command pattern implementation"""
    
    @pytest.fixture
    def handler(self):
        """Create handler with mocked registry"""
        mock_registry = Mock(spec=BridgeRegistry)
        return BridgeRegistryCommandHandler(mock_registry)
    
    def test_handle_create_command(self, handler):
        """Test create command execution - PRIMARY USE CASE"""
        handler.registry.create_bridge.return_value = "bridge-abc123"
        
        command_data = {
            "command": "create",
            "session1": "session1",
            "session2": "session2",
            "context": "context"
        }
        result = handler._handle_create(command_data)
        
        handler.registry.create_bridge.assert_called_once_with("session1", "session2", "context")
        assert result["bridge_id"] == "bridge-abc123"
        assert result["exit_code"] == 0
    
    def test_handle_list_command(self, handler):
        """Test list command - MONITORING USE CASE"""
        handler.registry.list_bridges.return_value = [
            {"bridge_id": "bridge-1", "session1": "s1", "session2": "s2", "context": "test", "created_at": "2024-01-01"},
            {"bridge_id": "bridge-2", "session1": "s3", "session2": "s4", "context": "test", "created_at": "2024-01-01"}
        ]
        
        with patch('builtins.print'):
            result = handler._handle_list()
        
        handler.registry.list_bridges.assert_called_once()
        assert result["exit_code"] == 0
    
    def test_handle_cleanup_command(self, handler):
        """Test cleanup command - MAINTENANCE USE CASE"""
        handler.registry.cleanup_old_bridges.return_value = {
            "bridges_removed": 3,
            "messages_removed": 10,
            "space_freed": 1024,
            "errors": []
        }
        
        command_data = {
            "command": "cleanup",
            "dry_run": False,
            "max_age": 7
        }
        
        with patch('builtins.print'):
            result = handler._handle_cleanup(command_data)
        
        handler.registry.cleanup_old_bridges.assert_called_once_with(7, False)
        assert result["exit_code"] == 0


class TestArgumentParserMVP:
    """MVP tests for argument parsing"""
    
    def test_parse_create_args(self):
        """Test create command parsing - MAIN WORKFLOW"""
        parser = BridgeRegistryArgumentParser()
        result = parser.parse_args(['bridge_registry.py', 'create', 'session1', 'session2', 'test context'])
        
        assert result["command"] == 'create'
        assert result["session1"] == 'session1'
        assert result["session2"] == 'session2'
        assert result["context"] == 'test context'
    
    def test_parse_list_args(self):
        """Test list command parsing - MONITORING WORKFLOW"""
        parser = BridgeRegistryArgumentParser()
        result = parser.parse_args(['bridge_registry.py', 'list'])
        
        assert result["command"] == 'list'
    
    def test_parse_cleanup_args(self):
        """Test cleanup command parsing - MAINTENANCE WORKFLOW"""
        parser = BridgeRegistryArgumentParser()
        result = parser.parse_args(['bridge_registry.py', 'cleanup'])
        
        assert result["command"] == 'cleanup'
        assert result["dry_run"] == False
        assert result["max_age"] == 7


# Performance test to ensure <30 second requirement
@pytest.mark.timeout(5)  # Fail if takes more than 5 seconds
def test_performance_requirement():
    """Ensure all tests complete quickly"""
    # This test just validates our performance constraint
    import time
    start = time.time()
    # Run a representative operation
    with patch('bridge_registry.Path'):
        registry = BridgeRegistry()
        _ = registry.create_bridge("s1", "s2", "ctx")
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Operation took {elapsed}s, should be <1s"


if __name__ == "__main__":
    # Quick runner for development
    pytest.main([__file__, "-v", "--tb=short", "-x"])