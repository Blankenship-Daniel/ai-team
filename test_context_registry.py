#!/usr/bin/env python3
"""
Comprehensive tests for ContextRegistry - Bulletproof context persistence
"""

import pytest
import tempfile
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Import the classes we're testing
from context_registry import ContextCheckpoint, ContextState, SQLiteContextStore, ContextRegistry


class TestContextCheckpoint:
    """Test immutable checkpoint functionality"""

    def test_checkpoint_creation(self):
        """Test checkpoint creation with proper immutability"""
        context_data = {"current_task": "testing", "working_directory": "/test", "tools": ["tmux", "git"]}

        checkpoint = ContextCheckpoint.create(
            agent_id="test:0", session_name="test", window_index=0, context_data=context_data
        )

        assert checkpoint.agent_id == "test:0"
        assert checkpoint.session_name == "test"
        assert checkpoint.window_index == 0
        assert checkpoint.context_version == "3.0"
        assert checkpoint.context_data == context_data
        assert checkpoint.parent_checkpoint_id is None

        # Test immutability
        with pytest.raises(AttributeError):
            checkpoint.agent_id = "modified"

    def test_checkpoint_integrity_verification(self):
        """Test cryptographic integrity verification"""
        context_data = {"task": "security_test"}

        checkpoint = ContextCheckpoint.create(
            agent_id="security:0", session_name="security", window_index=0, context_data=context_data
        )

        # Checkpoint should verify correctly
        assert checkpoint.verify_integrity() is True

        # Manually create checkpoint with wrong hash
        bad_checkpoint = ContextCheckpoint(
            id=checkpoint.id,
            agent_id=checkpoint.agent_id,
            session_name=checkpoint.session_name,
            window_index=checkpoint.window_index,
            timestamp=checkpoint.timestamp,
            context_version=checkpoint.context_version,
            context_hash="bad_hash",
            context_data=checkpoint.context_data,
        )

        # Should fail integrity check
        assert bad_checkpoint.verify_integrity() is False

    def test_checkpoint_deterministic_hash(self):
        """Test that identical context produces identical hash"""
        context_data = {"task": "hash_test", "data": [1, 2, 3]}

        checkpoint1 = ContextCheckpoint.create(
            agent_id="hash:0", session_name="hash", window_index=0, context_data=context_data
        )

        checkpoint2 = ContextCheckpoint.create(
            agent_id="hash:1", session_name="hash", window_index=1, context_data=context_data
        )

        # Same context data should produce same hash
        assert checkpoint1.context_hash == checkpoint2.context_hash

        # Different context should produce different hash
        different_context = {"task": "different", "data": [1, 2, 3]}
        checkpoint3 = ContextCheckpoint.create(
            agent_id="hash:2", session_name="hash", window_index=2, context_data=different_context
        )

        assert checkpoint1.context_hash != checkpoint3.context_hash


class TestContextState:
    """Test mutable context state"""

    def test_state_creation_and_mutation(self):
        """Test state creation and modification"""
        state = ContextState(agent_id="test:0")

        assert state.agent_id == "test:0"
        assert state.message_count == 0
        assert state.tools_available == []
        assert state.metadata == {}

        # Test mutation
        state.current_task = "new_task"
        state.message_count = 5
        state.tools_available.append("pytest")
        state.metadata["custom"] = "value"

        assert state.current_task == "new_task"
        assert state.message_count == 5
        assert "pytest" in state.tools_available
        assert state.metadata["custom"] == "value"

    def test_state_serialization(self):
        """Test state to/from dict conversion"""
        state = ContextState(
            agent_id="serial:0",
            current_task="serialization_test",
            tools_available=["tool1", "tool2"],
            metadata={"key": "value"},
        )

        # Convert to dict
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["agent_id"] == "serial:0"
        assert state_dict["current_task"] == "serialization_test"

        # Convert back from dict
        restored_state = ContextState.from_dict(state_dict)
        assert restored_state.agent_id == state.agent_id
        assert restored_state.current_task == state.current_task
        assert restored_state.tools_available == state.tools_available
        assert restored_state.metadata == state.metadata


class TestSQLiteContextStore:
    """Test SQLite storage backend"""

    def test_store_and_retrieve_checkpoint(self):
        """Test basic storage and retrieval"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteContextStore(Path(tmpdir) / "test.db")

            # Create test checkpoint
            context_data = {"test": "data"}
            checkpoint = ContextCheckpoint.create(
                agent_id="store:0", session_name="store", window_index=0, context_data=context_data
            )

            # Store checkpoint
            assert store.store(checkpoint) is True

            # Retrieve checkpoint
            retrieved = store.get(checkpoint.id)
            assert retrieved is not None
            assert retrieved.id == checkpoint.id
            assert retrieved.context_data == checkpoint.context_data
            assert retrieved.verify_integrity() is True

    def test_get_latest_checkpoint(self):
        """Test getting most recent checkpoint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteContextStore(Path(tmpdir) / "test.db")

            agent_id = "latest:0"

            # Store multiple checkpoints
            for i in range(3):
                context_data = {"iteration": i}
                checkpoint = ContextCheckpoint.create(
                    agent_id=agent_id, session_name="latest", window_index=0, context_data=context_data
                )
                store.store(checkpoint)

            # Get latest should return the last one
            latest = store.get_latest(agent_id)
            assert latest is not None
            assert latest.context_data["iteration"] == 2

    def test_checkpoint_chain(self):
        """Test checkpoint parent-child relationships"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteContextStore(Path(tmpdir) / "test.db")

            # Create chain of checkpoints
            parent = None
            checkpoints = []

            for i in range(3):
                context_data = {"step": i}
                checkpoint = ContextCheckpoint.create(
                    agent_id="chain:0",
                    session_name="chain",
                    window_index=0,
                    context_data=context_data,
                    parent_id=parent.id if parent else None,
                )
                store.store(checkpoint)
                checkpoints.append(checkpoint)
                parent = checkpoint

            # Get full chain
            chain = store.get_checkpoint_chain(checkpoints[-1].id)
            assert len(chain) == 3
            assert chain[0].context_data["step"] == 0
            assert chain[1].context_data["step"] == 1
            assert chain[2].context_data["step"] == 2

    def test_cleanup_old_checkpoints(self):
        """Test cleanup of old checkpoints"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteContextStore(Path(tmpdir) / "test.db")

            agent_id = "cleanup:0"

            # Create many checkpoints
            for i in range(10):
                context_data = {"iteration": i}
                checkpoint = ContextCheckpoint.create(
                    agent_id=agent_id, session_name="cleanup", window_index=0, context_data=context_data
                )
                store.store(checkpoint)

            # Cleanup keeping only 3
            store.cleanup_old_checkpoints(agent_id, keep_count=3)

            # Verify only 3 remain
            with store._get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM checkpoints WHERE agent_id = ?", (agent_id,)).fetchone()[0]
                assert count == 3

    def test_database_corruption_handling(self):
        """Test handling of database corruption"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "corrupt.db"
            store = SQLiteContextStore(db_path)

            # Create a checkpoint
            context_data = {"test": "corruption"}
            checkpoint = ContextCheckpoint.create(
                agent_id="corrupt:0", session_name="corrupt", window_index=0, context_data=context_data
            )
            store.store(checkpoint)

            # Corrupt the database by writing garbage
            with open(db_path, "wb") as f:
                f.write(b"corrupt_data")

            # Should handle corruption gracefully
            new_store = SQLiteContextStore(db_path)
            result = new_store.get(checkpoint.id)
            # Should return None or raise handled exception, not crash


class TestContextRegistry:
    """Test the main ContextRegistry class"""

    def test_registry_initialization(self):
        """Test registry initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            assert registry.storage_dir.exists()
            assert (registry.storage_dir / "context.db").exists()
            assert isinstance(registry.active_states, dict)

    def test_create_and_restore_checkpoint(self):
        """Test complete checkpoint lifecycle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Create checkpoint
            context_data = {"current_task": "lifecycle_test", "working_directory": "/test", "tools": ["tmux", "git"]}

            checkpoint_id = registry.create_checkpoint(
                session_name="lifecycle", window_index=0, context_data=context_data
            )

            assert checkpoint_id is not None
            assert len(checkpoint_id) == 36  # UUID length

            # Restore checkpoint
            restored = registry.restore_checkpoint(checkpoint_id)
            assert restored is not None
            assert restored.context_data == context_data
            assert restored.verify_integrity() is True

    def test_state_management(self):
        """Test active state management"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Update state
            registry.update_state(
                session_name="state", window_index=0, current_task="state_test", custom_field="custom_value"
            )

            # Get state
            state = registry.get_state("state", 0)
            assert state.current_task == "state_test"
            assert state.metadata["custom_field"] == "custom_value"

    def test_checkpoint_threshold(self):
        """Test checkpoint creation threshold"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Should not need checkpoint initially
            assert registry.should_create_checkpoint("threshold", 0, threshold=5) is False

            # Simulate message count increase
            state = registry.get_state("threshold", 0)
            state.message_count = 6

            # Should need checkpoint now
            assert registry.should_create_checkpoint("threshold", 0, threshold=5) is True

    def test_get_checkpoint_summary(self):
        """Test checkpoint summary functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Create multiple checkpoints
            for i in range(3):
                context_data = {"iteration": i}
                registry.create_checkpoint(session_name="summary", window_index=0, context_data=context_data)

            # Get summary
            summary = registry.get_checkpoint_summary("summary", 0)
            assert summary["total_checkpoints"] == 3
            assert summary["agent_id"] == "summary:0"
            assert "current_state" in summary

    def test_concurrent_access(self):
        """Test concurrent access safety"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Simulate concurrent checkpoint creation
            import threading
            import time

            results = []
            errors = []

            def create_checkpoint_worker(worker_id):
                try:
                    for i in range(5):
                        context_data = {"worker": worker_id, "iteration": i}
                        checkpoint_id = registry.create_checkpoint(
                            session_name=f"worker_{worker_id}", window_index=0, context_data=context_data
                        )
                        results.append(checkpoint_id)
                        time.sleep(0.01)  # Small delay
                except Exception as e:
                    errors.append(e)

            # Create multiple threads
            threads = []
            for worker_id in range(3):
                thread = threading.Thread(target=create_checkpoint_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Verify no errors and all checkpoints created
            assert len(errors) == 0
            assert len(results) == 15  # 3 workers × 5 iterations
            assert len(set(results)) == 15  # All unique IDs


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""

    def test_agent_session_simulation(self):
        """Simulate complete agent session with context preservation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            session_name = "integration"
            window_index = 0

            # 1. Agent starts session
            registry.update_state(
                session_name,
                window_index,
                current_task="Initialize project",
                working_directory="/project",
                session_start_time=datetime.now(timezone.utc).isoformat(),
            )

            # 2. First checkpoint after initial setup
            context_1 = {
                "phase": "initialization",
                "files_created": ["README.md", "src/main.py"],
                "git_status": "clean",
            }
            checkpoint_1 = registry.create_checkpoint(session_name, window_index, context_1)

            # 3. Agent does some work
            registry.update_state(session_name, window_index, current_task="Implement feature X")

            # 4. Second checkpoint after feature work
            context_2 = {
                "phase": "development",
                "files_modified": ["src/main.py", "src/feature_x.py"],
                "tests_passing": True,
                "git_commits": 2,
            }
            checkpoint_2 = registry.create_checkpoint(session_name, window_index, context_2)

            # 5. Simulate context loss and recovery
            restored_context = registry.restore_checkpoint(checkpoint_2)
            assert restored_context is not None
            assert restored_context.context_data["phase"] == "development"
            assert restored_context.context_data["tests_passing"] is True

            # 6. Verify checkpoint chain
            latest = registry.get_latest_checkpoint(session_name, window_index)
            assert latest.id == checkpoint_2

            # 7. Get session summary
            summary = registry.get_checkpoint_summary(session_name, window_index)
            assert summary["total_checkpoints"] == 2

    def test_multi_agent_orchestration(self):
        """Test multiple agents with independent context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Set up multiple agents
            agents = [("orchestrator", 0), ("alex-architect", 1), ("morgan-shipper", 2), ("sam-janitor", 3)]

            # Each agent creates checkpoints
            checkpoint_ids = {}
            for session, window in agents:
                context_data = {
                    "agent_role": session.split("-")[0],
                    "specialization": session.split("-")[1] if "-" in session else "coordinator",
                    "current_task": f"Working on {session} tasks",
                }

                checkpoint_id = registry.create_checkpoint(session, window, context_data)
                checkpoint_ids[f"{session}:{window}"] = checkpoint_id

            # Verify each agent has independent context
            for (session, window), checkpoint_id in checkpoint_ids.items():
                restored = registry.restore_checkpoint(checkpoint_id)
                assert restored is not None
                assert restored.session_name == session
                assert restored.window_index == window

            # Verify cross-agent isolation
            alex_checkpoint = registry.restore_checkpoint(checkpoint_ids["alex-architect:1"])
            morgan_checkpoint = registry.restore_checkpoint(checkpoint_ids["morgan-shipper:2"])

            assert alex_checkpoint.context_data["specialization"] == "architect"
            assert morgan_checkpoint.context_data["specialization"] == "shipper"

    def test_disaster_recovery(self):
        """Test recovery from various failure scenarios"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContextRegistry(Path(tmpdir))

            # Create initial state
            context_data = {"critical": "data", "state": "important"}
            checkpoint_id = registry.create_checkpoint("disaster", 0, context_data)

            # Scenario 1: Registry restart (simulates process restart)
            del registry
            new_registry = ContextRegistry(Path(tmpdir))

            # Should be able to restore from persistent storage
            restored = new_registry.restore_checkpoint(checkpoint_id)
            assert restored is not None
            assert restored.context_data == context_data

            # Scenario 2: Partial data corruption (test graceful degradation)
            # This would be tested with mocked corruption scenarios

            # Scenario 3: Network partition recovery
            # Multiple registries should be able to sync (future enhancement)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
