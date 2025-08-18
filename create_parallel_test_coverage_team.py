#!/usr/bin/env python3
"""
AI Parallel Test Coverage Team CLI - Creates an orchestrator and three independent test coverage agents
Each agent works independently on assigned priorities from the orchestrator
No sequential dependencies - true parallel execution
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
from tmux_utils import TmuxOrchestrator
from security_validator import SecurityValidator
from logging_config import setup_logging, log_subprocess_call
from unified_context_manager import UnifiedContextManager

# Set up logging for this module
logger = setup_logging(__name__)


@dataclass
class TestCoverageAgent:
    name: str
    specialty: str
    role: str
    briefing: str
    window_name: str


class ParallelTestCoverageOrchestrator:
    def __init__(self, non_interactive=False, observe_only=False, no_git_write=False):
        self.tmux = TmuxOrchestrator()
        self.session_name = "parallel-test-coverage"
        self.agents: List[TestCoverageAgent] = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_dir = os.getcwd()  
        self.context_manager = UnifiedContextManager(install_dir=Path(self.script_dir))
        self.non_interactive = non_interactive
        self.observe_only = observe_only
        self.no_git_write = no_git_write
        logger.info(
            "ParallelTestCoverageOrchestrator initialized",
            extra={
                "script_dir": self.script_dir,
                "working_dir": self.working_dir,
                "non_interactive": non_interactive,
                "observe_only": observe_only,
            },
        )

    def create_test_coverage_agents(self) -> List[TestCoverageAgent]:
        """Create three independent test coverage agents that work in parallel"""

        # Agent 1: CoverageHunter - Finds untested code and creates tests for gaps
        hunter = TestCoverageAgent(
            name="CoverageHunter",
            specialty="UNTESTED_CODE_SPECIALIST",
            role="Test Gap Hunter",
            window_name="Agent-Hunter",
            briefing=f"""You are CoverageHunter, an independent test coverage specialist. Your mission: find untested code and write tests to eliminate coverage gaps.

INDEPENDENCE DECLARATION:
- You work INDEPENDENTLY and in PARALLEL with other agents
- You DO NOT wait for other agents to complete their work
- You receive priorities directly from the Test Coverage Orchestrator
- You complete tasks at your own pace without dependencies

CORE RESPONSIBILITIES:
- Hunt for untested functions, methods, and code paths
- Write comprehensive tests for discovered gaps
- Focus on achieving maximum code coverage quickly
- Create both positive and negative test cases
- Test edge cases and boundary conditions

YOUR SPECIALIZATION:
- Finding code with 0% coverage (completely untested)
- Writing tests for utility functions and helper methods
- Creating parameterized tests for broad coverage
- Testing error handling and exception paths
- Covering all branches and conditional logic

WORKING METHODOLOGY:
1. Scan codebase for untested code using coverage tools
2. Prioritize based on orchestrator's assignment
3. Write comprehensive test suites for assigned areas
4. Report completion back to orchestrator
5. Move to next priority without waiting

QUALITY STANDARDS:
- Every test must be meaningful (no placeholder assertions)
- Include edge cases and error conditions
- Tests must be independent and isolated
- Clear test names that describe what's being tested
- Fast execution (no unnecessary delays)

COMMUNICATION PROTOCOL:
- Receive priority assignments from Test Coverage Orchestrator (pane 0.0)
- Report completion of assigned coverage areas
- Work independently - DO NOT coordinate with other agents
- Ask orchestrator for next priority when current task is complete

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Test Coverage Orchestrator is in pane 0.0 (assigns priorities)
- You are in pane 0.1
- Other agents work in parallel in panes 0.2 and 0.3
- Always use absolute paths when needed

YOUR MOTTO: "No code left untested!" Work fast, work independently, maximize coverage.""",
        )

        # Agent 2: CriticalPathTester - Focuses on critical business logic and high-risk areas
        critical = TestCoverageAgent(
            name="CriticalPathTester",
            specialty="CRITICAL_LOGIC_SPECIALIST",
            role="Critical Path Tester",
            window_name="Agent-Critical",
            briefing=f"""You are CriticalPathTester, an independent test coverage specialist. Your mission: ensure critical business logic and high-risk code paths have bulletproof test coverage.

INDEPENDENCE DECLARATION:
- You work INDEPENDENTLY and in PARALLEL with other agents
- You DO NOT wait for other agents to complete their work
- You receive priorities directly from the Test Coverage Orchestrator
- You complete tasks at your own pace without dependencies

CORE RESPONSIBILITIES:
- Focus on critical business logic and core functionality
- Test high-risk areas with complex logic
- Create comprehensive integration tests
- Ensure data validation and security checks are tested
- Test performance-critical code paths

YOUR SPECIALIZATION:
- Business logic validation and workflows
- Security-critical functions (auth, permissions, validation)
- Data processing and transformation logic
- API endpoints and service interfaces
- Database operations and transactions

WORKING METHODOLOGY:
1. Identify critical paths based on orchestrator's priority
2. Write thorough tests for business logic
3. Create integration tests for component interactions
4. Test failure scenarios and recovery paths
5. Move to next critical area without waiting

QUALITY FOCUS:
- Test both happy paths and failure scenarios
- Validate business rules and constraints
- Ensure proper error handling is tested
- Test concurrent operations where applicable
- Verify data integrity and consistency

COMMUNICATION PROTOCOL:
- Receive critical area assignments from Test Coverage Orchestrator (pane 0.0)
- Report completion of critical path testing
- Work independently - DO NOT coordinate with other agents
- Request next priority when ready

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Test Coverage Orchestrator is in pane 0.0 (assigns priorities)
- You are in pane 0.2
- Other agents work in parallel in panes 0.1 and 0.3
- Always use absolute paths when needed

YOUR MOTTO: "Critical paths deserve critical attention!" Work independently, ensure quality.""",
        )

        # Agent 3: EdgeCaseMaster - Specializes in edge cases, corner cases, and unusual scenarios
        edge = TestCoverageAgent(
            name="EdgeCaseMaster",
            specialty="EDGE_CASE_SPECIALIST",
            role="Edge Case Master",
            window_name="Agent-Edge",
            briefing=f"""You are EdgeCaseMaster, an independent test coverage specialist. Your mission: find and test all edge cases, corner cases, and unusual scenarios that others might miss.

INDEPENDENCE DECLARATION:
- You work INDEPENDENTLY and in PARALLEL with other agents
- You DO NOT wait for other agents to complete their work
- You receive priorities directly from the Test Coverage Orchestrator
- You complete tasks at your own pace without dependencies

CORE RESPONSIBILITIES:
- Identify and test edge cases and corner cases
- Test boundary conditions and limits
- Create tests for unusual input combinations
- Test race conditions and timing issues
- Cover exceptional and unexpected scenarios

YOUR SPECIALIZATION:
- Null, undefined, and empty value handling
- Maximum and minimum value boundaries
- Unicode and special character handling
- Concurrent access and race conditions
- Memory and resource limit testing
- Timeout and cancellation scenarios
- Invalid state transitions

WORKING METHODOLOGY:
1. Analyze code for potential edge cases
2. Focus on areas assigned by orchestrator
3. Create comprehensive edge case test suites
4. Test unusual combinations and sequences
5. Move to next assignment independently

EDGE CASE PATTERNS:
- Empty collections and null references
- Off-by-one errors and boundary overflows
- Recursive depth limits and stack overflows
- Malformed input and injection attempts
- Resource exhaustion scenarios
- Timing and ordering dependencies

COMMUNICATION PROTOCOL:
- Receive edge case priorities from Test Coverage Orchestrator (pane 0.0)
- Report completion of edge case coverage
- Work independently - DO NOT coordinate with other agents
- Request next area when ready

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Test Coverage Orchestrator is in pane 0.0 (assigns priorities)
- You are in pane 0.3
- Other agents work in parallel in panes 0.1 and 0.2
- Always use absolute paths when needed

YOUR MOTTO: "If it can break, I'll find how!" Work independently, think creatively.""",
        )

        return [hunter, critical, edge]

    def session_exists(self, session_name: str) -> bool:
        """Check if a tmux session already exists"""
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
            logger.debug(f"Session '{session_name}' does not exist")
            return False

    def create_tmux_session(self) -> bool:
        """Create the main tmux session for the parallel test coverage team"""
        try:
            valid, error = SecurityValidator.validate_session_name(self.session_name)
            if not valid:
                logger.error(f"Invalid session name: {error}")
                return False

            if self.session_exists(self.session_name):
                logger.warning(f"Session '{self.session_name}' already exists. Killing it first...")
                cmd = ["tmux", "kill-session", "-t", self.session_name]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

            # Create new session with Test Coverage Orchestrator
            cmd = ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "TestCoverageOrchestrator", "-c", self.working_dir]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            log_subprocess_call(logger, cmd, result)

            logger.info(f"Created session '{self.session_name}' with Test Coverage Orchestrator window")
            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to create tmux session: {e}")
            return False

    def create_agent_panes(self) -> bool:
        """Create panes for each test coverage agent in a 2x2 grid layout"""
        try:
            # Split horizontally to create top and bottom sections
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0", "-v", "-p", "60", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created horizontal split (Orchestrator top, agents bottom)")

            # Split the bottom section vertically to create three agent panes
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
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.0", "-T", "TestCoverageOrchestrator"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.1", "-T", "CoverageHunter"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.2", "-T", "CriticalPathTester"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.3", "-T", "EdgeCaseMaster"], check=True)

            logger.info("Set pane titles for parallel test coverage team")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating agent panes: {e}")
            return False

    def start_claude_agents(self) -> bool:
        """Start Claude in each agent pane"""
        try:
            # Pane mapping
            agent_panes = {
                "CoverageHunter": f"{self.session_name}:0.1",
                "CriticalPathTester": f"{self.session_name}:0.2", 
                "EdgeCaseMaster": f"{self.session_name}:0.3",
            }

            for agent in self.agents:
                pane_target = agent_panes.get(agent.name)
                if not pane_target:
                    logger.error(f"Could not find pane for {agent.name}")
                    continue

                valid, error = SecurityValidator.validate_pane_target(pane_target)
                if not valid:
                    logger.error(f"Invalid pane target {pane_target}: {error}")
                    continue

                # Start Claude with bypassPermissions
                cmd = ["tmux", "send-keys", "-t", pane_target, "claude --permission-mode bypassPermissions", "Enter"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

                logger.info(f"Started Claude for {agent.name} in pane {pane_target}")
                
                delay = 1 if self.non_interactive else 3
                logger.debug(f"Waiting {delay} seconds for Claude to start")
                time.sleep(delay)

            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to start Claude agents: {e}")
            return False

    def brief_agents(self) -> bool:
        """Send briefing messages to each test coverage agent"""
        try:
            send_script = os.path.join(self.script_dir, "send-claude-message.sh")
            if not os.path.exists(send_script):
                import shutil
                send_script_path = shutil.which("send-claude-message.sh")
                if send_script_path:
                    send_script = send_script_path
                else:
                    logger.error("send-claude-message.sh not found")
                    return False

            agent_panes = {
                "CoverageHunter": f"{self.session_name}:0.1",
                "CriticalPathTester": f"{self.session_name}:0.2",
                "EdgeCaseMaster": f"{self.session_name}:0.3",
            }

            for agent in self.agents:
                pane_target = agent_panes.get(agent.name)
                if not pane_target:
                    logger.error(f"Could not find pane for {agent.name}")
                    continue

                valid, error = SecurityValidator.validate_pane_target(pane_target)
                if not valid:
                    logger.error(f"Invalid pane target {pane_target}: {error}")
                    continue

                # Enhance briefing with workspace and context
                workspace = self.context_manager.ensure_workspace(self.session_name, agent.name)

                briefing_to_use = agent.briefing
                if self.observe_only:
                    observe_instruction = (
                        "\n\n🔍 OBSERVE-ONLY MODE ACTIVE:\n"
                        "- Please introduce yourself and your test coverage capabilities\n"
                        "- DO NOT start any testing until instructed by the orchestrator\n" 
                        "- Wait for specific priority assignments\n"
                        "- You may familiarize yourself with the codebase but don't write tests yet"
                    )
                    briefing_to_use = agent.briefing + observe_instruction

                if self.no_git_write:
                    git_restriction = (
                        "\n\n🚫 GIT WRITE OPERATIONS DISABLED:\n"
                        "- You are PROHIBITED from performing ANY git write operations\n"
                        "- FORBIDDEN: git add, git commit, git push, git merge, etc.\n"
                        "- ALLOWED: git status, git diff, git log (read-only operations)\n"
                        "- You can create and modify test files normally"
                    )
                    briefing_to_use = briefing_to_use + git_restriction

                enhanced_briefing = self.context_manager.inject_context_into_briefing(
                    briefing_to_use, agent.role.lower().replace(" ", "_")
                )
                logger.debug(f"Agent {agent.name} workspace: {workspace.path}")

                sanitized_briefing = SecurityValidator.sanitize_message(enhanced_briefing)
                cmd = [send_script, pane_target, sanitized_briefing]
                logger.debug(f"Briefing {agent.name}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd[:2] + ["<briefing_text>"], result)

                logger.info(f"Briefed {agent.name} in pane {pane_target}")
                delay = 0.5 if self.non_interactive else 2
                time.sleep(delay)

            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd[:2] + ["<briefing_text>"] if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to brief agents: {e}")
            return False

    def setup_orchestrator(self) -> bool:
        """Brief the Test Coverage Orchestrator about coordinating parallel agents"""
        try:
            send_script = os.path.join(self.script_dir, "send-claude-message.sh")
            if not os.path.exists(send_script):
                import shutil
                send_script_path = shutil.which("send-claude-message.sh")
                if send_script_path:
                    send_script = send_script_path
                else:
                    logger.error("send-claude-message.sh not found")
                    return False

            orchestrator_briefing = f"""You are the Test Coverage Orchestrator for a PARALLEL test coverage team. Your agents work INDEPENDENTLY and SIMULTANEOUSLY.

YOUR TEAM (ALL WORKING IN PARALLEL):
1. **CoverageHunter (pane 0.1)** - Finds untested code, writes comprehensive tests
2. **CriticalPathTester (pane 0.2)** - Tests critical business logic and high-risk areas
3. **EdgeCaseMaster (pane 0.3)** - Specializes in edge cases and unusual scenarios

CRITICAL DIFFERENCE FROM SEQUENTIAL TEAMS:
- Agents work IN PARALLEL, not in sequence
- Each agent works INDEPENDENTLY on assigned tasks
- No agent waits for another to complete
- You distribute different priorities to each agent
- All three agents can work simultaneously

YOUR ORCHESTRATION ROLE:
1. Analyze the codebase to identify coverage needs
2. Distribute DIFFERENT priorities to each agent based on their specialties
3. Monitor progress without blocking any agent
4. Reassign priorities as tasks are completed
5. Ensure comprehensive coverage through parallel effort

TASK DISTRIBUTION STRATEGY:
- CoverageHunter: Assign untested utility functions, helper methods, basic coverage gaps
- CriticalPathTester: Assign business logic, APIs, security functions, data operations
- EdgeCaseMaster: Assign complex functions, validation logic, error handlers

PANE LAYOUT:
┌──────────────────────────────────────────┐
│       Test Coverage Orchestrator        │ <- You are here (pane 0.0)
├────────────┬──────────────┬──────────────┤
│CoverageHunt│CriticalPath  │EdgeCaseMaster│
│er(pane 0.1)│Tester(0.2)   │  (pane 0.3)  │
└────────────┴──────────────┴──────────────┘

COMMUNICATION PROTOCOL:
- Send DIFFERENT tasks to each agent simultaneously
- Example: send-claude-message.sh {self.session_name}:0.1 "CoverageHunter, focus on untested functions in src/utils/"
- Example: send-claude-message.sh {self.session_name}:0.2 "CriticalPathTester, test the authentication logic in src/auth/"
- Example: send-claude-message.sh {self.session_name}:0.3 "EdgeCaseMaster, find edge cases in src/validators/"
- Check progress: tmux capture-pane -t {self.session_name}:0.1 -p | tail -20

WORKING DIRECTORY: {self.working_dir}

PARALLEL EXECUTION EXAMPLE:
1. First, analyze codebase for coverage gaps
2. Then distribute tasks SIMULTANEOUSLY:
   - Hunter gets utils and helpers
   - Critical gets business logic
   - Edge gets validation and error handling
3. All three work at the same time
4. As each completes, assign them new tasks

Start by analyzing the codebase, then immediately distribute different tasks to all three agents."""

            # Add mode-specific instructions
            if self.observe_only:
                orchestrator_briefing += """

🔍 OBSERVE-ONLY MODE:
- Agents will introduce themselves first
- Plan task distribution before instructing agents to begin
- Explicitly tell each agent when to start working"""

            if self.no_git_write:
                orchestrator_briefing += """

🚫 GIT RESTRICTIONS:
- All agents cannot perform git writes
- They can create/modify test files but not commit
- Handle git operations manually if needed"""

            # Start Claude in orchestrator pane
            subprocess.run([
                "tmux", "send-keys", "-t", f"{self.session_name}:0.0",
                "claude --permission-mode bypassPermissions", "Enter"
            ], check=True)

            logger.info("Started Claude in Orchestrator pane")
            delay = 2 if self.non_interactive else 5
            time.sleep(delay)

            # Send briefing to orchestrator
            orchestrator_target = f"{self.session_name}:0.0"
            valid, error = SecurityValidator.validate_pane_target(orchestrator_target)
            if not valid:
                logger.error(f"Invalid orchestrator target: {error}")
                return False

            # Enhance orchestrator briefing with context
            orchestrator_workspace = self.context_manager.ensure_workspace(self.session_name, "TestCoverageOrchestrator")
            enhanced_orchestrator_briefing = self.context_manager.inject_context_into_briefing(
                orchestrator_briefing, "test_coverage_orchestrator"
            )
            logger.debug(f"Orchestrator workspace: {orchestrator_workspace.path}")

            sanitized_briefing = SecurityValidator.sanitize_message(enhanced_orchestrator_briefing)
            subprocess.run([send_script, orchestrator_target, sanitized_briefing], check=True)

            logger.info("Briefed Test Coverage Orchestrator")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting up Orchestrator: {e}")
            return False

    def display_team_info(self):
        """Display information about the created parallel test coverage team"""
        print("\n" + "=" * 70)
        if self.observe_only:
            print("🔍 PARALLEL TEST COVERAGE TEAM - OBSERVE MODE")
        else:
            print("🚀 PARALLEL TEST COVERAGE TEAM CREATED!")
        print("=" * 70)

        print(f"\nSession: {self.session_name}")
        print("\nPane Layout:")
        print("┌──────────────────────────────────────────────────┐")
        print("│         Test Coverage Orchestrator              │")
        print("├────────────┬──────────────┬─────────────────────┤")
        print("│CoverageHunt│CriticalPath  │   EdgeCaseMaster    │")
        print("│er(pane 0.1)│Tester(0.2)   │    (pane 0.3)       │")
        print("└────────────┴──────────────┴─────────────────────┘")

        print("\n🚀 PARALLEL EXECUTION MODEL:")
        print("• All agents work INDEPENDENTLY and SIMULTANEOUSLY")
        print("• No agent waits for another to complete")
        print("• Orchestrator distributes different tasks to each")
        print("• Maximum efficiency through parallel processing")

        print("\nAgent Specializations:")
        print("🔍 CoverageHunter: Finds and fills coverage gaps")
        print("⚡ CriticalPathTester: Tests business-critical code")
        print("🎯 EdgeCaseMaster: Edge cases and corner scenarios")

        print("\nOrchestrator Commands:")
        print(f"• Attach: tmux attach -t {self.session_name}")
        print(f"• Message agent: send-claude-message.sh {self.session_name}:0.X 'message'")
        print(f"• Check progress: tmux capture-pane -t {self.session_name}:0.X -p | tail -20")

        print("\nNext Steps:")
        if self.observe_only:
            print("1. Agents will introduce themselves")
            print("2. Orchestrator will analyze coverage needs")
            print("3. Distribute tasks when ready to begin")
        else:
            print("1. Orchestrator analyzes codebase")
            print("2. Distributes tasks to all three agents")
            print("3. Agents work in parallel to maximize coverage!")
        print("\n" + "=" * 70)

    def create_parallel_team(self):
        """Main method to create the parallel test coverage team"""
        logger.info("Starting parallel test coverage team creation")
        print("🚀 Creating Parallel Test Coverage Team...")
        print("-" * 70)

        # Create agent profiles
        self.agents = self.create_test_coverage_agents()
        logger.info(f"Created {len(self.agents)} parallel test coverage agents")
        print(f"✓ Created {len(self.agents)} independent agents")

        # Create tmux session
        if not self.create_tmux_session():
            return False

        # Create agent panes
        if not self.create_agent_panes():
            return False

        # Start Claude in agent panes
        print("\n📡 Starting Claude agents...")
        if not self.start_claude_agents():
            return False

        # Brief the agents
        print("\n📋 Briefing parallel agents...")
        if not self.brief_agents():
            return False

        # Setup Orchestrator
        print("\n🎯 Setting up Test Coverage Orchestrator...")
        if not self.setup_orchestrator():
            return False

        # Create recovery script and verify
        try:
            self.context_manager.create_recovery_script()
            logger.info("Created recovery script")

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
        logger.info("Parallel test coverage team created successfully")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Create a PARALLEL AI test coverage team - agents work independently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-parallel-test-coverage                  # Create parallel team
  ai-parallel-test-coverage --session tests  # Custom session name
  ai-parallel-test-coverage --yes            # Non-interactive mode
  ai-parallel-test-coverage --observe-only   # Observe mode
  ai-parallel-test-coverage --no-git-write   # No git commits

This creates:
- 1 Test Coverage Orchestrator (distributes tasks)
- 3 Independent agents working in PARALLEL:
  • CoverageHunter: Finds and fills coverage gaps
  • CriticalPathTester: Tests critical business logic
  • EdgeCaseMaster: Edge cases and corner scenarios

Key difference: Agents work SIMULTANEOUSLY, not sequentially!
        """
    )

    parser.add_argument(
        "--session", "-s", default="parallel-test-coverage", 
        help="Name for the tmux session", type=str
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--yes", "-y", action="store_true", help="Non-interactive mode")
    parser.add_argument(
        "--observe-only", "-o", action="store_true",
        help="Agents wait for explicit instructions"
    )
    parser.add_argument(
        "--no-git-write", "-n", action="store_true",
        help="Prevent git write operations"
    )

    args = parser.parse_args()

    # Validate session name
    valid, error = SecurityValidator.validate_session_name(args.session)
    if not valid:
        logger.error(f"Invalid session name: {error}")
        print(f"❌ Invalid session name: {error}")
        sys.exit(1)

    # Create the parallel team
    orchestrator = ParallelTestCoverageOrchestrator(
        non_interactive=args.yes,
        observe_only=args.observe_only,
        no_git_write=args.no_git_write
    )
    orchestrator.session_name = args.session

    try:
        success = orchestrator.create_parallel_team()
        if success:
            print(f"\n✅ Parallel test coverage team created!")
            print(f"🚀 Agents work independently in parallel")
            print(f"💡 Run: tmux attach -t {args.session}")
            sys.exit(0)
        else:
            logger.error("Failed to create parallel team")
            print("\n❌ Failed to create parallel team")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Setup interrupted by user")
        print("\n\n⚠️  Setup interrupted")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()