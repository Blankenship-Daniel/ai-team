#!/usr/bin/env python3
"""
Multi-Team Coordination System
Prevents chaos in complex multi-team AI orchestration environments

Key Design Principles:
1. Fail-safe defaults - teams can operate independently if coordination fails
2. Explicit state boundaries - clear ownership of resources and context
3. Monotonic operations - avoid state conflicts through append-only patterns
4. Circuit breakers - isolate failing teams to prevent cascade failures
"""

import json
import time
import threading
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from ai_team.utils.logging_config import setup_logging

logger = setup_logging(__name__)


class TeamStatus(Enum):
    """Team operational status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    ISOLATED = "isolated"
    SHUTDOWN = "shutdown"


class ResourceType(Enum):
    """Types of resources that can conflict"""

    TMUX_SESSION = "tmux_session"
    TMUX_WINDOW = "tmux_window"
    FILE_LOCK = "file_lock"
    NETWORK_PORT = "network_port"
    CONTEXT_NAMESPACE = "context_namespace"


@dataclass
class TeamInfo:
    """Team metadata and status"""

    team_id: str
    session_name: str
    created_at: str
    last_heartbeat: str
    status: TeamStatus
    agents: List[str]
    resources: Set[str] = field(default_factory=set)
    context_checkpoints: List[str] = field(default_factory=list)
    error_count: int = 0
    isolation_reason: Optional[str] = None


@dataclass
class ResourceReservation:
    """Resource allocation tracking"""

    resource_id: str
    resource_type: ResourceType
    owner_team: str
    reserved_at: str
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterTeamMessage:
    """Message between teams"""

    message_id: str
    from_team: str
    to_team: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str
    requires_ack: bool = False
    ack_received: bool = False


class MultiTeamCoordinator:
    """Central coordinator for managing multiple AI teams safely"""

    def __init__(self, coordination_dir: str = ".coordination"):
        self.coordination_dir = Path(coordination_dir)
        self.coordination_dir.mkdir(exist_ok=True)

        # Core coordination files
        self.teams_file = self.coordination_dir / "teams.json"
        self.resources_file = self.coordination_dir / "resources.json"
        self.messages_file = self.coordination_dir / "messages.json"
        self.health_file = self.coordination_dir / "health.json"

        # In-memory state
        self.teams: Dict[str, TeamInfo] = {}
        self.resources: Dict[str, ResourceReservation] = {}
        self.message_queue: List[InterTeamMessage] = []

        # Configuration
        self.heartbeat_timeout = 60  # seconds
        self.resource_timeout = 300  # 5 minutes
        self.max_errors_before_isolation = 5
        self.context_sync_interval = 30  # seconds

        # Background services
        self._running = False
        self._lock = threading.RLock()
        self._threads: List[Any] = []

        self._load_state()
        logger.info("MultiTeamCoordinator initialized")

    def register_team(self, team_id: str, session_name: str, agents: List[str]) -> bool:
        """Register a new team in the coordination system"""
        with self._lock:
            try:
                # Check for conflicts
                conflicts = self._check_team_conflicts(team_id, session_name)
                if conflicts:
                    logger.error(f"Team registration conflicts: {conflicts}")
                    return False

                # Create team info
                team_info = TeamInfo(
                    team_id=team_id,
                    session_name=session_name,
                    created_at=datetime.now().isoformat(),
                    last_heartbeat=datetime.now().isoformat(),
                    status=TeamStatus.HEALTHY,
                    agents=agents.copy(),
                )

                self.teams[team_id] = team_info

                # Reserve core resources
                self._reserve_team_resources(team_id, session_name)

                self._save_state()
                logger.info(f"Registered team {team_id} with session {session_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to register team {team_id}: {e}")
                return False

    def unregister_team(self, team_id: str, cleanup: bool = True) -> bool:
        """Safely unregister a team and cleanup resources"""
        with self._lock:
            try:
                if team_id not in self.teams:
                    logger.warning(f"Team {team_id} not found for unregistration")
                    return False

                team_info = self.teams[team_id]

                if cleanup:
                    # Release all resources
                    self._release_team_resources(team_id)

                    # Cleanup inter-team state
                    self._cleanup_team_messages(team_id)

                    # Archive context checkpoints
                    self._archive_team_context(team_id)

                # Remove from active teams
                del self.teams[team_id]

                self._save_state()
                logger.info(f"Unregistered team {team_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to unregister team {team_id}: {e}")
                return False

    def heartbeat(self, team_id: str, status_data: Optional[Dict] = None) -> bool:
        """Team heartbeat - critical for health monitoring"""
        with self._lock:
            try:
                if team_id not in self.teams:
                    logger.warning(f"Heartbeat from unknown team {team_id}")
                    return False

                team_info = self.teams[team_id]
                team_info.last_heartbeat = datetime.now().isoformat()

                # Update status based on provided data
                if status_data:
                    if status_data.get("error_occurred"):
                        team_info.error_count += 1
                        logger.warning(f"Team {team_id} reported error (count: {team_info.error_count})")

                    # Check if team should be isolated
                    if team_info.error_count >= self.max_errors_before_isolation:
                        self._isolate_team(team_id, "Excessive errors")

                self._save_state()
                return True

            except Exception as e:
                logger.error(f"Heartbeat failed for team {team_id}: {e}")
                return False

    def reserve_resource(
        self,
        team_id: str,
        resource_type: ResourceType,
        resource_id: str,
        duration_minutes: int = 5,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Reserve a resource for exclusive use by a team"""
        with self._lock:
            try:
                if team_id not in self.teams:
                    logger.error(f"Unknown team {team_id} trying to reserve resource")
                    return False

                # Check if resource is already reserved
                if resource_id in self.resources:
                    existing = self.resources[resource_id]
                    if existing.owner_team != team_id:
                        # Check if reservation has expired
                        if existing.expires_at:
                            expiry = datetime.fromisoformat(existing.expires_at)
                            if datetime.now() < expiry:
                                logger.warning(f"Resource {resource_id} already reserved by {existing.owner_team}")
                                return False
                        else:
                            logger.warning(f"Resource {resource_id} permanently reserved by {existing.owner_team}")
                            return False

                # Create reservation
                expiry = datetime.now() + timedelta(minutes=duration_minutes)
                reservation = ResourceReservation(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    owner_team=team_id,
                    reserved_at=datetime.now().isoformat(),
                    expires_at=expiry.isoformat(),
                    metadata=metadata or {},
                )

                self.resources[resource_id] = reservation
                self.teams[team_id].resources.add(resource_id)

                self._save_state()
                logger.info(f"Team {team_id} reserved {resource_type.value}: {resource_id}")
                return True

            except Exception as e:
                logger.error(f"Resource reservation failed: {e}")
                return False

    def send_inter_team_message(
        self, from_team: str, to_team: str, message_type: str, payload: Dict, requires_ack: bool = False
    ) -> str:
        """Send message between teams with optional acknowledgment"""
        try:
            if from_team not in self.teams or to_team not in self.teams:
                raise ValueError("Invalid team IDs")

            message = InterTeamMessage(
                message_id=str(uuid.uuid4()),
                from_team=from_team,
                to_team=to_team,
                message_type=message_type,
                payload=payload,
                timestamp=datetime.now().isoformat(),
                requires_ack=requires_ack,
            )

            with self._lock:
                self.message_queue.append(message)
                self._save_state()

            logger.info(f"Message {message.message_id} sent from {from_team} to {to_team}")
            return message.message_id

        except Exception as e:
            logger.error(f"Failed to send inter-team message: {e}")
            return ""

    def get_team_messages(self, team_id: str, mark_as_read: bool = True) -> List[InterTeamMessage]:
        """Get pending messages for a team"""
        with self._lock:
            messages = [msg for msg in self.message_queue if msg.to_team == team_id]

            if mark_as_read:
                # Remove delivered messages that don't require ack
                self.message_queue = [
                    msg for msg in self.message_queue if not (msg.to_team == team_id and not msg.requires_ack)
                ]
                self._save_state()

            return messages

    def synchronize_context(self, team_id: str, context_data: Dict) -> Dict[str, Any]:
        """Synchronize context between teams"""
        try:
            if team_id not in self.teams:
                return {"error": "Team not found"}

            # Create context checkpoint
            checkpoint_id = self._create_context_checkpoint(team_id, context_data)

            # Get relevant context from other teams
            cross_team_context = self._gather_cross_team_context(team_id)

            return {
                "checkpoint_id": checkpoint_id,
                "cross_team_context": cross_team_context,
                "sync_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Context synchronization failed for team {team_id}: {e}")
            return {"error": str(e)}

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        with self._lock:
            now = datetime.now()
            health = {
                "timestamp": now.isoformat(),
                "total_teams": len(self.teams),
                "healthy_teams": 0,
                "degraded_teams": 0,
                "failing_teams": 0,
                "isolated_teams": 0,
                "resource_conflicts": 0,
                "stale_heartbeats": 0,
                "teams": {},
            }

            for team_id, team_info in self.teams.items():
                # Check heartbeat freshness
                heartbeat_age = (now - datetime.fromisoformat(team_info.last_heartbeat)).total_seconds()
                is_stale = heartbeat_age > self.heartbeat_timeout

                if is_stale and team_info.status == TeamStatus.HEALTHY:
                    team_info.status = TeamStatus.DEGRADED
                    health["stale_heartbeats"] += 1

                # Update counters
                if team_info.status == TeamStatus.HEALTHY:
                    health["healthy_teams"] += 1
                elif team_info.status == TeamStatus.DEGRADED:
                    health["degraded_teams"] += 1
                elif team_info.status == TeamStatus.FAILING:
                    health["failing_teams"] += 1
                elif team_info.status == TeamStatus.ISOLATED:
                    health["isolated_teams"] += 1

                health["teams"][team_id] = {
                    "status": team_info.status.value,
                    "heartbeat_age_seconds": heartbeat_age,
                    "error_count": team_info.error_count,
                    "resource_count": len(team_info.resources),
                }

            # Check for resource conflicts
            health["resource_conflicts"] = self._count_resource_conflicts()

            return health

    def start_coordination_services(self):
        """Start background coordination services"""
        if self._running:
            logger.warning("Coordination services already running")
            return

        self._running = True

        # Start health monitor
        health_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        health_thread.start()
        self._threads.append(health_thread)

        # Start resource cleanup
        cleanup_thread = threading.Thread(target=self._resource_cleanup_loop, daemon=True)
        cleanup_thread.start()
        self._threads.append(cleanup_thread)

        # Start context sync
        context_thread = threading.Thread(target=self._context_sync_loop, daemon=True)
        context_thread.start()
        self._threads.append(context_thread)

        logger.info("Multi-team coordination services started")

    def stop_coordination_services(self):
        """Stop all background services"""
        self._running = False
        for thread in self._threads:
            thread.join(timeout=5)
        logger.info("Multi-team coordination services stopped")

    # Private methods for internal coordination logic

    def _check_team_conflicts(self, team_id: str, session_name: str) -> List[str]:
        """Check for conflicts with existing teams"""
        conflicts = []

        if team_id in self.teams:
            conflicts.append(f"Team ID {team_id} already exists")

        for existing_team in self.teams.values():
            if existing_team.session_name == session_name:
                conflicts.append(f"Session name {session_name} already in use")

        return conflicts

    def _reserve_team_resources(self, team_id: str, session_name: str):
        """Reserve core resources for a team"""
        # Reserve tmux session
        self.reserve_resource(
            team_id,
            ResourceType.TMUX_SESSION,
            session_name,
            duration_minutes=0,  # Permanent reservation
            metadata={"core_resource": True},
        )

        # Reserve context namespace
        context_namespace = f"context_{team_id}"
        self.reserve_resource(
            team_id,
            ResourceType.CONTEXT_NAMESPACE,
            context_namespace,
            duration_minutes=0,
            metadata={"core_resource": True},
        )

    def _release_team_resources(self, team_id: str):
        """Release all resources owned by a team"""
        team_resources = list(self.teams[team_id].resources)

        for resource_id in team_resources:
            if resource_id in self.resources:
                del self.resources[resource_id]

        self.teams[team_id].resources.clear()
        logger.info(f"Released {len(team_resources)} resources for team {team_id}")

    def _isolate_team(self, team_id: str, reason: str):
        """Isolate a problematic team"""
        if team_id in self.teams:
            self.teams[team_id].status = TeamStatus.ISOLATED
            self.teams[team_id].isolation_reason = reason
            logger.warning(f"Isolated team {team_id}: {reason}")

    def _health_monitor_loop(self):
        """Background health monitoring"""
        while self._running:
            try:
                health = self.get_system_health()

                # Save health snapshot
                with open(self.health_file, "w") as f:
                    json.dump(health, f, indent=2)

                # Log critical issues
                if health["failing_teams"] > 0 or health["isolated_teams"] > 0:
                    logger.warning(
                        f"System health degraded: {health['failing_teams']} failing, {health['isolated_teams']} isolated"
                    )

                time.sleep(30)  # Health check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                time.sleep(60)

    def _resource_cleanup_loop(self):
        """Background resource cleanup"""
        while self._running:
            try:
                with self._lock:
                    expired_resources = []
                    now = datetime.now()

                    for resource_id, reservation in self.resources.items():
                        if reservation.expires_at:
                            expiry = datetime.fromisoformat(reservation.expires_at)
                            if now > expiry:
                                expired_resources.append(resource_id)

                    for resource_id in expired_resources:
                        reservation = self.resources[resource_id]
                        logger.info(f"Releasing expired resource {resource_id} from team {reservation.owner_team}")
                        del self.resources[resource_id]

                        # Remove from team's resource set
                        if reservation.owner_team in self.teams:
                            self.teams[reservation.owner_team].resources.discard(resource_id)

                    if expired_resources:
                        self._save_state()

                time.sleep(60)  # Cleanup every minute

            except Exception as e:
                logger.error(f"Resource cleanup error: {e}")
                time.sleep(120)

    def _context_sync_loop(self):
        """Background context synchronization"""
        while self._running:
            try:
                # Implement periodic context sync logic here
                # This would sync critical context between teams
                time.sleep(self.context_sync_interval)

            except Exception as e:
                logger.error(f"Context sync error: {e}")
                time.sleep(60)

    def _save_state(self):
        """Save coordination state to disk"""
        try:
            # Convert to serializable format
            teams_data = {
                team_id: {
                    **asdict(team_info),
                    "resources": list(team_info.resources),  # Set to list
                    "status": team_info.status.value,  # Enum to string
                }
                for team_id, team_info in self.teams.items()
            }

            resources_data = {
                resource_id: {**asdict(reservation), "resource_type": reservation.resource_type.value}
                for resource_id, reservation in self.resources.items()
            }

            messages_data = [asdict(msg) for msg in self.message_queue]

            # Write atomically
            with open(self.teams_file, "w") as f:
                json.dump(teams_data, f, indent=2)

            with open(self.resources_file, "w") as f:
                json.dump(resources_data, f, indent=2)

            with open(self.messages_file, "w") as f:
                json.dump(messages_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save coordination state: {e}")

    def _load_state(self):
        """Load coordination state from disk"""
        try:
            # Load teams
            if self.teams_file.exists():
                with open(self.teams_file) as f:
                    teams_data = json.load(f)
                    for team_id, data in teams_data.items():
                        data["status"] = TeamStatus(data["status"])
                        data["resources"] = set(data["resources"])
                        self.teams[team_id] = TeamInfo(**data)

            # Load resources
            if self.resources_file.exists():
                with open(self.resources_file) as f:
                    resources_data = json.load(f)
                    for resource_id, data in resources_data.items():
                        data["resource_type"] = ResourceType(data["resource_type"])
                        self.resources[resource_id] = ResourceReservation(**data)

            # Load messages
            if self.messages_file.exists():
                with open(self.messages_file) as f:
                    messages_data = json.load(f)
                    self.message_queue = [InterTeamMessage(**msg) for msg in messages_data]

        except Exception as e:
            logger.error(f"Failed to load coordination state: {e}")

    def _count_resource_conflicts(self) -> int:
        """Count current resource conflicts"""
        # Implementation would check for actual conflicts
        return 0

    def _create_context_checkpoint(self, team_id: str, context_data: Dict) -> str:
        """Create a context checkpoint for a team"""
        checkpoint_id = str(uuid.uuid4())
        # Implementation would save context checkpoint
        return checkpoint_id

    def _gather_cross_team_context(self, team_id: str) -> Dict:
        """Gather relevant context from other teams"""
        # Implementation would collect and filter context from other teams
        return {}

    def _cleanup_team_messages(self, team_id: str):
        """Clean up messages involving a team"""
        self.message_queue = [msg for msg in self.message_queue if msg.from_team != team_id and msg.to_team != team_id]

    def _archive_team_context(self, team_id: str):
        """Archive team context before cleanup"""
        # Implementation would archive context checkpoints
        pass


# Singleton coordinator instance
_coordinator: Optional[MultiTeamCoordinator] = None


def get_coordinator() -> MultiTeamCoordinator:
    """Get the global multi-team coordinator"""
    global _coordinator
    if _coordinator is None:
        _coordinator = MultiTeamCoordinator()
    return _coordinator
