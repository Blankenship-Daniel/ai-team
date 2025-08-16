#!/usr/bin/env python3
"""
Unified Context Manager - Combines embedded context with workspace management
Architecturally sound solution for agent context preservation across directories
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass 
class AgentWorkspace:
    """Represents an agent's workspace with tools and context"""
    path: Path
    tools_dir: Path
    context_file: Path
    status_file: Path
    has_tools: bool
    symlinks: Dict[str, Path]


class UnifiedContextManager:
    """
    Unified context management combining Sam's embedded approach with Alex's workspace creation.
    
    Architecture:
    1. Embedded context in briefings (primary - always works)
    2. Local workspace with tools (secondary - when needed)
    3. Fallback scripts (tertiary - recovery mechanism)
    """
    
    # Core embedded context from Sam's implementation
    CORE_CONTEXT = """
## CRITICAL AGENT KNOWLEDGE

### Communication Protocol
- Use `tmux send-keys -t session:window "message"` to communicate
- Check other agents: `tmux capture-pane -t session:window -p | tail -20`
- Your session/window: Use `tmux display-message -p "#{session_name}:#{window_index}"`

### Tool Creation (If Not Available)
If send-claude-message.sh is not available, create it:
```bash
cat > send-claude-message.sh << 'EOF'
#!/bin/bash
WINDOW="$1"
shift
MESSAGE="$*"
tmux send-keys -t "$WINDOW" "$MESSAGE"
sleep 1
tmux send-keys -t "$WINDOW" Enter
echo "Message sent to $WINDOW: $MESSAGE"
EOF
chmod +x send-claude-message.sh
```

### Git Discipline (MANDATORY)
1. **Commit every 30 minutes**: `git add -A && git commit -m "Progress: [what you did]"`
2. **Before task switches**: ALWAYS commit
3. **Tag stable versions**: `git tag stable-[feature]-$(date +%Y%m%d)`

### Error Recovery
- If tmux fails: Log error to ERROR.log
- If git conflicts: Create CONFLICT.md with details
- If blocked: Message orchestrator immediately
"""
    
    # Role-specific contexts
    ROLE_CONTEXTS = {
        "orchestrator": """
### Orchestrator Responsibilities
- Monitor all project managers
- Coordinate cross-project work
- Resolve conflicts between agents
- Schedule system-wide check-ins
""",
        "senior_software_engineer": """
### Alex (Perfectionist Architect) Guidelines
- Enforce SOLID principles
- Require comprehensive testing
- Document all architectural decisions
- No shortcuts without explicit justification
""",
        "full_stack_developer": """
### Morgan (Pragmatic Shipper) Guidelines
- Focus on MVP and iteration
- Document trade-offs explicitly
- Ship working code frequently
- Balance speed with maintainability
""",
        "code_quality_engineer": """
### Sam (Code Custodian) Guidelines
- Track technical debt in DEBT.md
- Run linters and formatters regularly
- Update dependencies systematically
- Clean as you go
"""
    }
    
    def __init__(self, install_dir: Optional[Path] = None):
        """
        Initialize the unified context manager.
        
        Args:
            install_dir: Path to Tmux-Orchestrator installation
        """
        self.install_dir = self._find_install_dir(install_dir)
        self.working_dir = Path.cwd()
        self.workspaces: Dict[str, AgentWorkspace] = {}
        
        logger.info(f"UnifiedContextManager initialized", extra={
            'install_dir': str(self.install_dir),
            'working_dir': str(self.working_dir)
        })
    
    def _find_install_dir(self, provided_path: Optional[Path] = None) -> Path:
        """Find Tmux-Orchestrator installation directory"""
        if provided_path and provided_path.exists():
            return provided_path.resolve()
        
        # Check current file location
        current = Path(__file__).parent
        if (current / 'create_ai_team.py').exists():
            return current.resolve()
        
        # Check environment variable
        env_path = os.environ.get('TMUX_ORCHESTRATOR_HOME')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path.resolve()
        
        # Default to current if all else fails
        logger.warning("Could not find install dir, using current directory")
        return current.resolve()
    
    def inject_context_into_briefing(self, original_briefing: str, role: str) -> str:
        """
        Inject context into agent briefing using embedded approach.
        
        This is the PRIMARY context delivery mechanism - always works regardless
        of directory or tool availability.
        """
        logger.info(f"Injecting context for role: {role}")
        
        # Build complete context
        context_parts = [self.CORE_CONTEXT]
        
        # Add role-specific context
        role_key = role.lower().replace(" ", "_").replace("-", "_")
        if role_key in self.ROLE_CONTEXTS:
            context_parts.append(self.ROLE_CONTEXTS[role_key])
        
        # Add environment information
        env_context = f"""
### Current Environment
- Working Directory: {self.working_dir}
- Orchestrator Installation: {self.install_dir}
- Tools Available: Check with `which send-claude-message.sh`
- If tools missing: Use the creation script above
"""
        context_parts.append(env_context)
        
        # Combine everything
        full_context = "\n".join(context_parts)
        
        enhanced_briefing = f"""{original_briefing}

---
## EMBEDDED OPERATIONAL CONTEXT
{full_context}
---

IMPORTANT: This context is embedded to ensure you maintain operational knowledge.
If you lose context, create the tools using the scripts provided above."""
        
        logger.debug(f"Enhanced briefing: {len(enhanced_briefing)} chars (from {len(original_briefing)})")
        return enhanced_briefing
    
    def ensure_workspace(self, session_name: str, agent_name: str) -> AgentWorkspace:
        """
        Ensure agent has a workspace with tools (SECONDARY mechanism).
        
        Creates .ai-team-workspace/<session>/<agent>/ structure with:
        - tools/ directory with communication scripts
        - context.json with environment info
        """
        workspace_key = f"{session_name}:{agent_name}"
        
        # Return cached workspace if exists
        if workspace_key in self.workspaces:
            return self.workspaces[workspace_key]
        
        # Create workspace structure
        workspace_path = self.working_dir / '.ai-team-workspace' / session_name / agent_name
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        tools_dir = workspace_path / 'tools'
        tools_dir.mkdir(exist_ok=True)
        
        # Copy essential tools
        has_tools = self._copy_tools(tools_dir)
        
        # Create context file
        context_file = workspace_path / 'context.json'
        self._create_context_file(context_file, session_name, agent_name)
        
        # Create status file
        status_file = workspace_path / 'STATUS.md'
        self._create_status_file(status_file, agent_name)
        
        # Create symlinks for tools in working directory
        symlinks = self._create_tool_symlinks()
        
        workspace = AgentWorkspace(
            path=workspace_path,
            tools_dir=tools_dir,
            context_file=context_file,
            status_file=status_file,
            has_tools=has_tools,
            symlinks=symlinks
        )
        
        self.workspaces[workspace_key] = workspace
        logger.info(f"Created workspace for {agent_name} at {workspace_path}")
        
        return workspace
    
    def _copy_tools(self, tools_dir: Path) -> bool:
        """Copy essential tools to workspace"""
        tools_to_copy = ['send-claude-message.sh', 'schedule_with_note.sh', 'context-status.sh']
        docs_to_copy = ['ORCHESTRATOR_GUIDE.md']
        all_copied = True
        
        # Copy executable tools
        for tool in tools_to_copy:
            source = self.install_dir / tool
            if source.exists():
                dest = tools_dir / tool
                try:
                    shutil.copy2(source, dest)
                    os.chmod(dest, 0o755)
                    logger.debug(f"Copied {tool} to workspace")
                except Exception as e:
                    logger.error(f"Failed to copy {tool}: {e}")
                    all_copied = False
            else:
                logger.warning(f"Tool not found: {tool}")
                all_copied = False
        
        # Copy documentation files
        for doc in docs_to_copy:
            source = self.install_dir / doc
            if source.exists():
                dest = tools_dir / doc
                try:
                    shutil.copy2(source, dest)
                    os.chmod(dest, 0o644)
                    logger.debug(f"Copied {doc} to workspace")
                except Exception as e:
                    logger.error(f"Failed to copy {doc}: {e}")
                    all_copied = False
            else:
                logger.warning(f"Documentation not found: {doc}")
                # Not critical if docs are missing
                pass
        
        return all_copied
    
    def _create_context_file(self, context_file: Path, session_name: str, agent_name: str):
        """Create JSON context file in workspace"""
        context_data = {
            "version": "2.0",
            "session": session_name,
            "agent": agent_name,
            "install_dir": str(self.install_dir),
            "working_dir": str(self.working_dir),
            "core_context": self.CORE_CONTEXT,
            "timestamp": str(Path.cwd()),
            "note": "Workspace context for agent operation"
        }
        
        try:
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2)
            logger.debug(f"Created context file at {context_file}")
        except Exception as e:
            logger.error(f"Failed to create context file: {e}")
    
    def _create_status_file(self, status_file: Path, agent_name: str):
        """Create initial status file for agent"""
        status_content = f"""# Agent Status: {agent_name}

## Current Status
- **Created**: {Path.cwd()}
- **Working Directory**: {self.working_dir}
- **Context Version**: 2.0

## Tasks
- [ ] Initialize workspace
- [ ] Verify tools available
- [ ] Establish communication with orchestrator

## Notes
This file tracks agent status and progress.
"""
        try:
            status_file.write_text(status_content)
            logger.debug(f"Created status file at {status_file}")
        except Exception as e:
            logger.error(f"Failed to create status file: {e}")
    
    def _create_tool_symlinks(self) -> Dict[str, Path]:
        """Create symlinks to essential tools in working directory"""
        symlinks = {}
        tools_to_link = ['send-claude-message.sh', 'schedule_with_note.sh']
        
        for tool in tools_to_link:
            source = self.install_dir / tool
            link = self.working_dir / tool
            
            if source.exists() and not link.exists():
                try:
                    link.symlink_to(source)
                    symlinks[tool] = source
                    logger.debug(f"Created symlink: {link} -> {source}")
                except Exception as e:
                    logger.warning(f"Could not create symlink for {tool}: {e}")
            elif link.exists():
                symlinks[tool] = link.resolve()
                logger.debug(f"Tool already exists: {tool}")
        
        return symlinks
    
    def create_recovery_script(self) -> Path:
        """
        Create recovery script (TERTIARY mechanism).
        
        This script can restore context if agents lose their way.
        """
        script_path = self.working_dir / 'restore_agent_context.sh'
        
        script_content = f"""#!/bin/bash
# Agent Context Recovery Script
# Run this if you lose context or tools

echo "=== RESTORING AGENT CONTEXT ==="

# 1. Show core knowledge
cat << 'EOF'
{self.CORE_CONTEXT}
EOF

# 2. Create missing tools
if [ ! -f "./send-claude-message.sh" ]; then
    echo "Creating send-claude-message.sh..."
    cat > send-claude-message.sh << 'TOOL'
#!/bin/bash
WINDOW="$1"
shift
MESSAGE="$*"
tmux send-keys -t "$WINDOW" "$MESSAGE"
sleep 1
tmux send-keys -t "$WINDOW" Enter
echo "Message sent to $WINDOW: $MESSAGE"
TOOL
    chmod +x send-claude-message.sh
    echo "✓ Created send-claude-message.sh"
fi

# 3. Check environment
echo ""
echo "Environment Check:"
echo "- Working Directory: $(pwd)"
echo "- Tmux Session: $(tmux display-message -p '#{{session_name}}')"
echo "- Window/Pane: $(tmux display-message -p '#{{window_index}}.#{{pane_index}}')"

echo ""
echo "=== CONTEXT RESTORED ==="
echo "You can now continue with your tasks."
"""
        
        try:
            script_path.write_text(script_content)
            os.chmod(script_path, 0o755)
            logger.info(f"Created recovery script at {script_path}")
            return script_path
        except Exception as e:
            logger.error(f"Failed to create recovery script: {e}")
            raise
    
    def verify_agent_readiness(self, session_name: str, agent_name: str) -> Tuple[bool, list]:
        """
        Verify an agent has everything needed to operate.
        
        Returns:
            Tuple of (is_ready, list_of_issues)
        """
        issues = []
        
        # Check workspace
        workspace_key = f"{session_name}:{agent_name}"
        if workspace_key not in self.workspaces:
            issues.append("No workspace created")
        else:
            workspace = self.workspaces[workspace_key]
            if not workspace.has_tools:
                issues.append("Tools not properly copied to workspace")
            if not workspace.context_file.exists():
                issues.append("Context file missing")
        
        # Check recovery script
        recovery_script = self.working_dir / 'restore_agent_context.sh'
        if not recovery_script.exists():
            issues.append("Recovery script not created")
        
        is_ready = len(issues) == 0
        return is_ready, issues
    
    def cleanup_workspaces(self, session_name: Optional[str] = None):
        """Clean up agent workspaces"""
        workspace_root = self.working_dir / '.ai-team-workspace'
        
        if not workspace_root.exists():
            return
        
        if session_name:
            session_workspace = workspace_root / session_name
            if session_workspace.exists():
                shutil.rmtree(session_workspace)
                logger.info(f"Cleaned up workspaces for session {session_name}")
                # Remove from cache
                self.workspaces = {k: v for k, v in self.workspaces.items() 
                                 if not k.startswith(f"{session_name}:")}
        else:
            shutil.rmtree(workspace_root)
            logger.info("Cleaned up all agent workspaces")
            self.workspaces.clear()