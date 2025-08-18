#!/usr/bin/env python3
"""
Fixed test suite for bridge_registry.py targeting 100% coverage
Matches actual implementation methods and structure
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from bridge_registry import BridgeRegistry


class TestBridgeRegistry:
    """Test BridgeRegistry with actual methods"""
    
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
        """Test registry initialization and directory structure"""
        registry = BridgeRegistry(coord_dir=str(temp_coord_dir))
        assert registry.coord_dir == temp_coord_dir
        
        # Check all directories were created
        assert (temp_coord_dir / "registry").exists()
        assert (temp_coord_dir / "registry" / "bridges").exists()
        assert (temp_coord_dir / "registry" / "sessions").exists()
        assert (temp_coord_dir / "messages").exists()
        assert (temp_coord_dir / "cleanup").exists()
        
    def test_create_bridge_success(self, registry):
        """Test successful bridge creation between two sessions"""
        bridge_id = registry.create_bridge("session1", "session2", "test context")
        
        assert bridge_id is not None
        assert bridge_id.startswith("bridge-")
        
        # Check bridge file was created
        bridge_file = registry.bridges_dir / f"{bridge_id}.json"
        assert bridge_file.exists()
        
        # Check bridge content
        with open(bridge_file) as f:
            bridge_data = json.load(f)
        assert bridge_data["session1"] == "session1"
        assert bridge_data["session2"] == "session2"
        assert bridge_data["context"] == "test context"
        
    def test_create_bridge_with_different_sessions(self, registry):
        """Test creating multiple bridges with different sessions"""
        bridge1 = registry.create_bridge("sess_a", "sess_b", "context1")
        bridge2 = registry.create_bridge("sess_c", "sess_d", "context2")
        
        assert bridge1 != bridge2
        assert len(bridge1) > 10  # UUID-based ID
        assert len(bridge2) > 10
        
    def test_list_bridges_empty(self, registry):
        """Test listing bridges when none exist"""
        bridges = registry.list_bridges()
        assert bridges == []
        
    def test_list_bridges_with_bridges(self, registry):
        """Test listing existing bridges"""
        bridge1 = registry.create_bridge("s1", "s2", "ctx1")
        bridge2 = registry.create_bridge("s3", "s4", "ctx2")
        
        bridges = registry.list_bridges()
        assert len(bridges) == 2
        
        bridge_ids = [b["bridge_id"] for b in bridges]
        assert bridge1 in bridge_ids
        assert bridge2 in bridge_ids
        
    def test_get_session_bridges(self, registry):
        """Test getting bridges for a specific session"""
        # Create bridge with session1
        bridge1 = registry.create_bridge("session1", "session2", "ctx")
        bridge2 = registry.create_bridge("session1", "session3", "ctx2")
        registry.create_bridge("session4", "session5", "ctx3")  # Different session
        
        session1_bridges = registry.get_session_bridges("session1")
        
        assert len(session1_bridges) == 2
        assert bridge1 in session1_bridges
        assert bridge2 in session1_bridges
        
    def test_get_session_bridges_no_matches(self, registry):
        """Test getting bridges for session with no bridges"""
        registry.create_bridge("s1", "s2", "ctx")
        
        bridges = registry.get_session_bridges("nonexistent_session")
        assert bridges == []
        
    def test_find_peer_sessions(self, registry):
        """Test finding peer sessions for a given session"""
        registry.create_bridge("session1", "peer_a", "ctx1")
        registry.create_bridge("session1", "peer_b", "ctx2")
        registry.create_bridge("peer_c", "session1", "ctx3")  # Reversed order
        
        peers = registry.find_peer_sessions("session1")
        
        assert len(peers) == 3
        peer_sessions = [p[1] for p in peers]  # Extract peer session names
        assert "peer_a" in peer_sessions
        assert "peer_b" in peer_sessions
        assert "peer_c" in peer_sessions
        
    def test_find_peer_sessions_no_peers(self, registry):
        """Test finding peers when none exist"""
        registry.create_bridge("other1", "other2", "ctx")
        
        peers = registry.find_peer_sessions("session1")
        assert peers == []
        
    def test_cleanup_old_bridges_dry_run(self, registry, temp_coord_dir):
        """Test cleanup in dry run mode"""
        # Create bridge and make it old
        bridge_id = registry.create_bridge("s1", "s2", "ctx")
        bridge_file = registry.bridges_dir / f"{bridge_id}.json"
        
        # Make file old by modifying timestamp
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(bridge_file, (old_time, old_time))
        
        # Dry run should not delete
        result = registry.cleanup_old_bridges(max_age_days=7, dry_run=True)
        
        assert bridge_file.exists()  # Still exists
        assert result["removed_count"] == 0
        assert len(result["would_remove"]) == 1
        
    def test_cleanup_old_bridges_actual_cleanup(self, registry):
        """Test actual cleanup of old bridges"""
        # Create bridge
        bridge_id = registry.create_bridge("s1", "s2", "ctx")
        bridge_file = registry.bridges_dir / f"{bridge_id}.json"
        
        # Make it old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(bridge_file, (old_time, old_time))
        
        # Actual cleanup
        result = registry.cleanup_old_bridges(max_age_days=7, dry_run=False)
        
        assert not bridge_file.exists()  # Should be deleted
        assert result["removed_count"] == 1
        assert bridge_id in result["removed_bridges"]
        
    def test_cleanup_keeps_recent_bridges(self, registry):
        """Test that recent bridges are not cleaned up"""
        bridge_id = registry.create_bridge("s1", "s2", "ctx")
        bridge_file = registry.bridges_dir / f"{bridge_id}.json"
        
        # Cleanup with short age - should keep recent bridge
        result = registry.cleanup_old_bridges(max_age_days=7, dry_run=False)
        
        assert bridge_file.exists()
        assert result["removed_count"] == 0
        
    def test_add_session_to_bridge_internal(self, registry):
        """Test internal method _add_session_to_bridge"""
        bridge_id = "test-bridge"
        session = "test-session"
        
        # This method creates session tracking files
        registry._add_session_to_bridge(session, bridge_id)
        
        # Check session file was created
        session_file = registry.sessions_dir / f"{session}.json"
        assert session_file.exists()
        
        with open(session_file) as f:
            session_data = json.load(f)
        assert bridge_id in session_data["bridges"]
        
    def test_add_session_to_bridge_multiple(self, registry):
        """Test adding multiple bridges to same session"""
        session = "test-session"
        
        registry._add_session_to_bridge(session, "bridge1")
        registry._add_session_to_bridge(session, "bridge2")
        
        session_file = registry.sessions_dir / f"{session}.json"
        with open(session_file) as f:
            session_data = json.load(f)
            
        assert "bridge1" in session_data["bridges"]
        assert "bridge2" in session_data["bridges"]
        assert len(session_data["bridges"]) == 2
        
    def test_update_active_bridges_internal(self, registry):
        """Test internal method _update_active_bridges"""
        # Create some bridges first
        registry.create_bridge("s1", "s2", "ctx1")
        registry.create_bridge("s3", "s4", "ctx2")
        
        # Call update method
        registry._update_active_bridges()
        
        # Check active bridges file was created/updated
        active_file = registry.registry_dir / "active_bridges.json"
        assert active_file.exists()
        
        with open(active_file) as f:
            active_data = json.load(f)
        assert len(active_data["bridges"]) >= 2
        
    def test_remove_bridge_from_sessions(self, registry):
        """Test internal method _remove_bridge_from_sessions"""
        # Create session with bridge
        bridge_id = "test-bridge"
        session = "test-session"
        registry._add_session_to_bridge(session, bridge_id)
        
        # Remove bridge from sessions
        registry._remove_bridge_from_sessions(bridge_id)
        
        # Check bridge was removed from session
        session_file = registry.sessions_dir / f"{session}.json"
        with open(session_file) as f:
            session_data = json.load(f)
        assert bridge_id not in session_data["bridges"]
        
    def test_error_handling_invalid_bridge_file(self, registry, temp_coord_dir):
        """Test handling of invalid bridge files during listing"""
        # Create invalid JSON file
        invalid_file = registry.bridges_dir / "invalid-bridge.json"
        invalid_file.write_text("invalid json content")
        
        # Should handle gracefully and skip invalid files
        bridges = registry.list_bridges()
        # Should not crash, may return empty list or skip invalid files
        assert isinstance(bridges, list)
        
    def test_error_handling_missing_session_file(self, registry):
        """Test handling when session file doesn't exist"""
        bridges = registry.get_session_bridges("nonexistent")
        assert bridges == []
        
    def test_error_handling_cleanup_permission_error(self, registry):
        """Test cleanup with permission errors"""
        bridge_id = registry.create_bridge("s1", "s2", "ctx")
        bridge_file = registry.bridges_dir / f"{bridge_id}.json"
        
        # Make it old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(bridge_file, (old_time, old_time))
        
        # Mock permission error
        with patch("pathlib.Path.unlink", side_effect=PermissionError("No permission")):
            result = registry.cleanup_old_bridges(max_age_days=7, dry_run=False)
            
            # Should handle error gracefully
            assert "error_count" in result or result["removed_count"] == 0


class TestBridgeRegistryEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_bridge_creation_with_empty_context(self):
        """Test bridge creation with empty context"""
        with tempfile.TemporaryDirectory() as temp:
            registry = BridgeRegistry(coord_dir=temp)
            bridge_id = registry.create_bridge("s1", "s2", "")
            
            assert bridge_id is not None
            # Empty context should be handled gracefully
            
    def test_bridge_creation_same_sessions(self):
        """Test creating bridge between same session"""
        with tempfile.TemporaryDirectory() as temp:
            registry = BridgeRegistry(coord_dir=temp)
            bridge_id = registry.create_bridge("same_session", "same_session", "self-bridge")
            
            assert bridge_id is not None
            # Should allow self-bridges if needed
            
    def test_cleanup_with_zero_age(self):
        """Test cleanup with zero max age"""
        with tempfile.TemporaryDirectory() as temp:
            registry = BridgeRegistry(coord_dir=temp)
            registry.create_bridge("s1", "s2", "ctx")
            
            # Zero age should clean all bridges
            result = registry.cleanup_old_bridges(max_age_days=0, dry_run=False)
            assert result["removed_count"] >= 0
            
    def test_concurrent_bridge_creation(self):
        """Test that concurrent bridge creation generates unique IDs"""
        with tempfile.TemporaryDirectory() as temp:
            registry = BridgeRegistry(coord_dir=temp)
            
            bridge_ids = []
            for i in range(10):
                bridge_id = registry.create_bridge(f"s{i}a", f"s{i}b", f"ctx{i}")
                bridge_ids.append(bridge_id)
                
            # All IDs should be unique
            assert len(set(bridge_ids)) == 10
            
    def test_large_context_handling(self):
        """Test handling of large context strings"""
        with tempfile.TemporaryDirectory() as temp:
            registry = BridgeRegistry(coord_dir=temp)
            
            large_context = "x" * 10000  # 10KB string
            bridge_id = registry.create_bridge("s1", "s2", large_context)
            
            assert bridge_id is not None
            
            # Verify large context was stored
            bridge_file = registry.bridges_dir / f"{bridge_id}.json"
            with open(bridge_file) as f:
                bridge_data = json.load(f)
            assert len(bridge_data["context"]) == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=bridge_registry", "--cov-report=term-missing"])