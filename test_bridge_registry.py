#!/usr/bin/env python3
"""
Comprehensive test suite for bridge_registry.py
Targets 100% code coverage from current 51%
Focus on error paths, edge cases, and command pattern implementation
"""

import pytest
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call, mock_open
import uuid
import sys

from bridge_registry import BridgeRegistry


class TestBridgeRegistry:
    """Test BridgeRegistry core functionality"""
    
    @pytest.fixture
    def temp_coord_dir(self):
        """Create temporary coordination directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)
        
    @pytest.fixture
    def registry(self, temp_coord_dir):
        """Create BridgeRegistry with temp directory"""
        return BridgeRegistry(coord_dir=str(temp_coord_dir))
        
    def test_initialization(self, temp_coord_dir):
        """Test registry initialization"""
        registry = BridgeRegistry(coord_dir=str(temp_coord_dir))
        assert registry.coord_dir == temp_coord_dir
        assert temp_coord_dir.exists()
        assert registry.bridges == {}
        
    def test_initialization_creates_directory(self):
        """Test that initialization creates directory if missing"""
        with tempfile.TemporaryDirectory() as temp:
            coord_path = Path(temp) / "new_coord_dir"
            registry = BridgeRegistry(coord_dir=str(coord_path))
            assert coord_path.exists()
            
    def test_create_bridge_success(self, registry, temp_coord_dir):
        """Test successful bridge creation"""
        bridge_id = registry.create_bridge("TestTeam", {"config": "value"})
        
        assert bridge_id is not None
        assert bridge_id in registry.bridges
        assert registry.bridges[bridge_id]["team_name"] == "TestTeam"
        assert registry.bridges[bridge_id]["metadata"]["config"] == "value"
        
        # Check bridge file was created
        bridge_file = temp_coord_dir / f"bridge_{bridge_id}.json"
        assert bridge_file.exists()
        
    def test_create_bridge_with_custom_id(self, registry):
        """Test bridge creation with custom ID"""
        custom_id = "custom-bridge-123"
        bridge_id = registry.create_bridge("Team", {}, bridge_id=custom_id)
        
        assert bridge_id == custom_id
        assert custom_id in registry.bridges
        
    def test_create_bridge_duplicate_id(self, registry):
        """Test creating bridge with duplicate ID"""
        bridge_id = registry.create_bridge("Team1", {})
        
        # Try to create with same ID
        duplicate_id = registry.create_bridge("Team2", {}, bridge_id=bridge_id)
        assert duplicate_id != bridge_id  # Should generate new ID
        
    def test_list_bridges_empty(self, registry):
        """Test listing bridges when none exist"""
        bridges = registry.list_bridges()
        assert bridges == []
        
    def test_list_bridges_multiple(self, registry):
        """Test listing multiple bridges"""
        id1 = registry.create_bridge("Team1", {})
        id2 = registry.create_bridge("Team2", {})
        
        bridges = registry.list_bridges()
        assert len(bridges) == 2
        
        bridge_ids = [b["id"] for b in bridges]
        assert id1 in bridge_ids
        assert id2 in bridge_ids
        
    def test_list_bridges_active_only(self, registry):
        """Test listing only active bridges"""
        active_id = registry.create_bridge("ActiveTeam", {})
        inactive_id = registry.create_bridge("InactiveTeam", {})
        
        # Mark one as inactive
        registry.bridges[inactive_id]["active"] = False
        
        active_bridges = registry.list_bridges(active_only=True)
        assert len(active_bridges) == 1
        assert active_bridges[0]["id"] == active_id
        
    def test_get_bridge_exists(self, registry):
        """Test getting existing bridge"""
        bridge_id = registry.create_bridge("Team", {"key": "value"})
        
        bridge = registry.get_bridge(bridge_id)
        assert bridge is not None
        assert bridge["team_name"] == "Team"
        assert bridge["metadata"]["key"] == "value"
        
    def test_get_bridge_not_exists(self, registry):
        """Test getting non-existent bridge"""
        bridge = registry.get_bridge("non-existent-id")
        assert bridge is None
        
    def test_update_bridge_success(self, registry):
        """Test updating bridge metadata"""
        bridge_id = registry.create_bridge("Team", {"old": "value"})
        
        success = registry.update_bridge(bridge_id, {"new": "data", "extra": 123})
        assert success is True
        
        bridge = registry.get_bridge(bridge_id)
        assert bridge["metadata"]["new"] == "data"
        assert bridge["metadata"]["extra"] == 123
        assert "old" not in bridge["metadata"]  # Replaced, not merged
        
    def test_update_bridge_not_exists(self, registry):
        """Test updating non-existent bridge"""
        success = registry.update_bridge("non-existent", {"data": "value"})
        assert success is False
        
    def test_delete_bridge_success(self, registry, temp_coord_dir):
        """Test successful bridge deletion"""
        bridge_id = registry.create_bridge("Team", {})
        bridge_file = temp_coord_dir / f"bridge_{bridge_id}.json"
        assert bridge_file.exists()
        
        success = registry.delete_bridge(bridge_id)
        assert success is True
        assert bridge_id not in registry.bridges
        assert not bridge_file.exists()
        
    def test_delete_bridge_not_exists(self, registry):
        """Test deleting non-existent bridge"""
        success = registry.delete_bridge("non-existent")
        assert success is False
        
    def test_cleanup_old_bridges(self, registry):
        """Test cleaning up old bridges"""
        # Create old bridge
        old_id = registry.create_bridge("OldTeam", {})
        registry.bridges[old_id]["created_at"] = (
            datetime.now() - timedelta(hours=3)
        ).isoformat()
        
        # Create recent bridge
        new_id = registry.create_bridge("NewTeam", {})
        
        # Cleanup bridges older than 2 hours
        cleaned = registry.cleanup_old_bridges(max_age_hours=2)
        
        assert len(cleaned) == 1
        assert old_id in cleaned
        assert old_id not in registry.bridges
        assert new_id in registry.bridges
        
    def test_cleanup_old_bridges_none_old(self, registry):
        """Test cleanup when no bridges are old enough"""
        registry.create_bridge("Team1", {})
        registry.create_bridge("Team2", {})
        
        cleaned = registry.cleanup_old_bridges(max_age_hours=24)
        assert cleaned == []
        assert len(registry.bridges) == 2
        
    def test_monitor_bridges(self, registry):
        """Test monitoring bridge health"""
        # Create bridges with different states
        healthy_id = registry.create_bridge("HealthyTeam", {})
        unhealthy_id = registry.create_bridge("UnhealthyTeam", {})
        
        # Mark one as unhealthy
        registry.bridges[unhealthy_id]["last_heartbeat"] = (
            datetime.now() - timedelta(minutes=10)
        ).isoformat()
        
        with patch("builtins.print") as mock_print:
            registry.monitor_bridges()
            
        # Check monitoring output
        calls = mock_print.call_args_list
        assert any("HealthyTeam" in str(call) for call in calls)
        assert any("healthy" in str(call).lower() for call in calls)
        
    def test_persist_bridges(self, registry, temp_coord_dir):
        """Test persisting bridges to disk"""
        bridge_id = registry.create_bridge("Team", {"data": "value"})
        
        # Verify file was created
        bridge_file = temp_coord_dir / f"bridge_{bridge_id}.json"
        assert bridge_file.exists()
        
        # Verify content
        with open(bridge_file) as f:
            saved_data = json.load(f)
        assert saved_data["team_name"] == "Team"
        assert saved_data["metadata"]["data"] == "value"
        
    def test_persist_bridges_error(self, registry):
        """Test persist with write error"""
        bridge_id = registry.create_bridge("Team", {})
        
        with patch("builtins.open", side_effect=PermissionError("No write access")):
            # Should handle error gracefully
            registry.persist_bridges()  # Should not raise
            
    def test_load_bridges(self, registry, temp_coord_dir):
        """Test loading bridges from disk"""
        # Create bridge file manually
        bridge_data = {
            "id": "test-bridge",
            "team_name": "LoadedTeam",
            "created_at": datetime.now().isoformat(),
            "active": True,
            "metadata": {"loaded": True}
        }
        
        bridge_file = temp_coord_dir / "bridge_test-bridge.json"
        with open(bridge_file, "w") as f:
            json.dump(bridge_data, f)
            
        # Load bridges
        registry.load_bridges()
        
        assert "test-bridge" in registry.bridges
        assert registry.bridges["test-bridge"]["team_name"] == "LoadedTeam"
        
    def test_load_bridges_invalid_json(self, registry, temp_coord_dir):
        """Test loading with invalid JSON file"""
        invalid_file = temp_coord_dir / "bridge_invalid.json"
        invalid_file.write_text("not valid json")
        
        # Should handle error gracefully
        registry.load_bridges()  # Should not raise
        
    def test_load_bridges_no_files(self, registry):
        """Test loading when no bridge files exist"""
        registry.load_bridges()
        assert registry.bridges == {}
        
    def test_heartbeat(self, registry):
        """Test updating bridge heartbeat"""
        bridge_id = registry.create_bridge("Team", {})
        original_heartbeat = registry.bridges[bridge_id].get("last_heartbeat")
        
        import time
        time.sleep(0.01)
        
        registry.heartbeat(bridge_id)
        new_heartbeat = registry.bridges[bridge_id]["last_heartbeat"]
        
        assert new_heartbeat != original_heartbeat
        
    def test_heartbeat_nonexistent(self, registry):
        """Test heartbeat for non-existent bridge"""
        # Should not raise
        registry.heartbeat("non-existent")
        
    def test_is_bridge_healthy(self, registry):
        """Test checking bridge health"""
        bridge_id = registry.create_bridge("Team", {})
        
        # Fresh bridge should be healthy
        assert registry.is_bridge_healthy(bridge_id) is True
        
        # Old heartbeat should be unhealthy
        registry.bridges[bridge_id]["last_heartbeat"] = (
            datetime.now() - timedelta(minutes=10)
        ).isoformat()
        assert registry.is_bridge_healthy(bridge_id) is False
        
    def test_is_bridge_healthy_nonexistent(self, registry):
        """Test health check for non-existent bridge"""
        assert registry.is_bridge_healthy("non-existent") is False
        
    def test_get_bridge_age(self, registry):
        """Test getting bridge age"""
        bridge_id = registry.create_bridge("Team", {})
        
        # Set creation time to 1 hour ago
        registry.bridges[bridge_id]["created_at"] = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()
        
        age = registry.get_bridge_age(bridge_id)
        assert age is not None
        assert 0.9 < age < 1.1  # Approximately 1 hour
        
    def test_get_bridge_age_nonexistent(self, registry):
        """Test getting age of non-existent bridge"""
        age = registry.get_bridge_age("non-existent")
        assert age is None


class TestBridgeCommands:
    """Test Command pattern implementation"""
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock registry"""
        return Mock(spec=BridgeRegistry)
        
    def test_create_bridge_command_execute(self, mock_registry):
        """Test CreateBridgeCommand execution"""
        mock_registry.create_bridge.return_value = "bridge-123"
        
        command = CreateBridgeCommand(mock_registry, "TestTeam", {"key": "value"})
        result = command.execute()
        
        assert result == "bridge-123"
        mock_registry.create_bridge.assert_called_once_with("TestTeam", {"key": "value"}, None)
        
    def test_create_bridge_command_with_id(self, mock_registry):
        """Test CreateBridgeCommand with custom ID"""
        command = CreateBridgeCommand(mock_registry, "Team", {}, "custom-id")
        command.execute()
        
        mock_registry.create_bridge.assert_called_once_with("Team", {}, "custom-id")
        
    def test_list_bridges_command_execute(self, mock_registry):
        """Test ListBridgesCommand execution"""
        mock_bridges = [{"id": "1", "team": "A"}, {"id": "2", "team": "B"}]
        mock_registry.list_bridges.return_value = mock_bridges
        
        command = ListBridgesCommand(mock_registry)
        result = command.execute()
        
        assert result == mock_bridges
        mock_registry.list_bridges.assert_called_once_with(False)
        
    def test_list_bridges_command_active_only(self, mock_registry):
        """Test ListBridgesCommand with active_only flag"""
        command = ListBridgesCommand(mock_registry, active_only=True)
        command.execute()
        
        mock_registry.list_bridges.assert_called_once_with(True)
        
    def test_cleanup_bridge_command_execute(self, mock_registry):
        """Test CleanupBridgeCommand execution"""
        mock_registry.cleanup_old_bridges.return_value = ["old-1", "old-2"]
        
        command = CleanupBridgeCommand(mock_registry, max_age_hours=2)
        result = command.execute()
        
        assert result == ["old-1", "old-2"]
        mock_registry.cleanup_old_bridges.assert_called_once_with(2)
        
    def test_monitor_bridge_command_execute(self, mock_registry):
        """Test MonitorBridgeCommand execution"""
        command = MonitorBridgeCommand(mock_registry)
        result = command.execute()
        
        assert result is None
        mock_registry.monitor_bridges.assert_called_once()


class TestBridgeCommandInvoker:
    """Test command invoker functionality"""
    
    def test_add_and_execute_command(self):
        """Test adding and executing commands"""
        invoker = BridgeCommandInvoker()
        mock_command = Mock(spec=BridgeCommand)
        mock_command.execute.return_value = "result"
        
        invoker.add_command(mock_command)
        results = invoker.execute_commands()
        
        assert len(results) == 1
        assert results[0] == "result"
        mock_command.execute.assert_called_once()
        
    def test_execute_multiple_commands(self):
        """Test executing multiple commands"""
        invoker = BridgeCommandInvoker()
        
        commands = []
        for i in range(3):
            cmd = Mock(spec=BridgeCommand)
            cmd.execute.return_value = f"result-{i}"
            commands.append(cmd)
            invoker.add_command(cmd)
            
        results = invoker.execute_commands()
        
        assert len(results) == 3
        assert results == ["result-0", "result-1", "result-2"]
        
        for cmd in commands:
            cmd.execute.assert_called_once()
            
    def test_execute_with_exception(self):
        """Test command execution with exception"""
        invoker = BridgeCommandInvoker()
        
        # Add command that raises exception
        failing_cmd = Mock(spec=BridgeCommand)
        failing_cmd.execute.side_effect = ValueError("Command failed")
        
        # Add normal command
        normal_cmd = Mock(spec=BridgeCommand)
        normal_cmd.execute.return_value = "success"
        
        invoker.add_command(failing_cmd)
        invoker.add_command(normal_cmd)
        
        results = invoker.execute_commands()
        
        # Should handle exception and continue
        assert len(results) == 1
        assert results[0] == "success"
        
    def test_clear_commands(self):
        """Test clearing command queue"""
        invoker = BridgeCommandInvoker()
        
        invoker.add_command(Mock(spec=BridgeCommand))
        invoker.add_command(Mock(spec=BridgeCommand))
        
        assert len(invoker.commands) == 2
        
        invoker.clear_commands()
        assert len(invoker.commands) == 0


class TestMainFunction:
    """Test main() function and CLI integration"""
    
    def test_main_create_operation(self):
        """Test main with create operation"""
        test_args = ["bridge_registry.py", "create", "TestTeam", "--metadata", '{"key":"value"}']
        
        with patch("sys.argv", test_args):
            with patch("bridge_registry.BridgeRegistry") as MockRegistry:
                mock_instance = MockRegistry.return_value
                mock_instance.create_bridge.return_value = "bridge-123"
                
                # Import and run main
                from bridge_registry import main
                with patch("builtins.print") as mock_print:
                    main()
                    
                mock_instance.create_bridge.assert_called_once()
                mock_print.assert_called()
                
    def test_main_list_operation(self):
        """Test main with list operation"""
        test_args = ["bridge_registry.py", "list"]
        
        with patch("sys.argv", test_args):
            with patch("bridge_registry.BridgeRegistry") as MockRegistry:
                mock_instance = MockRegistry.return_value
                mock_instance.list_bridges.return_value = [
                    {"id": "1", "team_name": "Team1"},
                    {"id": "2", "team_name": "Team2"}
                ]
                
                from bridge_registry import main
                with patch("builtins.print") as mock_print:
                    main()
                    
                mock_instance.list_bridges.assert_called_once()
                assert mock_print.call_count > 0
                
    def test_main_cleanup_operation(self):
        """Test main with cleanup operation"""
        test_args = ["bridge_registry.py", "cleanup", "--max-age", "2"]
        
        with patch("sys.argv", test_args):
            with patch("bridge_registry.BridgeRegistry") as MockRegistry:
                mock_instance = MockRegistry.return_value
                mock_instance.cleanup_old_bridges.return_value = ["old-1"]
                
                from bridge_registry import main
                with patch("builtins.print") as mock_print:
                    main()
                    
                mock_instance.cleanup_old_bridges.assert_called_once_with(2)
                
    def test_main_monitor_operation(self):
        """Test main with monitor operation"""
        test_args = ["bridge_registry.py", "monitor"]
        
        with patch("sys.argv", test_args):
            with patch("bridge_registry.BridgeRegistry") as MockRegistry:
                mock_instance = MockRegistry.return_value
                
                from bridge_registry import main
                main()
                
                mock_instance.monitor_bridges.assert_called_once()
                
    def test_main_invalid_operation(self):
        """Test main with invalid operation"""
        test_args = ["bridge_registry.py", "invalid_op"]
        
        with patch("sys.argv", test_args):
            from bridge_registry import main
            with patch("builtins.print") as mock_print:
                main()
                
                # Should print error message
                assert any("Unknown" in str(call) for call in mock_print.call_args_list)
                
    def test_main_no_arguments(self):
        """Test main with no arguments"""
        test_args = ["bridge_registry.py"]
        
        with patch("sys.argv", test_args):
            from bridge_registry import main
            with patch("builtins.print") as mock_print:
                main()
                
                # Should print usage
                assert any("Usage" in str(call) for call in mock_print.call_args_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=bridge_registry", "--cov-report=term-missing"])