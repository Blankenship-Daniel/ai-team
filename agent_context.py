#!/usr/bin/env python3
"""
Agent Context Management - Ensures agents maintain their knowledge regardless of working directory
Solves the "context loss" problem when running from different repos
"""

import json
from pathlib import Path
from typing import Dict, Optional
from logging_config import setup_logging

logger = setup_logging(__name__)


class AgentContextManager:
    """Manages embedded context for agents to maintain knowledge across repos"""

    # Context version - INCREMENT when making breaking changes
    CONTEXT_VERSION = "2.0.0"

    # Version history for compatibility checking
    COMPATIBLE_VERSIONS = ["2.0.0", "1.9.0"]  # Versions that are compatible

    # Core knowledge that EVERY agent needs
    CORE_CONTEXT = """
## CRITICAL AGENT KNOWLEDGE

### Communication Protocol
- Use `tmux send-keys -t session:window "message"` to communicate
- Check other agents: `tmux capture-pane -t session:window -p | tail -20`
- Your session/window: Use `tmux display-message -p "#{session_name}:#{window_index}"`

### Git Discipline (MANDATORY)
1. **Commit every 30 minutes**: Prevent work loss
   ```bash
   git add -A && git commit -m "Progress: [what you did]"
   ```
2. **Before task switches**: ALWAYS commit
3. **Tag stable versions**: `git tag stable-[feature]-$(date +%Y%m%d)`

### Orchestration Commands
- Schedule check-in: `./schedule_with_note.sh 30 "Continue [task]"`
- Send message: `./send-claude-message.sh session:window "message"`
- Status update: Create STATUS.md in project root

### Error Recovery
- If tmux fails: Log error to ERROR.log
- If git conflicts: Create CONFLICT.md with details
- If blocked: Message orchestrator immediately
"""

    # Role-specific context templates
    ROLE_CONTEXTS = {
        "orchestrator": """
### Orchestrator Responsibilities
- Monitor all project managers
- Resolve cross-team dependencies
- Make architectural decisions
- Ensure quality standards
- Deploy new agents as needed

### Monitoring Commands
- View all sessions: `tmux ls`
- Check agent health: `for s in $(tmux ls -F "#{session_name}"); do echo "=== $s ==="; tmux capture-pane -t $s:0 -p | tail -5; done`
""",
        "project_manager": """
### Project Manager Responsibilities
- Coordinate team members
- Track task progress
- Ensure specifications are met
- Regular status reports to orchestrator
- Git branch management

### Team Coordination
- Assign tasks clearly with deadlines
- Check engineer progress every 30 min
- Escalate blockers to orchestrator
""",
        "developer": """
### Developer Responsibilities
- Implement features to spec
- Write tests for new code
- Document complex logic
- Follow project patterns
- Regular commits (30 min max)

### Development Workflow
1. Read specification carefully
2. Check existing patterns
3. Implement incrementally
4. Test each component
5. Commit working code frequently
""",
    }

    def __init__(self, install_dir: Optional[Path] = None):
        """Initialize with the tmux-orchestrator installation directory"""
        if install_dir:
            self.install_dir = Path(install_dir)
        else:
            # Try to find where we're installed
            self.install_dir = Path(__file__).parent

        self.context_cache = {}
        logger.info(f"AgentContextManager initialized with install_dir: {self.install_dir}")

    def load_external_context(self, filename: str) -> Optional[str]:
        """Load context from external files like CLAUDE.md"""
        possible_paths = [
            self.install_dir / "docs" / "developer" / filename,
            self.install_dir / filename,
            Path.cwd() / filename,
            Path.home() / ".tmux-orchestrator" / filename,
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    content = path.read_text()
                    logger.info(f"Loaded external context from {path}")
                    return content
                except Exception as e:
                    logger.error(f"Failed to read {path}: {e}")

        logger.warning(f"Could not find {filename} in any expected location")
        return None

    def build_agent_context(self, role: str, include_external: bool = True) -> str:
        """Build complete context for an agent based on role"""
        logger.info(f"Building context for role: {role}", extra={"context_version": self.CONTEXT_VERSION, "role": role})

        # Start with version header
        context_parts = [f"## CONTEXT VERSION: {self.CONTEXT_VERSION}\n", self.CORE_CONTEXT]

        # Add role-specific context
        if role.lower() in self.ROLE_CONTEXTS:
            context_parts.append(self.ROLE_CONTEXTS[role.lower()])

        # Try to include external CLAUDE.md if available
        if include_external:
            external = self.load_external_context("CLAUDE.md")
            if external:
                context_parts.append("\n## Extended Knowledge Base\n")
                context_parts.append(external)

        # Add working directory context
        context_parts.append("\n## Current Environment\n")
        context_parts.append(f"- Working Directory: {Path.cwd()}")
        context_parts.append(f"- Orchestrator Install: {self.install_dir}")
        context_parts.append("- Context Preserved: Yes (embedded)")

        full_context = "\n\n".join(context_parts)
        logger.info(
            f"Successfully built context for {role}",
            extra={
                "role": role,
                "context_size": len(full_context),
                "version": self.CONTEXT_VERSION,
                "external_included": include_external and bool(self.load_external_context("CLAUDE.md")),
            },
        )
        return full_context

    def inject_context_into_briefing(self, original_briefing: str, role: str) -> str:
        """Inject context into an agent's briefing"""
        try:
            logger.info(f"Starting context injection for {role}")

            context = self.build_agent_context(role)

            # Create enhanced briefing with embedded context and version
            enhanced_briefing = f"""{original_briefing}

---
## EMBEDDED OPERATIONAL CONTEXT
## VERSION: {self.CONTEXT_VERSION}
{context}
---

Remember: This context is embedded to ensure you maintain full operational knowledge regardless of working directory.

CONTEXT VERSION: {self.CONTEXT_VERSION} - If you see version mismatch errors, run: ./restore_context.sh"""

            logger.info(
                f"Context injection successful for {role}",
                extra={
                    "role": role,
                    "original_size": len(original_briefing),
                    "enhanced_size": len(enhanced_briefing),
                    "context_version": self.CONTEXT_VERSION,
                    "size_increase": len(enhanced_briefing) - len(original_briefing),
                },
            )
            return enhanced_briefing

        except Exception as e:
            logger.error(
                f"Context injection failed for {role}: {e}",
                extra={"role": role, "error": str(e), "context_version": self.CONTEXT_VERSION},
            )
            # Return original briefing with error notice
            return f"""{original_briefing}

⚠️ WARNING: Context injection failed. Error: {e}
You may be missing critical operational knowledge. Run: ./restore_context.sh"""

    def create_context_file(self, target_dir: Path = None) -> Path:
        """Create a .tmux-orchestrator-context file in target directory"""
        if target_dir is None:
            target_dir = Path.cwd()

        context_file = target_dir / ".tmux-orchestrator-context"

        context_data = {
            "context_version": self.CONTEXT_VERSION,
            "compatible_versions": self.COMPATIBLE_VERSIONS,
            "install_dir": str(self.install_dir),
            "core_context": self.CORE_CONTEXT,
            "generated_at": str(Path.cwd()),
            "timestamp": str(Path.cwd()),
            "note": "This file ensures agents maintain context. Do not commit to git.",
        }

        try:
            with open(context_file, "w") as f:
                json.dump(context_data, f, indent=2)
            logger.info(
                f"Created context file",
                extra={"path": str(context_file), "version": self.CONTEXT_VERSION, "size": context_file.stat().st_size},
            )
            return context_file
        except Exception as e:
            logger.error(f"Failed to create context file: {e}", extra={"path": str(context_file), "error": str(e)})
            raise

    @classmethod
    def load_context_file(cls, target_dir: Path = None) -> Optional[Dict]:
        """Load context from a .tmux-orchestrator-context file"""
        if target_dir is None:
            target_dir = Path.cwd()

        context_file = target_dir / ".tmux-orchestrator-context"

        if context_file.exists():
            try:
                with open(context_file, "r") as f:
                    data = json.load(f)

                # Version validation
                file_version = data.get("context_version", "1.0")
                if not cls.is_version_compatible(file_version):
                    logger.warning(
                        f"Context version mismatch",
                        extra={
                            "file_version": file_version,
                            "current_version": cls.CONTEXT_VERSION,
                            "compatible": cls.COMPATIBLE_VERSIONS,
                        },
                    )
                else:
                    logger.debug(
                        f"Context file loaded successfully", extra={"version": file_version, "path": str(context_file)}
                    )

                return data
            except Exception as e:
                logger.error(f"Failed to load context file: {e}", extra={"path": str(context_file), "error": str(e)})
        else:
            logger.debug(f"No context file found at {context_file}")

        return None

    @classmethod
    def is_version_compatible(cls, version: str) -> bool:
        """Check if a context version is compatible with current version"""
        return version in cls.COMPATIBLE_VERSIONS

    @classmethod
    def validate_agent_context(cls, agent_response: str) -> tuple[bool, str]:
        """Validate that an agent has the correct context version"""
        # Look for version string in agent response
        import re

        version_pattern = r"CONTEXT VERSION:\s*([\d\.]+)"
        match = re.search(version_pattern, agent_response)

        if not match:
            logger.warning("No context version found in agent response")
            return False, "No context version found"

        agent_version = match.group(1)
        if not cls.is_version_compatible(agent_version):
            logger.error(
                f"Agent context version mismatch",
                extra={
                    "agent_version": agent_version,
                    "expected": cls.CONTEXT_VERSION,
                    "compatible": cls.COMPATIBLE_VERSIONS,
                },
            )
            return False, f"Version {agent_version} not compatible with {cls.CONTEXT_VERSION}"

        logger.debug(f"Agent context version validated: {agent_version}")
        return True, agent_version

    def create_fallback_script(self) -> Path:
        """Create a fallback script agents can run to restore context"""
        script_path = Path.cwd() / "restore_context.sh"

        script_content = f"""#!/bin/bash
# Tmux Orchestrator Context Restoration Script
# Run this if you lose context or forget communication protocols

echo "=== RESTORING AGENT CONTEXT ==="

# Core communication knowledge
cat << 'EOF'
{self.CORE_CONTEXT}
EOF

# Version information
echo "CONTEXT VERSION: {self.CONTEXT_VERSION}"
echo "Compatible versions: {', '.join(self.COMPATIBLE_VERSIONS)}"
echo ""

# Check if we can find the orchestrator installation
if [ -d "{self.install_dir}" ]; then
    echo "✓ Found orchestrator at {self.install_dir}"
    if [ -f "{self.install_dir}/docs/developer/CLAUDE.md" ]; then
        echo "✓ Extended context available"
    fi
else
    echo "⚠ Orchestrator installation not found at expected location"
    echo "  You may need to rely on embedded context only"
fi

# Check for context file
if [ -f ".tmux-orchestrator-context" ]; then
    echo "✓ Context file found in current directory"
fi

echo "=== CONTEXT RESTORED ==="
echo "You can now continue with your tasks using the above knowledge."
echo "Your context version is: {self.CONTEXT_VERSION}"
"""

        try:
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            logger.info(
                f"Created fallback script",
                extra={"path": str(script_path), "version": self.CONTEXT_VERSION, "size": script_path.stat().st_size},
            )
            return script_path
        except Exception as e:
            logger.error(f"Failed to create fallback script: {e}", extra={"path": str(script_path), "error": str(e)})
            raise

    def get_context_health_status(self) -> Dict:
        """Get comprehensive health status of context system"""
        health = {
            "version": self.CONTEXT_VERSION,
            "compatible_versions": self.COMPATIBLE_VERSIONS,
            "install_dir": str(self.install_dir),
            "install_dir_exists": self.install_dir.exists(),
            "claude_md_available": False,
            "context_file_exists": False,
            "recovery_script_exists": False,
            "issues": [],
        }

        # Check for CLAUDE.md
        claude_md = self.load_external_context("CLAUDE.md")
        if claude_md:
            health["claude_md_available"] = True
            logger.debug("CLAUDE.md is available")
        else:
            health["issues"].append("CLAUDE.md not found - using embedded context only")

        # Check for context file
        context_file = Path.cwd() / ".tmux-orchestrator-context"
        if context_file.exists():
            health["context_file_exists"] = True
            # Validate version
            data = self.load_context_file()
            if data:
                file_version = data.get("context_version", "unknown")
                if not self.is_version_compatible(file_version):
                    health["issues"].append(f"Context file version mismatch: {file_version}")
        else:
            health["issues"].append("No context file in working directory")

        # Check for recovery script
        recovery_script = Path.cwd() / "restore_context.sh"
        if recovery_script.exists():
            health["recovery_script_exists"] = True
        else:
            health["issues"].append("No recovery script available")

        # Overall status
        health["status"] = "healthy" if len(health["issues"]) == 0 else "degraded"

        logger.info("Context health check completed", extra=health)
        return health

    def monitor_agent_context(self, session_name: str, agent_name: str) -> tuple[bool, str]:
        """Monitor if an agent has proper context"""
        try:
            # This would normally check the agent's output for version strings
            # For now, return a basic check
            logger.info(f"Monitoring context for {agent_name} in {session_name}")

            # In a real implementation, this would:
            # 1. Capture recent agent output
            # 2. Look for version strings
            # 3. Validate against expected version

            return True, f"Agent {agent_name} context monitoring not fully implemented"

        except Exception as e:
            logger.error(
                f"Failed to monitor agent context: {e}",
                extra={"session": session_name, "agent": agent_name, "error": str(e)},
            )
            return False, str(e)
