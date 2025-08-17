#!/usr/bin/env python3
"""
Context Registry - Immutable checkpoint-based context persistence
Foundational layer for bulletproof agent context management
"""

import json
import sqlite3
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass(frozen=True)
class ContextCheckpoint:
    """Immutable context checkpoint"""

    id: str
    agent_id: str
    session_name: str
    window_index: int
    timestamp: str
    context_version: str
    context_hash: str
    context_data: Dict[str, Any]
    parent_checkpoint_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        agent_id: str,
        session_name: str,
        window_index: int,
        context_data: Dict[str, Any],
        parent_id: Optional[str] = None,
    ) -> "ContextCheckpoint":
        """Create new immutable checkpoint"""
        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create deterministic hash of context data
        context_json = json.dumps(context_data, sort_keys=True, separators=(",", ":"))
        context_hash = hashlib.sha256(context_json.encode()).hexdigest()

        return cls(
            id=checkpoint_id,
            agent_id=agent_id,
            session_name=session_name,
            window_index=window_index,
            timestamp=timestamp,
            context_version="3.0",
            context_hash=context_hash,
            context_data=context_data,
            parent_checkpoint_id=parent_id,
        )

    def verify_integrity(self) -> bool:
        """Verify checkpoint data integrity"""
        context_json = json.dumps(self.context_data, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256(context_json.encode()).hexdigest()
        return expected_hash == self.context_hash


@dataclass
class ContextState:
    """Mutable context state for an agent"""

    agent_id: str
    current_task: Optional[str] = None
    working_directory: Optional[str] = None
    last_commit: Optional[str] = None
    tools_available: Optional[List[str]] = None
    git_branch: Optional[str] = None
    session_start_time: Optional[str] = None
    message_count: int = 0
    last_checkpoint_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.tools_available is None:
            self.tools_available = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextState":
        """Create from dictionary"""
        return cls(**data)


class SQLiteContextStore:
    """SQLite-based persistent storage for context checkpoints"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_name TEXT NOT NULL,
                    window_index INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    context_version TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_checkpoint_id) REFERENCES checkpoints(id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_timestamp
                ON checkpoints(agent_id, timestamp DESC)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_session_window
                ON checkpoints(session_name, window_index, timestamp DESC)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_context_hash
                ON checkpoints(context_hash)
            """
            )

            conn.commit()
            logger.debug(f"Initialized context database at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def store(self, checkpoint: ContextCheckpoint) -> bool:
        """Store checkpoint atomically"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO checkpoints (
                        id, agent_id, session_name, window_index,
                        timestamp, context_version, context_hash,
                        context_data, parent_checkpoint_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        checkpoint.id,
                        checkpoint.agent_id,
                        checkpoint.session_name,
                        checkpoint.window_index,
                        checkpoint.timestamp,
                        checkpoint.context_version,
                        checkpoint.context_hash,
                        json.dumps(checkpoint.context_data),
                        checkpoint.parent_checkpoint_id,
                    ),
                )
                conn.commit()
                logger.debug(f"Stored checkpoint {checkpoint.id[:8]} for {checkpoint.agent_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to store checkpoint: {e}")
            return False

    def get(self, checkpoint_id: str) -> Optional[ContextCheckpoint]:
        """Retrieve specific checkpoint"""
        try:
            with self._get_connection() as conn:
                row = conn.execute("SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)).fetchone()

                if row:
                    return ContextCheckpoint(
                        id=row["id"],
                        agent_id=row["agent_id"],
                        session_name=row["session_name"],
                        window_index=row["window_index"],
                        timestamp=row["timestamp"],
                        context_version=row["context_version"],
                        context_hash=row["context_hash"],
                        context_data=json.loads(row["context_data"]),
                        parent_checkpoint_id=row["parent_checkpoint_id"],
                    )
        except Exception as e:
            logger.error(f"Failed to retrieve checkpoint {checkpoint_id}: {e}")
        return None

    def get_latest(self, agent_id: str) -> Optional[ContextCheckpoint]:
        """Get most recent checkpoint for agent"""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT * FROM checkpoints
                    WHERE agent_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """,
                    (agent_id,),
                ).fetchone()

                if row:
                    return ContextCheckpoint(
                        id=row["id"],
                        agent_id=row["agent_id"],
                        session_name=row["session_name"],
                        window_index=row["window_index"],
                        timestamp=row["timestamp"],
                        context_version=row["context_version"],
                        context_hash=row["context_hash"],
                        context_data=json.loads(row["context_data"]),
                        parent_checkpoint_id=row["parent_checkpoint_id"],
                    )
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for {agent_id}: {e}")
        return None

    def get_checkpoint_chain(self, checkpoint_id: str) -> List[ContextCheckpoint]:
        """Get full chain of checkpoints leading to given checkpoint"""
        chain = []
        current_id: Optional[str] = checkpoint_id

        while current_id:
            checkpoint = self.get(current_id)
            if not checkpoint:
                break
            chain.append(checkpoint)
            current_id = checkpoint.parent_checkpoint_id

        return list(reversed(chain))  # Return chronological order

    def cleanup_old_checkpoints(self, agent_id: str, keep_count: int = 100):
        """Clean up old checkpoints, keeping only the most recent"""
        try:
            with self._get_connection() as conn:
                # Get checkpoints to delete
                rows = conn.execute(
                    """
                    SELECT id FROM checkpoints
                    WHERE agent_id = ?
                    ORDER BY timestamp DESC
                    OFFSET ?
                """,
                    (agent_id, keep_count),
                ).fetchall()

                if rows:
                    ids_to_delete = [row[0] for row in rows]
                    placeholders = ",".join(["?"] * len(ids_to_delete))

                    # Use parameterized query - placeholders are safe (just "?" repeated)
                    query = f"""
                        DELETE FROM checkpoints
                        WHERE id IN ({placeholders})
                    """  # nosec B608

                    conn.execute(query, ids_to_delete)

                    conn.commit()
                    logger.info(f"Cleaned up {len(ids_to_delete)} old checkpoints for {agent_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")


class ContextRegistry:
    """
    Centralized context state management with immutable checkpoints.

    This is the foundational layer for bulletproof context persistence.
    Provides atomic operations, versioning, and recovery capabilities.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path.cwd() / ".context-registry"

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize storage backend
        db_path = self.storage_dir / "context.db"
        self.store = SQLiteContextStore(db_path)

        # In-memory state cache
        self.active_states: Dict[str, ContextState] = {}
        self.checkpoint_cache: Dict[str, ContextCheckpoint] = {}

        logger.info(f"ContextRegistry initialized at {self.storage_dir}")

    def get_agent_key(self, session_name: str, window_index: int) -> str:
        """Generate consistent agent key"""
        return f"{session_name}:{window_index}"

    def create_checkpoint(self, session_name: str, window_index: int, context_data: Dict[str, Any]) -> str:
        """
        Create immutable context checkpoint.

        Returns:
            Checkpoint ID
        """
        agent_key = self.get_agent_key(session_name, window_index)

        # Get current state for parent reference
        current_state = self.active_states.get(agent_key)
        parent_id = current_state.last_checkpoint_id if current_state else None

        # Create new checkpoint
        checkpoint = ContextCheckpoint.create(
            agent_id=agent_key,
            session_name=session_name,
            window_index=window_index,
            context_data=context_data,
            parent_id=parent_id,
        )

        # Verify integrity before storing
        if not checkpoint.verify_integrity():
            raise ValueError("Checkpoint failed integrity check")

        # Store atomically
        if not self.store.store(checkpoint):
            raise RuntimeError("Failed to store checkpoint")

        # Update in-memory state
        if agent_key not in self.active_states:
            self.active_states[agent_key] = ContextState(agent_id=agent_key)

        self.active_states[agent_key].last_checkpoint_id = checkpoint.id
        self.active_states[agent_key].message_count += 1

        # Cache the checkpoint
        self.checkpoint_cache[checkpoint.id] = checkpoint

        logger.info(f"Created checkpoint {checkpoint.id[:8]} for {agent_key}")
        return checkpoint.id

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[ContextCheckpoint]:
        """
        Restore context from specific checkpoint.

        Returns:
            ContextCheckpoint if found, None otherwise
        """
        # Check cache first
        checkpoint: Optional[ContextCheckpoint]
        if checkpoint_id in self.checkpoint_cache:
            checkpoint = self.checkpoint_cache[checkpoint_id]
        else:
            # Load from storage
            checkpoint = self.store.get(checkpoint_id)
            if checkpoint:
                self.checkpoint_cache[checkpoint_id] = checkpoint

        if checkpoint:
            # Verify integrity
            if not checkpoint.verify_integrity():
                logger.error(f"Checkpoint {checkpoint_id} failed integrity check")
                return None

            # Update active state
            agent_key = checkpoint.agent_id
            if agent_key not in self.active_states:
                self.active_states[agent_key] = ContextState(agent_id=agent_key)

            self.active_states[agent_key].last_checkpoint_id = checkpoint.id

            logger.info(f"Restored checkpoint {checkpoint_id[:8]} for {agent_key}")
            return checkpoint

        logger.warning(f"Checkpoint {checkpoint_id} not found")
        return None

    def get_latest_checkpoint(self, session_name: str, window_index: int) -> Optional[ContextCheckpoint]:
        """Get most recent checkpoint for agent"""
        agent_key = self.get_agent_key(session_name, window_index)
        return self.store.get_latest(agent_key)

    def update_state(self, session_name: str, window_index: int, **updates):
        """Update active state for agent"""
        agent_key = self.get_agent_key(session_name, window_index)

        if agent_key not in self.active_states:
            self.active_states[agent_key] = ContextState(agent_id=agent_key)

        state = self.active_states[agent_key]
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                if state.metadata is None:
                    state.metadata = {}
                state.metadata[key] = value

        logger.debug(f"Updated state for {agent_key}: {updates}")

    def get_state(self, session_name: str, window_index: int) -> ContextState:
        """Get current state for agent"""
        agent_key = self.get_agent_key(session_name, window_index)

        if agent_key not in self.active_states:
            self.active_states[agent_key] = ContextState(agent_id=agent_key)

        return self.active_states[agent_key]

    def should_create_checkpoint(self, session_name: str, window_index: int, threshold: int = 5) -> bool:
        """Determine if checkpoint should be created based on message count"""
        state = self.get_state(session_name, window_index)
        return state.message_count >= threshold

    def get_checkpoint_summary(self, session_name: str, window_index: int) -> Dict[str, Any]:
        """Get summary of checkpoints for agent"""
        agent_key = self.get_agent_key(session_name, window_index)

        try:
            with self.store._get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_checkpoints,
                        MIN(timestamp) as first_checkpoint,
                        MAX(timestamp) as latest_checkpoint
                    FROM checkpoints
                    WHERE agent_id = ?
                """,
                    (agent_key,),
                ).fetchone()

                return {
                    "agent_id": agent_key,
                    "total_checkpoints": row["total_checkpoints"] if row else 0,
                    "first_checkpoint": row["first_checkpoint"] if row else None,
                    "latest_checkpoint": row["latest_checkpoint"] if row else None,
                    "current_state": self.get_state(session_name, window_index).to_dict(),
                }
        except Exception as e:
            logger.error(f"Failed to get checkpoint summary: {e}")
            return {"error": str(e)}

    def cleanup(self, session_name: Optional[str] = None, keep_count: int = 100):
        """Clean up old checkpoints"""
        if session_name:
            # Clean specific session
            for window_index in range(10):  # Assume max 10 windows
                agent_key = self.get_agent_key(session_name, window_index)
                self.store.cleanup_old_checkpoints(agent_key, keep_count)
        else:
            # Clean all agents
            for agent_key in self.active_states.keys():
                self.store.cleanup_old_checkpoints(agent_key, keep_count)
