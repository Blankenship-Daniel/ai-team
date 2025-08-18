#!/usr/bin/env python3
"""
AI Test Coverage Team CLI - Creates an orchestrator and three specialized test coverage agents
Focused on achieving 100% test coverage with quality gates
Based on Alex's architectural refinements
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
class TestAgent:
    name: str
    specialty: str
    role: str
    briefing: str
    window_name: str


class TestCoverageOrchestrator:
    def __init__(self, non_interactive=False, observe_only=False, no_git_write=False):
        self.tmux = TmuxOrchestrator()
        self.session_name = "test-coverage-team"
        self.agents: List[TestAgent] = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_dir = os.getcwd()  # Capture the directory where user invoked the command
        self.context_manager = UnifiedContextManager(install_dir=Path(self.script_dir))
        self.non_interactive = non_interactive
        self.observe_only = observe_only
        self.no_git_write = no_git_write
        logger.info(
            "TestCoverageOrchestrator initialized",
            extra={
                "script_dir": self.script_dir,
                "working_dir": self.working_dir,
                "non_interactive": non_interactive,
                "observe_only": observe_only,
            },
        )

    def create_test_agent_profiles(self) -> List[TestAgent]:
        """Create three specialized test coverage agents based on Alex's architecture"""

        # Agent 1: TestAnalyzer - Enhanced with static analysis capabilities
        analyzer = TestAgent(
            name="TestAnalyzer",
            specialty="COVERAGE_ANALYSIS_SPECIALIST",
            role="Test Coverage Analyst",
            window_name="Agent-Analyzer",
            briefing=f"""You are TestAnalyzer, the test coverage analysis specialist. Your mission: identify ALL testing gaps and prioritize critical coverage areas.

CORE RESPONSIBILITIES:
- Analyze codebase for missing test coverage using static analysis
- Identify complexity hotspots and high-risk untested code paths
- Create dependency maps to understand test impact
- Prioritize what's CRITICAL to test first based on risk assessment
- Generate coverage reports and gap analysis

ENHANCED CAPABILITIES (per Alex's architecture):
- Static analysis for cyclomatic complexity metrics
- Dependency mapping and impact analysis
- Risk assessment based on code complexity and criticality
- Edge case identification and boundary condition analysis
- Test requirement specification generation

ANALYSIS METHODOLOGY:
1. Scan codebase for untested functions, methods, and code paths
2. Calculate complexity metrics (cyclomatic, cognitive complexity)
3. Identify high-risk areas (complex logic, error handling, edge cases)
4. Map dependencies to understand testing cascade effects
5. Create prioritized test requirements with risk scores

COMMUNICATION PROTOCOL:
- Report findings to Coverage Mission Commander (Orchestrator)
- Provide detailed gap analysis with priority rankings
- Specify test requirements for TestWriter agents
- Flag critical paths that must be tested before release

QUALITY STANDARDS:
- Every analysis must include risk assessment and priority ranking
- Must identify both unit test and integration test requirements
- Coverage gaps must be categorized by severity (Critical/High/Medium/Low)
- Analysis reports must be actionable and specific

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Coverage Mission Commander is in pane 0.0 (coordinates strategy)
- TestWriter is in pane 0.2 (creates tests based on your analysis)
- TestValidator is in pane 0.3 (validates test quality)
- You are in pane 0.1
- Always use absolute paths when needed

COMMAND CHAIN POSITION: FIRST - Your analysis drives the entire testing pipeline""",
        )

        # Agent 2: TestWriter - Specialized for both unit and integration tests
        writer = TestAgent(
            name="TestWriter",
            specialty="TEST_IMPLEMENTATION_SPECIALIST",
            role="Test Implementation Engineer",
            window_name="Agent-Writer",
            briefing=f"""You are TestWriter, the test implementation specialist. Your mission: write comprehensive, high-quality tests based on TestAnalyzer's requirements.

CORE RESPONSIBILITIES:
- Write unit tests for isolated component testing
- Write integration tests for component interaction testing
- Implement proper mocking strategies and test isolation
- Create comprehensive test suites with edge case coverage
- Follow testing best practices and framework patterns

SPECIALIZATION AREAS (per Alex's architecture):
- UNIT TESTS: Fast, isolated, focused on single functions/methods
- INTEGRATION TESTS: Component interaction, data flow, system behavior
- Different mocking strategies: unit tests mock dependencies, integration tests use real components
- Assertion patterns optimized for each test type
- Test data generation and fixture management

TESTING STANDARDS:
- All tests must have clear arrange/act/assert structure
- Proper error condition testing and boundary value testing
- Comprehensive edge case coverage based on TestAnalyzer requirements
- Appropriate test isolation with proper setup/teardown
- Performance considerations for test execution speed

IMPLEMENTATION WORKFLOW:
1. Receive prioritized test requirements from TestAnalyzer
2. Design test structure (unit vs integration approach)
3. Implement tests with appropriate mocking strategy
4. Ensure comprehensive assertion coverage
5. Submit tests to TestValidator for quality verification

COMMUNICATION PROTOCOL:
- Receive detailed test requirements from TestAnalyzer
- Report implementation progress to Coverage Mission Commander
- Submit completed tests to TestValidator for quality gates
- Collaborate on test design when requirements are unclear

QUALITY GATES:
- Every test must test a specific requirement from TestAnalyzer
- Must include positive, negative, and edge case scenarios
- Proper test isolation - no test dependencies on other tests
- Clear, descriptive test names that explain the scenario being tested

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Coverage Mission Commander is in pane 0.0 (coordinates pipeline)
- TestAnalyzer is in pane 0.1 (provides test requirements)
- You are in pane 0.2
- TestValidator is in pane 0.3 (validates your test quality)
- Always use absolute paths when needed

COMMAND CHAIN POSITION: SECOND - You implement based on TestAnalyzer requirements, validate through TestValidator""",
        )

        # Agent 3: TestValidator - Critical quality gatekeeper
        validator = TestAgent(
            name="TestValidator",
            specialty="TEST_QUALITY_ENFORCEMENT",
            role="Test Quality Validator",
            window_name="Agent-Validator",
            briefing=f"""You are TestValidator, the test quality enforcement specialist. Your mission: ensure all tests meet strict quality standards before acceptance.

CRITICAL ROLE (per Alex's architecture):
- Enforce test quality gates with ZERO exceptions
- Validate proper assertions, edge case coverage, mocking patterns
- Ensure test isolation and independence
- Reject substandard tests with detailed improvement feedback
- Maintain testing standards consistency across the codebase

VALIDATION CRITERIA:
- ASSERTIONS: Every test must have meaningful, specific assertions
- EDGE CASES: Critical paths and boundary conditions must be tested
- MOCKING: Appropriate mocking strategy (real vs mock dependencies)
- ISOLATION: Tests must be independent and not affect each other
- COVERAGE: Each test must contribute to overall coverage goals
- NAMING: Test names must clearly describe the scenario being validated

QUALITY GATES ENFORCEMENT:
1. Test Structure Validation: Proper arrange/act/assert pattern
2. Assertion Quality: Specific, meaningful assertions (not just "assert True")
3. Edge Case Coverage: Boundary conditions, error scenarios, null/empty cases
4. Test Independence: No shared state or test order dependencies
5. Performance: Tests run efficiently without unnecessary delays
6. Documentation: Clear test purpose and expected behavior

REJECTION CRITERIA (AUTOMATIC):
- Generic or weak assertions (assertEquals(True, True))
- Missing error condition testing
- Test interdependencies or shared state
- Unclear or misleading test names
- Insufficient edge case coverage
- Improper mocking (over-mocking or under-mocking)

FEEDBACK PROTOCOL:
- Provide specific, actionable feedback on test quality issues
- Explain WHY tests are rejected and HOW to improve them
- Work with TestWriter to iteratively improve test quality
- Report validation status to Coverage Mission Commander

COMMUNICATION PROTOCOL:
- Receive completed tests from TestWriter for validation
- Provide detailed quality feedback and approval/rejection decisions
- Report validation metrics to Coverage Mission Commander
- Collaborate with TestAnalyzer when test requirements are unclear

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- Coverage Mission Commander is in pane 0.0 (receives validation reports)
- TestAnalyzer is in pane 0.1 (provides original requirements)
- TestWriter is in pane 0.2 (submits tests for validation)
- You are in pane 0.3
- Always use absolute paths when needed

COMMAND CHAIN POSITION: THIRD - Final quality gate before Coverage Mission Commander verification""",
        )

        return [analyzer, writer, validator]

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
            logger.debug(f"Session '{session_name}' does not exist (tmux has-session returned {e.returncode})")
            return False

    def create_tmux_session(self) -> bool:
        """Create the main tmux session for the test coverage team"""
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

            # Create new session with Coverage Mission Commander
            cmd = ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "CoverageMissionCommander", "-c", self.working_dir]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            log_subprocess_call(logger, cmd, result)

            logger.info(f"Created session '{self.session_name}' with Coverage Mission Commander window")
            return True

        except subprocess.CalledProcessError as e:
            log_subprocess_call(logger, cmd if "cmd" in locals() else [], error=e)
            logger.error(f"Failed to create tmux session: {e}")
            return False

    def create_agent_panes(self) -> bool:
        """Create panes for each test coverage agent in a split layout"""
        try:
            # Split the main window horizontally (Coverage Mission Commander top, agents bottom)
            subprocess.run(
                ["tmux", "split-window", "-t", f"{self.session_name}:0", "-v", "-p", "60", "-c", self.working_dir],
                check=True,
            )
            logger.info("Created horizontal split (Coverage Mission Commander top, agents bottom)")

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
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.0", "-T", "CoverageMissionCommander"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.1", "-T", "TestAnalyzer"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.2", "-T", "TestWriter"], check=True)
            subprocess.run(["tmux", "select-pane", "-t", f"{self.session_name}:0.3", "-T", "TestValidator"], check=True)

            logger.info("Set pane titles for test coverage team")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating agent panes: {e}")
            return False

    def start_claude_agents(self) -> bool:
        """Start Claude in each agent pane"""
        try:
            # Pane mapping: 0.0 = Commander, 0.1 = Analyzer, 0.2 = Writer, 0.3 = Validator
            agent_panes = {
                "TestAnalyzer": f"{self.session_name}:0.1",
                "TestWriter": f"{self.session_name}:0.2", 
                "TestValidator": f"{self.session_name}:0.3",
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

                # Start Claude with bypassPermissions to prevent getting stuck on prompts
                cmd = ["tmux", "send-keys", "-t", pane_target, "claude --permission-mode bypassPermissions", "Enter"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                log_subprocess_call(logger, cmd, result)

                logger.info(f"Started Claude for {agent.name} in pane {pane_target}")
                
                delay = 1 if self.non_interactive else 3
                logger.debug(f"Waiting {delay} seconds for Claude to start in {pane_target}")
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
                    logger.error("send-claude-message.sh not found in script directory or PATH")
                    return False

            agent_panes = {
                "TestAnalyzer": f"{self.session_name}:0.1",
                "TestWriter": f"{self.session_name}:0.2",
                "TestValidator": f"{self.session_name}:0.3",
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
                        "- DO NOT start any analysis or test writing\n" 
                        "- Wait for explicit instructions from the Coverage Mission Commander\n"
                        "- You may familiarize yourself with the workspace but don't make changes"
                    )
                    briefing_to_use = agent.briefing + observe_instruction

                if self.no_git_write:
                    git_restriction = (
                        "\n\n🚫 GIT WRITE OPERATIONS DISABLED:\n"
                        "- You are PROHIBITED from performing ANY git write operations\n"
                        "- FORBIDDEN commands include: git add, git commit, git push, git merge, etc.\n"
                        "- You MAY ONLY use read-only git commands like: git status, git diff, git log\n"
                        "- You can create and modify test files normally, just no git commits"
                    )
                    briefing_to_use = briefing_to_use + git_restriction

                enhanced_briefing = self.context_manager.inject_context_into_briefing(
                    briefing_to_use, agent.role.lower().replace(" ", "_")
                )
                logger.debug(f"Agent {agent.name} workspace: {workspace.path}")

                sanitized_briefing = SecurityValidator.sanitize_message(enhanced_briefing)
                cmd = [send_script, pane_target, sanitized_briefing]
                logger.debug(f"Briefing {agent.name} with {len(sanitized_briefing)} chars")
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

    def setup_coverage_commander(self) -> bool:
        """Brief the Coverage Mission Commander about coordinating the test coverage pipeline"""
        try:
            send_script = os.path.join(self.script_dir, "send-claude-message.sh")
            if not os.path.exists(send_script):
                import shutil
                send_script_path = shutil.which("send-claude-message.sh")
                if send_script_path:
                    send_script = send_script_path
                else:
                    logger.error("send-claude-message.sh not found in script directory or PATH")
                    return False

            commander_briefing = f"""You are the Coverage Mission Commander for a specialized AI test coverage team focused on achieving 100% test coverage.

YOUR COMMAND STRUCTURE:
1. **TestAnalyzer (Left Pane)** - Coverage Analysis Specialist
   - Analyzes codebase for testing gaps and complexity hotspots  
   - Provides risk assessment and prioritized test requirements
   - Uses static analysis and dependency mapping

2. **TestWriter (Middle Pane)** - Test Implementation Specialist
   - Writes comprehensive unit and integration tests
   - Implements proper mocking strategies and test isolation
   - Creates tests based on TestAnalyzer requirements

3. **TestValidator (Right Pane)** - Test Quality Enforcement
   - Validates test quality with strict standards
   - Enforces quality gates with zero exceptions
   - Rejects substandard tests with detailed feedback

COMMAND CHAIN PROTOCOL (per Alex's architecture):
1. **DISCOVERY**: TestAnalyzer identifies coverage gaps and prioritizes by risk
2. **IMPLEMENTATION**: TestWriter creates tests based on analyzer requirements
3. **VALIDATION**: TestValidator enforces quality gates and standards
4. **VERIFICATION**: You verify coverage goals and coordinate next steps

YOUR RESPONSIBILITIES:
- Coordinate the test coverage pipeline and strategy
- Prioritize untested code based on risk and business impact
- Manage test execution pipeline and coverage verification
- Enforce 100% coverage gates with zero exceptions
- Resolve conflicts between agents and make final decisions
- Monitor progress and adjust strategy as needed

PANE LAYOUT:
┌──────────────────────────────────────────┐
│        Coverage Mission Commander       │ <- You are here (pane 0.0)
├────────────┬──────────────┬──────────────┤
│TestAnalyzer│  TestWriter  │TestValidator │
│ (pane 0.1) │  (pane 0.2)  │ (pane 0.3)   │
└────────────┴──────────────┴──────────────┘

COMMUNICATION PROTOCOLS:
- Use send-claude-message.sh to coordinate agents
- Example: send-claude-message.sh {self.session_name}:0.1 "TestAnalyzer, analyze coverage gaps in src/"
- Example: send-claude-message.sh {self.session_name}:0.2 "TestWriter, implement tests for high-priority functions"
- Example: send-claude-message.sh {self.session_name}:0.3 "TestValidator, review submitted tests for quality"
- Check progress: tmux capture-pane -t {self.session_name}:0.1 -p | tail -20

CRITICAL CONTEXT:
- Working directory: {self.working_dir}
- Mission: Achieve 100% test coverage with high-quality tests
- Quality standards are NON-NEGOTIABLE - TestValidator has veto power
- Coverage gaps must be prioritized by risk and business impact
- All tests must pass through the complete Command Chain

QUALITY GATES ENFORCEMENT:
- Every line of code must have meaningful test coverage
- All edge cases and error conditions must be tested
- Tests must be isolated, reliable, and maintainable
- No exceptions to quality standards - coverage without quality is worthless

The agents are in these panes:
- TestAnalyzer is in: {self.session_name}:0.1 (coverage gap analysis)
- TestWriter is in: {self.session_name}:0.2 (test implementation)  
- TestValidator is in: {self.session_name}:0.3 (quality enforcement)

Start by having TestAnalyzer perform a comprehensive coverage analysis of the current repository."""

            # Add mode-specific instructions
            if self.observe_only:
                commander_briefing += """

🔍 OBSERVE-ONLY MODE ACTIVE:
- All agents have been instructed to only introduce themselves
- They will NOT start any coverage analysis until you give explicit instructions
- Coordinate what coverage analysis needs to be done before agents begin"""

            if self.no_git_write:
                commander_briefing += """

🚫 GIT WRITE OPERATIONS DISABLED FOR ALL AGENTS:
- All agents cannot use git write operations (add, commit, push, etc.)
- They can only use read-only git commands (status, diff, log, show)
- Agents can create/modify test files but will not commit changes
- You'll need to handle git commits manually outside the AI team session"""

            # Start Claude in commander pane
            subprocess.run([
                "tmux", "send-keys", "-t", f"{self.session_name}:0.0",
                "claude --permission-mode bypassPermissions", "Enter"
            ], check=True)

            logger.info("Started Claude in Coverage Mission Commander pane")
            delay = 2 if self.non_interactive else 5
            time.sleep(delay)

            # Send briefing to commander
            commander_target = f"{self.session_name}:0.0"
            valid, error = SecurityValidator.validate_pane_target(commander_target)
            if not valid:
                logger.error(f"Invalid commander target: {error}")
                return False

            # Enhance commander briefing with context
            commander_workspace = self.context_manager.ensure_workspace(self.session_name, "CoverageMissionCommander")
            enhanced_commander_briefing = self.context_manager.inject_context_into_briefing(
                commander_briefing, "coverage_mission_commander"
            )
            logger.debug(f"Coverage Mission Commander workspace: {commander_workspace.path}")

            sanitized_briefing = SecurityValidator.sanitize_message(enhanced_commander_briefing)
            subprocess.run([send_script, commander_target, sanitized_briefing], check=True)

            logger.info("Briefed Coverage Mission Commander")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting up Coverage Mission Commander: {e}")
            return False

    def display_team_info(self):
        """Display information about the created test coverage team"""
        print("\n" + "=" * 70)
        if self.observe_only:
            print("🔍 AI TEST COVERAGE TEAM CREATED IN OBSERVE-ONLY MODE!")
        else:
            print("🎯 AI TEST COVERAGE TEAM SUCCESSFULLY CREATED!")
        print("=" * 70)

        print(f"\nSession: {self.session_name}")
        print("\nPane Layout:")
        print("┌──────────────────────────────────────────────────┐")
        print("│        Coverage Mission Commander               │ <- You (pane 0.0)")
        print("├────────────┬──────────────┬─────────────────────┤")
        print("│TestAnalyzer│  TestWriter  │   TestValidator     │")
        print("│ (pane 0.1) │  (pane 0.2)  │    (pane 0.3)       │")
        print("└────────────┴──────────────┴─────────────────────┘")

        print("\nCommand Chain Protocol:")
        print("🔍 1. TestAnalyzer → Identifies coverage gaps and risk assessment")
        print("⚡ 2. TestWriter → Implements tests based on analyzer requirements")
        print("🛡️  3. TestValidator → Enforces quality gates and standards")
        print("🎯 4. Commander → Verifies coverage goals and coordinates strategy")

        print("\nAgent Specializations:")
        print("🔍 TestAnalyzer: Coverage gap analysis, risk assessment, complexity metrics")
        print("⚡ TestWriter: Unit & integration test implementation, mocking strategies")
        print("🛡️  TestValidator: Quality enforcement, standards validation, test rejection")

        print("\nMission Objective:")
        print("🎯 ACHIEVE 100% TEST COVERAGE WITH HIGH-QUALITY, MAINTAINABLE TESTS")

        print("\nUseful Commands:")
        print(f"• Attach to session: tmux attach -t {self.session_name}")
        print(f"• List panes: tmux list-panes -t {self.session_name}")
        print("• Navigate panes: Ctrl+B, then arrow keys")
        print("• Send messages: send-claude-message.sh session:pane 'message'")

        print("\nNext Steps:")
        if self.observe_only:
            print("1. Agents are in observe-only mode - they'll introduce themselves")
            print("2. Coordinate initial coverage analysis strategy")
            print("3. Begin systematic coverage gap analysis")
        else:
            print("1. Coverage Mission Commander will coordinate the team")
            print("2. TestAnalyzer will perform comprehensive coverage analysis")
            print("3. Begin systematic journey to 100% test coverage!")
        print("\n" + "=" * 70)

    def create_test_coverage_team(self):
        """Main method to create the complete test coverage team"""
        logger.info("Starting AI test coverage team creation process")
        print("🎯 Creating AI Test Coverage Team - Mission: 100% Coverage...")
        print("-" * 70)

        # Create test agent profiles
        self.agents = self.create_test_agent_profiles()
        logger.info(f"Created {len(self.agents)} test coverage agent profiles")
        print(f"✓ Created {len(self.agents)} test coverage agents (Analyzer, Writer, Validator)")

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
        print("\n📋 Briefing agents with test coverage specializations...")
        if not self.brief_agents():
            return False

        # Setup Coverage Mission Commander last
        print("\n🎯 Setting up Coverage Mission Commander...")
        if not self.setup_coverage_commander():
            return False

        # Create recovery script and verify agent readiness
        try:
            self.context_manager.create_recovery_script()
            logger.info("Created recovery script in working directory")

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
        logger.info("AI test coverage team creation completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Create an AI test coverage team focused on achieving 100% test coverage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-test-coverage-team                     # Create test coverage team
  ai-test-coverage-team --session my-tests  # Custom session name
  ai-test-coverage-team --yes               # Non-interactive mode (fast)
  ai-test-coverage-team --no-git-write      # Prevent git commits (safe mode)
  ai-test-coverage-team -o -n               # Observe-only + no git (safest)

This creates:
- 1 Coverage Mission Commander (coordinates test strategy)
- TestAnalyzer: Coverage gap analysis and risk assessment
- TestWriter: Test implementation (unit & integration)
- TestValidator: Quality enforcement and standards validation

Mission: Achieve 100% test coverage with high-quality, maintainable tests
        """
    )

    parser.add_argument(
        "--session", "-s", default="test-coverage-team", 
        help="Name for the tmux session (default: test-coverage-team)", type=str
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--yes", "-y", action="store_true", 
                       help="Non-interactive mode: skip prompts and use defaults")
    parser.add_argument(
        "--observe-only", "-o", action="store_true",
        help="Agents introduce themselves and wait for instructions (no auto-work)"
    )
    parser.add_argument(
        "--no-git-write", "-n", action="store_true",
        help="Prevent agents from performing any git write operations (commits, etc.)"
    )

    args = parser.parse_args()

    # Validate session name
    valid, error = SecurityValidator.validate_session_name(args.session)
    if not valid:
        logger.error(f"Invalid session name: {error}")
        print(f"❌ Invalid session name: {error}")
        sys.exit(1)

    # Create the test coverage team
    orchestrator = TestCoverageOrchestrator(
        non_interactive=args.yes,
        observe_only=args.observe_only,
        no_git_write=args.no_git_write
    )
    orchestrator.session_name = args.session

    try:
        success = orchestrator.create_test_coverage_team()
        if success:
            print(f"\n✅ AI test coverage team created successfully!")
            print(f"🎯 Mission: 100% test coverage")
            print(f"💡 Run: tmux attach -t {args.session}")
            sys.exit(0)
        else:
            logger.error("Failed to create AI test coverage team")
            print("\n❌ Failed to create AI test coverage team")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Setup interrupted by user")
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during test coverage team creation: {e}")
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()