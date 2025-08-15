#!/usr/bin/env python3
"""
Agent Context Manager - Ensures agents have access to critical knowledge and tools
regardless of where the ai-team CLI is invoked from.

This module solves the architectural problem of context loss when agents are
created in different directories.
"""

import os
import shutil
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass
class AgentContext:
    """Represents the essential context an agent needs to function"""
    
    # Paths to critical files
    claude_md_path: str
    learnings_md_path: str
    send_message_script: str
    schedule_script: str
    
    # Content that should be injected into briefings
    tmux_commands: Dict[str, str]
    coordination_protocol: str
    workspace_path: str
    
    # Tool availability
    available_tools: List[str]
    tool_paths: Dict[str, str]


class AgentContextManager:
    """
    Manages context preservation for AI agents across different working directories.
    
    This class ensures that regardless of where the ai-team CLI is invoked,
    agents will have access to:
    1. Critical documentation (CLAUDE.md, LEARNINGS.md)
    2. Communication tools (send-claude-message.sh)
    3. Workspace for collaboration
    4. Knowledge of how to coordinate
    """
    
    # Essential files that must be accessible to agents
    ESSENTIAL_FILES = {
        'claude_md': 'docs/developer/CLAUDE.md',
        'learnings_md': 'docs/developer/LEARNINGS.md',
        'send_message': 'send-claude-message.sh',
        'schedule': 'schedule_with_note.sh',
    }
    
    # Tmux commands agents need to know
    TMUX_COMMANDS = {
        'list_windows': 'tmux list-windows -F "#{window_index}: #{window_name}"',
        'capture_pane': 'tmux capture-pane -t {target} -p',
        'send_message': './send-claude-message.sh {target} "{message}"',
        'check_session': 'tmux has-session -t {session}',
        'list_panes': 'tmux list-panes -t {session} -F "#{pane_index}: #{pane_title}"',
    }
    
    def __init__(self, orchestrator_root: Optional[str] = None):
        """
        Initialize the context manager.
        
        Args:
            orchestrator_root: Path to Tmux-Orchestrator installation.
                             If None, will try to auto-detect.
        """
        self.orchestrator_root = self._find_orchestrator_root(orchestrator_root)
        self.working_dir = Path.cwd()
        self.context_cache: Dict[str, AgentContext] = {}
        
        logger.info(f"AgentContextManager initialized", extra={
            'orchestrator_root': str(self.orchestrator_root),
            'working_dir': str(self.working_dir)
        })
    
    def _find_orchestrator_root(self, provided_path: Optional[str] = None) -> Path:
        """
        Find the Tmux-Orchestrator installation directory.
        
        Strategy:
        1. Use provided path if given
        2. Check if we're running from within Tmux-Orchestrator
        3. Check common installation locations
        4. Look for TMUX_ORCHESTRATOR_HOME environment variable
        """
        if provided_path:
            path = Path(provided_path)
            if path.exists() and (path / 'create_ai_team.py').exists():
                return path.resolve()
        
        # Check if we're already in the orchestrator directory
        current = Path(__file__).parent
        if (current / 'create_ai_team.py').exists():
            return current.resolve()
        
        # Check environment variable
        env_path = os.environ.get('TMUX_ORCHESTRATOR_HOME')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path.resolve()
        
        # Check common locations
        common_locations = [
            Path.home() / '.local' / 'share' / 'tmux-orchestrator',
            Path.home() / '.tmux-orchestrator',
            Path('/opt/tmux-orchestrator'),
            Path('/usr/local/share/tmux-orchestrator'),
        ]
        
        for location in common_locations:
            if location.exists() and (location / 'create_ai_team.py').exists():
                logger.info(f"Found orchestrator at {location}")
                return location.resolve()
        
        # Last resort: find through the module path
        import inspect
        module_path = Path(inspect.getfile(self.__class__)).parent
        if (module_path / 'create_ai_team.py').exists():
            return module_path.resolve()
        
        raise RuntimeError(
            "Cannot find Tmux-Orchestrator installation. "
            "Please set TMUX_ORCHESTRATOR_HOME environment variable."
        )
    
    def create_agent_workspace(self, session_name: str, agent_name: str) -> Path:
        """
        Create a dedicated workspace for an agent with necessary context.
        
        Args:
            session_name: The tmux session name
            agent_name: The agent's name (e.g., 'Alex-Purist')
            
        Returns:
            Path to the created workspace
        """
        # Create workspace directory
        workspace = self.working_dir / '.ai-team-workspaces' / session_name / agent_name
        workspace.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating workspace for {agent_name} at {workspace}")
        
        # Create context subdirectory
        context_dir = workspace / '.context'
        context_dir.mkdir(exist_ok=True)
        
        # Copy essential files
        for file_key, relative_path in self.ESSENTIAL_FILES.items():
            source = self.orchestrator_root / relative_path
            if source.exists():
                dest = context_dir / source.name
                shutil.copy2(source, dest)
                logger.debug(f"Copied {source.name} to agent workspace")
            else:
                logger.warning(f"Essential file not found: {source}")
        
        # Create tools directory with symlinks or copies
        tools_dir = workspace / '.tools'
        tools_dir.mkdir(exist_ok=True)
        
        # Copy or symlink tools
        tool_files = ['send-claude-message.sh', 'schedule_with_note.sh']
        for tool in tool_files:
            source = self.orchestrator_root / tool
            if source.exists():
                dest = tools_dir / tool
                # Copy instead of symlink for portability
                shutil.copy2(source, dest)
                # Make executable
                os.chmod(dest, 0o755)
                logger.debug(f"Installed tool {tool} in workspace")
        
        # Create context manifest
        self._create_context_manifest(workspace, session_name, agent_name)
        
        return workspace
    
    def _create_context_manifest(self, workspace: Path, session_name: str, agent_name: str):
        """
        Create a manifest file with all context information.
        
        This manifest helps agents understand their environment and capabilities.
        """
        manifest = {
            'session_name': session_name,
            'agent_name': agent_name,
            'workspace': str(workspace),
            'orchestrator_root': str(self.orchestrator_root),
            'working_directory': str(self.working_dir),
            'context_files': {
                'claude_md': str(workspace / '.context' / 'CLAUDE.md'),
                'learnings_md': str(workspace / '.context' / 'LEARNINGS.md'),
            },
            'tools': {
                'send_message': str(workspace / '.tools' / 'send-claude-message.sh'),
                'schedule': str(workspace / '.tools' / 'schedule_with_note.sh'),
            },
            'tmux_commands': self.TMUX_COMMANDS,
            'coordination_protocol': self._get_coordination_protocol(),
        }
        
        manifest_path = workspace / '.context' / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created context manifest for {agent_name}")
    
    def _get_coordination_protocol(self) -> str:
        """
        Returns the coordination protocol that agents should follow.
        """
        return """
AGENT COORDINATION PROTOCOL:

1. COMMUNICATION:
   - Use send-claude-message.sh to communicate with other agents
   - Format: ./send-claude-message.sh SESSION:WINDOW "Your message"
   - Check responses with: tmux capture-pane -t SESSION:WINDOW -p

2. WORKSPACE:
   - Your workspace is in .ai-team-workspaces/SESSION/YOUR_NAME/
   - Share files by writing to the workspace
   - Other agents can read from their workspaces

3. SYNCHRONIZATION:
   - Always announce when starting a task
   - Report completion status
   - Ask for help if blocked

4. CONTEXT FILES:
   - .context/CLAUDE.md - Core tmux commands and patterns
   - .context/LEARNINGS.md - Accumulated team knowledge
   - .context/manifest.json - Your environment configuration

5. AVAILABLE TOOLS:
   - .tools/send-claude-message.sh - Send messages to other agents
   - .tools/schedule_with_note.sh - Schedule future check-ins
"""
    
    def inject_context_into_briefing(self, original_briefing: str, 
                                    session_name: str, 
                                    agent_name: str,
                                    workspace: Path) -> str:
        """
        Inject critical context into an agent's briefing.
        
        This ensures the agent knows:
        1. Where their workspace is
        2. How to communicate
        3. Where to find documentation
        4. Available tools and their usage
        """
        context_injection = f"""

CRITICAL CONTEXT - READ THIS FIRST:

YOUR WORKSPACE: {workspace}
SESSION: {session_name}
YOUR NAME: {agent_name}

ESSENTIAL KNOWLEDGE LOCATIONS:
- Tmux commands: {workspace}/.context/CLAUDE.md
- Team learnings: {workspace}/.context/LEARNINGS.md
- Environment config: {workspace}/.context/manifest.json

COMMUNICATION TOOLS (in {workspace}/.tools/):
- send-claude-message.sh - Message other agents
- schedule_with_note.sh - Schedule check-ins

TO COMMUNICATE WITH OTHERS:
```bash
cd {workspace}
./.tools/send-claude-message.sh {session_name}:WINDOW_NUMBER "Your message"
```

TO READ MESSAGES FROM OTHERS:
```bash
tmux capture-pane -t {session_name}:WINDOW_NUMBER -p | tail -50
```

TO SEE ALL WINDOWS:
```bash
tmux list-windows -t {session_name}
```

IMPORTANT: Always work from your workspace directory for tool access.

---
ORIGINAL BRIEFING:
"""
        return context_injection + original_briefing
    
    def get_agent_context(self, session_name: str, agent_name: str) -> AgentContext:
        """
        Get or create the context for an agent.
        
        Args:
            session_name: The tmux session name
            agent_name: The agent's name
            
        Returns:
            AgentContext object with all necessary information
        """
        cache_key = f"{session_name}:{agent_name}"
        
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        # Create workspace
        workspace = self.create_agent_workspace(session_name, agent_name)
        
        # Build context object
        context = AgentContext(
            claude_md_path=str(workspace / '.context' / 'CLAUDE.md'),
            learnings_md_path=str(workspace / '.context' / 'LEARNINGS.md'),
            send_message_script=str(workspace / '.tools' / 'send-claude-message.sh'),
            schedule_script=str(workspace / '.tools' / 'schedule_with_note.sh'),
            tmux_commands=self.TMUX_COMMANDS,
            coordination_protocol=self._get_coordination_protocol(),
            workspace_path=str(workspace),
            available_tools=['send-claude-message.sh', 'schedule_with_note.sh'],
            tool_paths={
                'send_message': str(workspace / '.tools' / 'send-claude-message.sh'),
                'schedule': str(workspace / '.tools' / 'schedule_with_note.sh'),
            }
        )
        
        self.context_cache[cache_key] = context
        return context
    
    def cleanup_workspaces(self, session_name: Optional[str] = None):
        """
        Clean up agent workspaces.
        
        Args:
            session_name: If provided, only clean up workspaces for this session.
                         Otherwise, clean up all workspaces.
        """
        workspace_root = self.working_dir / '.ai-team-workspaces'
        
        if not workspace_root.exists():
            return
        
        if session_name:
            session_workspace = workspace_root / session_name
            if session_workspace.exists():
                shutil.rmtree(session_workspace)
                logger.info(f"Cleaned up workspaces for session {session_name}")
        else:
            shutil.rmtree(workspace_root)
            logger.info("Cleaned up all agent workspaces")
    
    def verify_context_integrity(self, session_name: str, agent_name: str) -> Tuple[bool, List[str]]:
        """
        Verify that an agent's context is complete and accessible.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        workspace = self.working_dir / '.ai-team-workspaces' / session_name / agent_name
        
        if not workspace.exists():
            issues.append(f"Workspace directory does not exist: {workspace}")
            return False, issues
        
        # Check essential files
        essential_checks = [
            (workspace / '.context' / 'CLAUDE.md', "CLAUDE.md missing"),
            (workspace / '.context' / 'LEARNINGS.md', "LEARNINGS.md missing"),
            (workspace / '.context' / 'manifest.json', "manifest.json missing"),
            (workspace / '.tools' / 'send-claude-message.sh', "send-claude-message.sh missing"),
        ]
        
        for path, error_msg in essential_checks:
            if not path.exists():
                issues.append(error_msg)
        
        # Check tool executability
        for tool in ['send-claude-message.sh', 'schedule_with_note.sh']:
            tool_path = workspace / '.tools' / tool
            if tool_path.exists() and not os.access(tool_path, os.X_OK):
                issues.append(f"{tool} is not executable")
        
        is_valid = len(issues) == 0
        return is_valid, issues