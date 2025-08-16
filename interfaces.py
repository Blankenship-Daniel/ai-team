#!/usr/bin/env python3
"""
Protocol Interfaces for Clean Architecture
Defines contracts for dependency injection and SOLID refactoring
"""

from typing import Protocol, Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentProfile:
    """Value object for agent configuration"""

    name: str
    personality: str
    role: str
    briefing: str
    window_name: str


@dataclass
class SessionInfo:
    """Value object for tmux session details"""

    name: str
    working_dir: str
    window_count: int
    pane_layout: Dict[str, str]


class IAgentProfileFactory(Protocol):
    """Factory for creating agent profiles with different strategies"""

    def create_default_profiles(self) -> List[AgentProfile]:
        """Create the standard Alex/Morgan/Sam agent profiles"""
        ...

    def create_custom_profile(self, name: str, role: str, personality_type: str) -> AgentProfile:
        """Create a custom agent profile"""
        ...

    def validate_profile(self, profile: AgentProfile) -> Tuple[bool, Optional[str]]:
        """Validate agent profile for completeness and security"""
        ...


class ITmuxSessionManager(Protocol):
    """Interface for tmux session operations"""

    def create_session(self, session_info: SessionInfo) -> bool:
        """Create new tmux session with specified configuration"""
        ...

    def destroy_session(self, session_name: str) -> bool:
        """Safely destroy tmux session"""
        ...

    def session_exists(self, session_name: str) -> bool:
        """Check if session exists"""
        ...

    def create_pane_layout(self, session_name: str, layout_config: Dict[str, Any]) -> bool:
        """Create pane layout for agents"""
        ...

    def send_to_pane(self, pane_target: str, message: str) -> bool:
        """Send message to specific pane"""
        ...


class IContextInjector(Protocol):
    """Interface for context and briefing management"""

    def inject_context(self, briefing: str, role: str, environment: Dict[str, str]) -> str:
        """Inject operational context into agent briefing"""
        ...

    def create_workspace(self, session_name: str, agent_name: str) -> Path:
        """Create agent workspace with tools and context"""
        ...

    def sanitize_briefing(self, briefing: str) -> str:
        """Sanitize briefing for safe transmission"""
        ...


class ITeamCoordinator(Protocol):
    """Interface for orchestrating the complete team creation process"""

    def coordinate_team_creation(
        self, session_name: str, agents: List[AgentProfile], working_dir: str
    ) -> Tuple[bool, Optional[str]]:
        """Coordinate the complete team creation process"""
        ...

    def setup_orchestrator(self, session_name: str, working_dir: str) -> bool:
        """Setup the orchestrator pane with briefing"""
        ...

    def verify_team_readiness(self, session_name: str, agents: List[AgentProfile]) -> Tuple[bool, List[str]]:
        """Verify all agents are properly initialized"""
        ...


class ISecurityValidator(Protocol):
    """Interface for security validation operations"""

    def validate_session_name(self, session_name: str) -> Tuple[bool, Optional[str]]:
        """Validate tmux session name for security"""
        ...

    def validate_pane_target(self, pane_target: str) -> Tuple[bool, Optional[str]]:
        """Validate tmux pane target"""
        ...

    def sanitize_message(self, message: str) -> str:
        """Sanitize message for safe transmission"""
        ...

    def validate_file_path(self, file_path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate file path for safety"""
        ...


class IMessageRouter(Protocol):
    """Interface for inter-team message routing"""

    def route_message(self, from_session: str, to_session: str, message: str) -> bool:
        """Route message between sessions"""
        ...

    def auto_detect_session(self) -> str:
        """Auto-detect current session for routing"""
        ...

    def establish_bridge(self, session1: str, session2: str) -> bool:
        """Establish bidirectional communication bridge"""
        ...


class IBridgeEstablisher(Protocol):
    """Interface for establishing team-to-team bridges"""

    def create_bridge(self, team1: str, team2: str, bridge_type: str) -> bool:
        """Create communication bridge between teams"""
        ...

    def list_available_teams(self) -> List[str]:
        """List teams available for bridging"""
        ...

    def get_bridge_status(self) -> Dict[str, Any]:
        """Get status of all active bridges"""
        ...


# Dependency Injection Container Interface


class IDependencyContainer(Protocol):
    """Interface for dependency injection container"""

    def register(self, interface_type: type, implementation: Any) -> None:
        """Register implementation for interface"""
        ...

    def resolve(self, interface_type: type) -> Any:
        """Resolve implementation for interface"""
        ...

    def register_singleton(self, interface_type: type, implementation: Any) -> None:
        """Register singleton implementation"""
        ...


# Configuration Interfaces


class IConfiguration(Protocol):
    """Interface for configuration management"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        ...

    def load_from_file(self, config_path: Path) -> None:
        """Load configuration from file"""
        ...


# Abstract Base Classes for Complex Implementations


class BaseTeamOrchestrator(ABC):
    """Base class for team orchestration implementations"""

    def __init__(
        self,
        profile_factory: IAgentProfileFactory,
        session_manager: ITmuxSessionManager,
        context_injector: IContextInjector,
        security_validator: ISecurityValidator,
    ):
        self.profile_factory = profile_factory
        self.session_manager = session_manager
        self.context_injector = context_injector
        self.security_validator = security_validator

    @abstractmethod
    def create_team(self, session_name: str, working_dir: str) -> bool:
        """Template method for team creation"""
        pass

    def _validate_inputs(self, session_name: str, working_dir: str) -> Tuple[bool, Optional[str]]:
        """Common validation logic"""
        valid, error = self.security_validator.validate_session_name(session_name)
        if not valid:
            return False, error

        valid, error = self.security_validator.validate_file_path(working_dir, must_exist=True)
        if not valid:
            return False, error

        return True, None


# Type Aliases for Complex Types

PaneLayout = Dict[str, str]  # pane_id -> agent_name
BridgeConfig = Dict[str, Any]  # Configuration for bridge establishment
ValidationResult = Tuple[bool, Optional[str]]  # (is_valid, error_message)
TeamCreationResult = Tuple[bool, Optional[str]]  # (success, error_message)
