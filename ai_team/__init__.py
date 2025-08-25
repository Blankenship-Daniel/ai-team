"""
AI Team - Tmux-based AI agent orchestration framework
"""

__version__ = "2.0.0"
__author__ = "AI Team Contributors"

from ai_team.core.unified_context_manager import UnifiedContextManager
from ai_team.utils.tmux_utils import TmuxOrchestrator
from ai_team.agents.agent_profile_factory import AgentProfileFactory

__all__ = [
    "UnifiedContextManager",
    "TmuxOrchestrator", 
    "AgentProfileFactory",
]