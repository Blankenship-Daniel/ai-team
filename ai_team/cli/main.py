#!/usr/bin/env python3
"""
AI Team CLI - Creates an orchestrator and three opinionated AI agents
Based on the Tmux Orchestrator framework
"""

import argparse
import subprocess
import time
import json
import os
import sys
import shlex
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from ai_team.utils.tmux_utils import TmuxOrchestrator
from ai_team.utils.security_validator import SecurityValidator
from ai_team.utils.logging_config import setup_logging, log_subprocess_call
from ai_team.core.unified_context_manager import UnifiedContextManager

# Set up logging for this module
logger = setup_logging(__name__)


@dataclass
class AgentProfile:
    name: str
    personality: str
    role: str
    briefing: str
    window_name: str


class AITeamOrchestrator:
    def __init__(self, non_interactive=False, observe_only=False, no_git_write=False, initiative=None):
        self.tmux = TmuxOrchestrator()
        self.session_name = "ai-team"
        self.agents: List[AgentProfile] = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_dir = os.getcwd()  # Capture the directory where user invoked the command
        self.context_manager = UnifiedContextManager(install_dir=Path(self.script_dir))
        self.non_interactive = non_interactive
        self.observe_only = observe_only
        self.no_git_write = no_git_write
        self.initiative = initiative
        logger.info(
            "AITeamOrchestrator initialized",
            extra={
                "script_dir": self.script_dir,
                "working_dir": self.working_dir,
                "non_interactive": non_interactive,
                "observe_only": observe_only,
                "initiative": initiative,
            },
        )

    def create_agent_profiles(self) -> List[AgentProfile]:
        """Create three strongly opinionated AI agent profiles"""

        # Add initiative context to briefings
        initiative_context = ""
        if self.initiative:
            initiative_context = f"""

TEAM INITIATIVE:
You and your team have been assigned to work on the following initiative:
"{self.initiative}"

Focus all your efforts on this specific task. Coordinate with the other agents to deliver this initiative successfully.
"""

        agent1 = AgentProfile(
            name="Alex-Purist",
            personality="PERFECTIONIST_ARCHITECT",
            role="Senior Software Engineer",
            window_name="Agent-Alex",
            briefing=f"""You are Alex, a senior software engineer with 15+ years of experience. You are:

PERSONALITY TRAITS:
- Extremely detail-oriented and perfectionist
- Strong believer in clean architecture and SOLID principles
- Will argue for proper design patterns even if it takes longer
- Highly critical of technical debt and shortcuts
- Values type safety, comprehensive testing, and documentation
- Prefers established, battle-tested technologies over trendy ones

COMMUNICATION STYLE:
- Direct and technical, no sugar-coating
- Will push back on bad ideas with solid reasoning
- Provides detailed technical explanations
- Not afraid to say "that's wrong" when it is
- Focuses on long-term maintainability over quick fixes

CORE BELIEFS:
- "Code is read more than it's written"
- "If it's not tested, it's broken"
- "Premature optimization is evil, but so is premature pessimization"
- "Documentation is not optional"
- "Technical debt always comes due with interest"

When communicating with the other agents or orchestrator, be firm in your convictions but professional. Challenge ideas that compromise quality.

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- You can read/write files and run commands
- The orchestrator is in pane 0.0
- You are in pane 0.1
- Morgan is in pane 0.2, Sam is in pane 0.3
- Always use absolute paths when needed{initiative_context}""",
        )

        agent2 = AgentProfile(
            name="Morgan-Pragmatist",
            personality="SHIP_IT_ENGINEER",
            role="Full-Stack Developer",
            window_name="Agent-Morgan",
            briefing=f"""You are Morgan, a full-stack developer focused on shipping products. You are:

PERSONALITY TRAITS:
- Results-oriented and deadline-driven
- Believes in iterative development and MVP approach
- Willing to take calculated technical shortcuts for business value
- Prefers modern tools and frameworks that increase velocity
- Values working software over perfect software
- Comfortable with refactoring as you learn

COMMUNICATION STYLE:
- Practical and business-focused
- Will challenge over-engineering with ROI arguments
- Provides quick, actionable solutions
- Not afraid to say "good enough for now" when appropriate
- Focuses on user value and time-to-market

CORE BELIEFS:
- "Perfect is the enemy of good"
- "Ship early, ship often, iterate based on feedback"
- "User feedback trumps theoretical concerns"
- "Technical debt is manageable if you're intentional about it"
- "The best code is code that solves real problems for users"

When communicating with the other agents or orchestrator, advocate for pragmatic solutions that deliver value quickly while acknowledging trade-offs.

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- You can read/write files and run commands
- The orchestrator is in pane 0.0
- Alex is in pane 0.1
- You are in pane 0.2, Sam is in pane 0.3
- Always use absolute paths when needed{initiative_context}""",
        )

        agent3 = AgentProfile(
            name="Sam-Janitor",
            personality="CODE_CUSTODIAN",
            role="Code Quality Engineer",
            window_name="Agent-Sam",
            briefing=f"""You are Sam, a code quality engineer specializing in technical debt management and code hygiene. You are:

PERSONALITY TRAITS:
- Obsessed with code cleanliness and consistency
- Expert at identifying and prioritizing technical debt
- Passionate about refactoring and modernization
- Believes in the "Boy Scout Rule" - leave code cleaner than you found it
- Values automated tooling for linting, formatting, and analysis
- Enjoys simplifying complex code and removing duplications

COMMUNICATION STYLE:
- Methodical and systematic in approach
- Provides clear prioritization of cleanup tasks
- Focuses on measurable improvements (cyclomatic complexity, test coverage, etc.)
- Advocates for continuous small improvements over big rewrites
- Not afraid to tackle the "boring" but necessary work

CORE BELIEFS:
- "Clean code is a feature, not a nice-to-have"
- "Technical debt compounds faster than financial debt"
- "Consistency beats perfection"
- "Automation prevents regression"
- "Small, continuous improvements lead to big wins"
- "Every TODO comment should have an expiration date"

SPECIAL FOCUS AREAS:
- Dead code elimination
- Dependency updates and security patches
- Test coverage improvements
- Documentation gaps
- Code duplication removal
- Performance bottlenecks from poor practices
- Deprecated API migrations
- Build and CI/CD pipeline optimization

When communicating with other agents or orchestrator, advocate for allocating time to cleanup and maintenance. Balance urgency with importance, and help the team understand the long-term cost of ignoring technical debt.

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- You can read/write files and run commands
- The orchestrator is in pane 0.0
- Alex is in pane 0.1, Morgan is in pane 0.2
- You are in pane 0.3
- Always use absolute paths when needed{initiative_context}""",
        )

        return [agent1, agent2, agent3]

    def session_exists(self, session_name: str) -> bool:
        """Check if a tmux session already exists"""
        # Validate session name first
        valid, error = SecurityValidator.validate_session_name(session_name)
        if not valid:
            logger.error(f"Invalid session name: {error}")
            raise ValueError(f"Invalid session name: {error}")

        logger.debug(f"Checking if session '{session_name}' exists")
        try:
            cmd = ["tmux", "has-session", "-t", session_name]
            result = subprocess.run(cmd, check=True, capture_output=True)
            log_subprocess_call(logger, cmd, result)
            logger.debug(f"Session '{session_name}' exists")
            return True
        except subprocess.CalledProcessError as e:
            # This is expected behavior when session doesn't exist - log as debug, not error
            logger.debug(f"Session '{session_name}' does not exist (tmux has-session returned {e.returncode})")
            return False

    def create_tmux_session(self) -> bool:
        """Create the main tmux session for the AI team"""
        try:
            # Validate session name
            valid, error = SecurityValidator.validate_session_name(self.session_name)
            if not valid:
                logger.error(f"Invalid session name: {error}")
                return False

            if self.session_exists(self.session_name):
                logger.warning(f"Session '{self.session_name}' already exists. Killing it first...")
                cmd = ["tmux", "kill-session", "-t", self.session_name]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

            # Create new session with orchestrator
            cmd = ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "Orchestrator", "-c", self.working_dir]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            log_subprocess_call(logger, cmd, result)

            logger.info(f"Created session '{self.session_name}' with orchestrator window")
            logger.info(f"Created session '{self.session_name}' with orchestrator window")
            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to create tmux session: {e}")
            logger.error(f"Error creating tmux session: {e}")
            return False

    def create_agent_panes(self) -> bool:
        """Create panes for each AI agent in a split layout"""
        try:
            # Split the main window horizontally to create top and bottom sections
            # Top: Orchestrator, Bottom: Three agents side by side
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0", "-v", "-p", "60", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created horizontal split (Orchestrator top, agents bottom)")

            # Split the bottom pane vertically to create first two agent panes
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0.1", "-h", "-p", "66", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created first vertical split for agent panes")

            # Split again to create third agent pane
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0.2", "-h", "-p", "50", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created second vertical split for third agent pane")

            # Set pane titles
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.0", "-T", "Orchestrator"], check=True)

            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.1", "-T", "Alex-Purist"], check=True)

            subprocess.run(
                ["tmux", "select-pane", "-t", f"{self.session_name}:0.2", "-T", "Morgan-Pragmatist"], check=True
            )

            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.3", "-T", "Sam-Janitor"], check=True)

            logger.info("Set pane titles")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating agent panes: {e}")
            return False

    def start_claude_agents(self) -> bool:
        """Start Claude in each agent pane"""
        try:
            # Pane mapping: 0.0 = Orchestrator, 0.1 = Alex, 0.2 = Morgan, 0.3 = Sam
            agent_panes = {
                "Alex-Purist": f"{self.session_name}:0.1",
                "Morgan-Pragmatist": f"{self.session_name}:0.2",
                "Sam-Janitor": f"{self.session_name}:0.3",
            }

            for agent in self.agents:
                pane_target = agent_panes.get(agent.name)
                if not pane_target:
                    logger.error(f"Could not find pane for {agent.name}")
                    continue

                # Validate pane target before sending commands
                valid, error = SecurityValidator.validate_pane_target(pane_target)
                if not valid:
                    logger.error(f"Invalid pane target {pane_target}: {error}")
                    continue

                # Start Claude in the pane with appropriate flags
                # IMPORTANT: Use --permission-mode bypassPermissions to prevent agents getting stuck on prompts
                cmd = ["tmux", "send-keys", "-t", pane_target, "claude --permission-mode bypassPermissions", "Enter"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

                logger.info(f"Started Claude for {agent.name} in pane {pane_target}")
                logger.info(f"Started Claude for {agent.name} in pane {pane_target}")

                # Wait for Claude to start (reduced delay in non-interactive mode)
                delay = 1 if self.non_interactive else 3
                logger.debug(f"Waiting {delay} seconds for Claude to start in {pane_target}")
                time.sleep(delay)

            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to start Claude agents: {e}")
            logger.error(f"Error starting Claude agents: {e}")
            return False

    def brief_agents(self) -> bool:
        """Send briefing messages to each agent"""
        try:
            # Try to find send-claude-message.sh in the same directory, or in PATH
            send_script = os.path.join(self.script_dir, "send-claude-message.sh")
            if not os.path.exists(send_script):
                # Look for it in PATH (for global installation)
                import shutil

                send_script_path = shutil.which("send-claude-message.sh")
                if send_script_path:
                    send_script = send_script_path
                else:
                    logger.error("send-claude-message.sh not found in script directory or PATH")
                    return False

            # Pane mapping: 0.0 = Orchestrator, 0.1 = Alex, 0.2 = Morgan, 0.3 = Sam
            agent_panes = {
                "Alex-Purist": f"{self.session_name}:0.1",
                "Morgan-Pragmatist": f"{self.session_name}:0.2",
                "Sam-Janitor": f"{self.session_name}:0.3",
            }

            for agent in self.agents:
                pane_target = agent_panes.get(agent.name)
                if not pane_target:
                    logger.error(f"Could not find pane for {agent.name}")
                    continue

                # Validate pane target and sanitize briefing
                valid, error = SecurityValidator.validate_pane_target(pane_target)
                if not valid:
                    logger.error(f"Invalid pane target {pane_target}: {error}")
                    continue

                # Enhance briefing with embedded context and ensure workspace
                workspace = self.context_manager.ensure_workspace(self.session_name, agent.name)

                # Add observe-only instruction if flag is set
                briefing_to_use = agent.briefing
                if self.observe_only:
                    observe_instruction = (
                        "\n\n🔍 OBSERVE-ONLY MODE ACTIVE:\n"
                        "- Please introduce yourself and your capabilities\n"
                        "- DO NOT start any work or analysis\n"
                        "- Wait for explicit instructions from the orchestrator\n"
                        "- You may familiarize yourself with the workspace but don't make changes"
                    )
                    briefing_to_use = agent.briefing + observe_instruction

                # Add no-git-write restriction if flag is set
                if self.no_git_write:
                    git_restriction = (
                        "\n\n🚫 GIT WRITE OPERATIONS DISABLED:\n"
                        "- You are PROHIBITED from performing ANY git write operations\n"
                        "- FORBIDDEN commands include: git add, git commit, git push, git merge, git rebase, git reset, git checkout -b, git branch, git tag, git pull (with merge), git cherry-pick, git stash push, git stash pop\n"
                        "- You MAY ONLY use read-only git commands like: git status, git diff, git log, git show, git blame, git branch -l, git remote -v, git config -l\n"
                        "- If you need to suggest changes, describe them in text but DO NOT execute any git write commands\n"
                        "- If asked to commit changes, politely explain that git write operations are disabled\n"
                        "- You can create and modify files normally, just no git commits or similar operations"
                    )
                    briefing_to_use = briefing_to_use + git_restriction

                enhanced_briefing = self.context_manager.inject_context_into_briefing(
                    briefing_to_use, agent.role.lower().replace(" ", "_")
                )
                logger.debug(f"Agent {agent.name} workspace: {workspace.path}")

                # Send the briefing with proper escaping
                sanitized_briefing = SecurityValidator.sanitize_message(enhanced_briefing)
                cmd = [send_script, pane_target, sanitized_briefing]
                logger.debug(
                    f"Briefing {agent.name} with {len(sanitized_briefing)} chars (enhanced from {len(agent.briefing)})"
                )
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd[:2] + ["<briefing_text>"], result)  # Don't log full briefing

                logger.info(f"Briefed {agent.name} in pane {pane_target}")
                logger.info(f"Briefed {agent.name} in pane {pane_target}")
                # Reduced delay in non-interactive mode
                delay = 0.5 if self.non_interactive else 2
                time.sleep(delay)

            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd[:2] + ["<briefing_text>"] if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to brief agents: {e}")
            logger.error(f"Error briefing agents: {e}")
            return False

    def setup_orchestrator(self) -> bool:
        """Brief the orchestrator about its role"""
        try:
            # Try to find send-claude-message.sh in the same directory, or in PATH
            send_script = os.path.join(self.script_dir, "send-claude-message.sh")
            if not os.path.exists(send_script):
                # Look for it in PATH (for global installation)
                import shutil

                send_script_path = shutil.which("send-claude-message.sh")
                if send_script_path:
                    send_script = send_script_path
                else:
                    logger.error("send-claude-message.sh not found in script directory or PATH")
                    return False

            # Add initiative to orchestrator briefing
            initiative_instructions = ""
            if self.initiative:
                initiative_instructions = f"""

🎯 TEAM INITIATIVE:
Your team has been assigned to work on the following initiative:
"{self.initiative}"

YOUR RESPONSIBILITIES:
1. Ensure all team members understand and focus on this initiative
2. Break down the initiative into tasks appropriate for each agent's strengths
3. Coordinate the team's efforts to deliver this specific goal
4. Keep discussions and work focused on completing this initiative
5. Help resolve any disagreements about approach while staying aligned with the initiative
"""

            orchestrator_briefing = f"""You are the Orchestrator for a team of three AI software engineers:

1. **Alex (Left Pane)** - The Perfectionist Architect
   - Focuses on clean code, proper architecture, and long-term maintainability
   - Will push for best practices and comprehensive testing
   - Resistant to shortcuts and technical debt

2. **Morgan (Middle Pane)** - The Pragmatic Shipper
   - Focuses on delivering working software quickly
   - Advocates for MVP approach and iterative development
   - Willing to take calculated shortcuts for business value

3. **Sam (Right Pane)** - The Code Custodian
   - Specializes in technical debt management and code hygiene
   - Expert at refactoring, cleanup, and modernization
   - Advocates for continuous small improvements and automation

YOUR ROLE:
- Facilitate productive discussions between Alex, Morgan, and Sam
- Help them find middle ground when they disagree
- Assign tasks and coordinate their work
- Balance feature development with technical debt reduction
- Make final technical decisions when needed
- Keep the team focused on objectives

PANE LAYOUT:
┌──────────────────────────────────────────┐
│             Orchestrator                 │ <- You are here (pane 0.0)
├────────────┬──────────────┬──────────────┤
│    Alex    │    Morgan    │     Sam      │
│ (pane 0.1) │  (pane 0.2)  │  (pane 0.3)  │
└────────────┴──────────────┴──────────────┘

COMMUNICATION PROTOCOLS:
- Use send-claude-message.sh to message agents (available in PATH)
- Example: send-claude-message.sh {self.session_name}:0.1 "Alex, what's your take on this?"
- Example: send-claude-message.sh {self.session_name}:0.2 "Morgan, how would you approach this?"
- Example: send-claude-message.sh {self.session_name}:0.3 "Sam, what technical debt do you see here?"
- Check agent progress: tmux capture-pane -t {self.session_name}:0.1 -p | tail -20

CRITICAL CONTEXT:
- Working directory: {self.working_dir}
- You can read files with: cat <filename>
- You can write files with: echo "content" > filename
- You can run commands with: <command>
- Always use absolute paths when accessing files outside the current directory

PANE NAVIGATION:
- Use Ctrl+B, then arrow keys to move between panes
- All agents are visible simultaneously in the split view

The agents are in these panes:
- Alex is in: {self.session_name}:0.1 (left)
- Morgan is in: {self.session_name}:0.2 (middle)
- Sam is in: {self.session_name}:0.3 (right)

Start by introducing yourself to all three agents and asking them to introduce themselves to each other.{initiative_instructions}"""

            # Add observe-only instructions to orchestrator if flag is set
            if self.observe_only:
                orchestrator_briefing += """

🔍 OBSERVE-ONLY MODE ACTIVE:
- All agents have been instructed to only introduce themselves
- They will NOT start any work until you give them explicit instructions
- This prevents agents from immediately diving into random tasks
- You should coordinate what work needs to be done before agents begin"""

            # Add no-git-write instructions to orchestrator if flag is set
            if self.no_git_write:
                orchestrator_briefing += """

🚫 GIT WRITE OPERATIONS DISABLED FOR ALL AGENTS:
- All agents (Alex, Morgan, Sam) have been instructed to avoid git write operations
- They cannot use: git add, git commit, git push, git merge, git rebase, git reset, etc.
- They can only use read-only git commands: git status, git diff, git log, git show, etc.
- Agents can modify files but will not commit changes to git
- If you need commits, you'll need to handle them manually outside the AI team session
- Coordinate with agents to understand what changes they've made for manual commits"""

            # Start Claude in orchestrator pane with --permission-mode bypassPermissions
            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    f"{self.session_name}:0.0",
                    "claude --permission-mode bypassPermissions",
                    "Enter",
                ],
                check=True,
            )

            logger.info("Started Claude in orchestrator pane")
            # Reduced delay in non-interactive mode
            delay = 2 if self.non_interactive else 5
            time.sleep(delay)

            # Validate target and send briefing to orchestrator
            orchestrator_target = f"{self.session_name}:0.0"
            valid, error = SecurityValidator.validate_pane_target(orchestrator_target)
            if not valid:
                logger.error(f"Invalid orchestrator target: {error}")
                return False

            # Enhance orchestrator briefing with context and create workspace
            orchestrator_workspace = self.context_manager.ensure_workspace(self.session_name, "Orchestrator")
            enhanced_orchestrator_briefing = self.context_manager.inject_context_into_briefing(
                orchestrator_briefing, "orchestrator"
            )
            logger.debug(f"Orchestrator workspace: {orchestrator_workspace.path}")

            sanitized_briefing = SecurityValidator.sanitize_message(enhanced_orchestrator_briefing)
            subprocess.run([send_script, orchestrator_target, sanitized_briefing], check=True)

            logger.info("Briefed orchestrator")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting up orchestrator: {e}")
            return False

    def display_team_info(self):
        """Display information about the created team"""
        print("\n" + "=" * 60)
        if self.observe_only:
            print("🔍 AI TEAM CREATED IN OBSERVE-ONLY MODE!")
        else:
            print("🚀 AI TEAM SUCCESSFULLY CREATED!")
        print("=" * 60)

        print(f"\nSession: {self.session_name}")
        print("\nPane Layout:")
        print("┌──────────────────────────────────────────┐")
        print("│             Orchestrator                 │ <- You (pane 0.0)")
        print("├────────────┬──────────────┬──────────────┤")
        print("│    Alex    │    Morgan    │     Sam      │")
        print("│ (pane 0.1) │  (pane 0.2)  │  (pane 0.3)  │")
        print("└────────────┴──────────────┴──────────────┘")

        print("\nUseful Commands:")
        print(f"• Attach to session: tmux attach -t {self.session_name}")
        print(f"• List panes: tmux list-panes -t {self.session_name}")
        print("• Navigate panes: Ctrl+B, then arrow keys")
        print("• Send messages: send-claude-message.sh session:pane 'message'")

        print("\nAgent Personalities:")
        print("🎯 Alex: Perfectionist, advocates for best practices, long-term thinking")
        print("⚡ Morgan: Pragmatist, focuses on shipping and business value")
        print("🧹 Sam: Code janitor, tackles technical debt and cleanup tasks")

        print("\nNext Steps:")
        print("1. Attach to the session to see the orchestrator")
        if self.observe_only:
            print("2. Agents are in observe-only mode - they'll introduce themselves")
            print("3. You can then assign specific tasks to prevent chaos")
        else:
            print("2. The orchestrator will introduce the agents to each other")
            print("3. Give them a coding challenge to see their different approaches!")
        print("\n" + "=" * 60)

    def create_team(self):
        """Main method to create the complete AI team"""
        logger.info("Starting AI team creation process")
        print("🚀 Creating AI Team with Orchestrator + 3 Opinionated Agents...")
        print("-" * 60)

        # Create agent profiles
        self.agents = self.create_agent_profiles()
        logger.info(f"Created {len(self.agents)} agent profiles")
        print(f"✓ Created {len(self.agents)} agent profiles (Alex, Morgan, Sam)")

        # Create tmux session
        if not self.create_tmux_session():
            return False

        # Create agent panes
        if not self.create_agent_panes():
            return False

        # Start Claude in agent windows
        print("\n📡 Starting Claude agents...")
        if not self.start_claude_agents():
            return False

        # Brief the agents
        print("\n📋 Briefing agents with their personalities...")
        if not self.brief_agents():
            return False

        # Setup orchestrator last
        print("\n🎯 Setting up orchestrator...")
        if not self.setup_orchestrator():
            return False

        # Create recovery script and verify agent readiness
        try:
            self.context_manager.create_recovery_script()
            logger.info("Created recovery script in working directory")

            # Verify all agents are ready
            for agent in self.agents:
                is_ready, issues = self.context_manager.verify_agent_readiness(self.session_name, agent.name)
                if not is_ready:
                    logger.warning(f"Agent {agent.name} has issues: {issues}")
                else:
                    logger.info(f"Agent {agent.name} verified and ready")
        except Exception as e:
            logger.warning(f"Could not complete setup verification: {e}")

        # Display team info
        self.display_team_info()
        logger.info("AI team creation completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Create an AI team with orchestrator and three opinionated agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 create_ai_team.py                      # Create default team
  python3 create_ai_team.py --session my-team    # Create with custom session name
  python3 create_ai_team.py --yes                # Non-interactive mode (fast)
  python3 create_ai_team.py --no-git-write       # Prevent agents from making git commits
  python3 create_ai_team.py -o -n                # Observe-only + no git writes (safest mode)
  python3 create_ai_team.py -i "Build a REST API"  # Team works on specific initiative

This creates:
- 1 Orchestrator (coordinates and mediates)
- Alex: Perfectionist architect (quality-focused)
- Morgan: Pragmatic shipper (speed-focused)
- Sam: Code janitor (cleanup-focused)

Flags:
--no-git-write/-n: Prevents all agents from performing git write operations
                   (commits, adds, pushes, merges, etc.) for safety
        """
    )

    parser.add_argument(
        "--session", "-s", default="ai-team", help="Name for the tmux session (default: ai-team)", type=str
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--yes", "-y", action="store_true", help="Non-interactive mode: skip prompts and use defaults")

    parser.add_argument(
        "--observe-only",
        "-o",
        action="store_true",
        help="Agents introduce themselves and wait for instructions (no auto-work)",
    )

    parser.add_argument(
        "--no-git-write",
        "-n",
        action="store_true",
        help="Prevent agents from performing any git write operations (commits, adds, pushes, etc.)",
    )

    parser.add_argument(
        "--initiative",
        "-i",
        type=str,
        help="Specific initiative/task for the AI team to work on together",
    )

    args = parser.parse_args()

    # Validate session name from args
    valid, error = SecurityValidator.validate_session_name(args.session)
    if not valid:
        logger.error(f"Invalid session name: {error}")
        print(f"❌ Invalid session name: {error}")  # User-facing error
        sys.exit(1)

    # Create the team
    orchestrator = AITeamOrchestrator(
        non_interactive=args.yes, 
        observe_only=args.observe_only,
        no_git_write=args.no_git_write,
        initiative=args.initiative
    )
    orchestrator.session_name = args.session

    try:
        success = orchestrator.create_team()
        if success:
            print(f"\n✅ AI team created successfully!")
            print(f"💡 Run: tmux attach -t {args.session}")
            sys.exit(0)
        else:
            logger.error("Failed to create AI team")
            print("\n❌ Failed to create AI team")  # User-facing error
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Setup interrupted by user")
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during AI team creation: {e}")
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")  # User-facing error
        sys.exit(1)


if __name__ == "__main__":
    main()
