#!/usr/bin/env python3
"""
Simple Dependency Injection Container
Implements IDependencyContainer for clean architecture
"""

from typing import Dict, Type, Any, TypeVar, cast
from interfaces import IDependencyContainer
from logging_config import setup_logging

logger = setup_logging(__name__)

T = TypeVar("T")


class DependencyContainer:
    """Simple dependency injection container implementation"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._singleton_instances: Dict[Type, Any] = {}

    def register(self, interface_type: Type[T], implementation: Any) -> None:
        """Register implementation for interface"""
        self._services[interface_type] = implementation
        logger.debug(f"Registered {interface_type.__name__} -> {implementation}")

    def register_singleton(self, interface_type: Type[T], implementation: Any) -> None:
        """Register singleton implementation"""
        self._singletons[interface_type] = implementation
        logger.debug(f"Registered singleton {interface_type.__name__} -> {implementation}")

    def resolve(self, interface_type: Type[T]) -> T:
        """Resolve implementation for interface"""
        # Check singletons first
        if interface_type in self._singletons:
            if interface_type not in self._singleton_instances:
                implementation = self._singletons[interface_type]
                if callable(implementation):
                    self._singleton_instances[interface_type] = implementation()
                else:
                    self._singleton_instances[interface_type] = implementation
                logger.debug(f"Created singleton instance for {interface_type.__name__}")
            return cast(T, self._singleton_instances[interface_type])

        # Check regular services
        if interface_type in self._services:
            implementation = self._services[interface_type]
            if callable(implementation):
                instance = implementation()
                logger.debug(f"Created instance for {interface_type.__name__}")
                return cast(T, instance)
            else:
                return cast(T, implementation)

        raise ValueError(f"No implementation registered for {interface_type.__name__}")

    def is_registered(self, interface_type: Type) -> bool:
        """Check if interface is registered"""
        return interface_type in self._services or interface_type in self._singletons

    def clear(self) -> None:
        """Clear all registrations (useful for testing)"""
        self._services.clear()
        self._singletons.clear()
        self._singleton_instances.clear()
        logger.debug("Cleared all registrations")


# Global container instance
_container: DependencyContainer = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    return _container


def wire_dependencies() -> None:
    """
    Wire up all dependencies following Alex's architecture.
    This connects all components together for v1.1.
    """
    container = get_container()
    logger.info("Wiring dependencies for v1.1...")

    # Phase 1: Core security and validation
    from security_validator import SecurityValidator
    from interfaces import ISecurityValidator, IAgentProfileFactory

    container.register_singleton(ISecurityValidator, lambda: SecurityValidator())
    logger.debug("✓ Security validator registered")

    # Phase 2: Agent profile management
    from implementations.agent_profile_factory import AgentProfileFactory
    import os

    working_dir = os.getcwd()
    container.register_singleton(IAgentProfileFactory, lambda: AgentProfileFactory(working_dir))
    logger.debug("✓ Agent profile factory registered")

    # Phase 3: Context management - CONSOLIDATED BY SAM
    try:
        from implementations.context_injector import ContextInjector
        from interfaces import IContextInjector
        from pathlib import Path

        container.register_singleton(
            IContextInjector, lambda: ContextInjector(install_dir=Path(os.path.dirname(os.path.abspath(__file__))))
        )
        logger.debug("✓ Context injector registered (UnifiedContextManager consolidated)")
    except ImportError as e:
        logger.warning(f"Context injector not available: {e}")

    # Phase 4: Tmux session management
    try:
        from implementations.tmux_session_manager import TmuxSessionManager
        from interfaces import ITmuxSessionManager

        # TmuxSessionManager needs session name and working dir
        container.register_singleton(ITmuxSessionManager, lambda: TmuxSessionManager("ai-team", working_dir))
        logger.debug("✓ Tmux session manager registered")
    except ImportError as e:
        logger.debug(f"Tmux session manager not available: {e}")

    logger.info("Dependencies wired successfully!")
    return container


def configure_dependencies() -> None:
    """Configure default dependencies (backward compatibility)"""
    wire_dependencies()


# Decorator for dependency injection
def inject(interface_type: Type[T]) -> T:
    """Decorator/function to inject dependencies"""
    return get_container().resolve(interface_type)
