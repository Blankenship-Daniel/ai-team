#!/usr/bin/env python3
"""
Context Injector Implementation
Wraps UnifiedContextManager to implement IContextInjector protocol
"""

from pathlib import Path
from typing import Dict
from interfaces import IContextInjector
from unified_context_manager import UnifiedContextManager
from logging_config import setup_logging

logger = setup_logging(__name__)


class ContextInjector(IContextInjector):
    """
    DI-compliant context injector implementation.
    Delegates to UnifiedContextManager for actual functionality.
    """

    def __init__(self, install_dir: Path = None):
        """Initialize with UnifiedContextManager"""
        self._manager = UnifiedContextManager(install_dir=install_dir)
        logger.info("ContextInjector initialized with UnifiedContextManager")

    def inject_context(self, briefing: str, role: str, environment: Dict[str, str]) -> str:
        """Inject operational context into agent briefing"""
        return self._manager.inject_context(briefing, role, environment)

    def create_workspace(self, session_name: str, agent_name: str) -> Path:
        """Create agent workspace with tools and context"""
        return self._manager.create_workspace(session_name, agent_name)

    def sanitize_briefing(self, briefing: str) -> str:
        """Sanitize briefing for safe transmission"""
        return self._manager.sanitize_briefing(briefing)

    # Additional methods from UnifiedContextManager
    def create_recovery_script(self) -> Path:
        """Create recovery script for session restoration"""
        return self._manager.create_recovery_script()

    def verify_agent_readiness(self, session_name: str, agent_name: str) -> tuple:
        """Verify agent is ready with context and tools"""
        return self._manager.verify_agent_readiness(session_name, agent_name)
