#!/usr/bin/env python3
"""
AgentProfileFactory - Extracted using systematic refactoring blueprint
Implements IAgentProfileFactory Protocol for clean architecture
"""

from typing import List
from pathlib import Path
from ai_team.core.interfaces import IAgentProfileFactory, AgentProfile
from ai_team.utils.logging_config import setup_logging

logger = setup_logging(__name__)


class AgentProfileFactoryAdapter:
    """
    Adapter: Exact extraction from create_ai_team.py with zero breaking changes
    This maintains backward compatibility while providing clean interface
    """

    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        logger.debug(f"AgentProfileFactoryAdapter initialized with working_dir: {working_dir}")

    def create_agent_profiles(self) -> List[AgentProfile]:
        """Create three strongly opinionated AI agent profiles - EXACT extraction"""

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
- Always use absolute paths when needed""",
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
- Always use absolute paths when needed""",
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
- Always use absolute paths when needed""",
        )

        logger.info("Created 3 agent profiles successfully")
        return [agent1, agent2, agent3]


class EnhancedAgentProfileFactory:
    """
    Enhanced: Adds extensibility and clean architecture patterns
    Implements IAgentProfileFactory Protocol with future-ready design
    """

    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self._adapter = AgentProfileFactoryAdapter(working_dir)
        logger.debug(f"EnhancedAgentProfileFactory initialized with working_dir: {working_dir}")

    def create_agent_profiles(self) -> List[AgentProfile]:
        """Create agent profiles using adapter pattern for backward compatibility"""
        return self._adapter.create_agent_profiles()

    def create_custom_agent_profile(
        self, name: str, personality: str, role: str, window_name: str, custom_briefing: str
    ) -> AgentProfile:
        """Enhanced: Create custom agent profile for extensibility"""
        briefing = f"""{custom_briefing}

WORKING CONTEXT:
- You're in directory: {self.working_dir}
- You can read/write files and run commands
- Always use absolute paths when needed"""

        profile = AgentProfile(
            name=name, personality=personality, role=role, window_name=window_name, briefing=briefing
        )
        logger.info(f"Created custom agent profile: {name}")
        return profile

    def get_default_profiles(self) -> List[AgentProfile]:
        """Enhanced: Explicit method for default profiles"""
        return self.create_agent_profiles()

    def validate_profile(self, profile: AgentProfile) -> bool:
        """Enhanced: Validation for agent profiles"""
        if not profile.name or not profile.personality or not profile.role:
            logger.warning(f"Invalid profile: missing required fields")
            return False
        if not profile.window_name or not profile.briefing:
            logger.warning(f"Invalid profile: missing window_name or briefing")
            return False
        logger.debug(f"Profile validation passed for: {profile.name}")
        return True


class AgentProfileFactory:
    """
    Factory: Clean creation patterns with dependency injection support
    Primary interface for agent profile creation
    """

    @staticmethod
    def create_factory(working_dir: str) -> EnhancedAgentProfileFactory:
        """Factory method for creating agent profile factories"""
        logger.debug(f"Creating AgentProfileFactory for working_dir: {working_dir}")
        return EnhancedAgentProfileFactory(working_dir)

    @staticmethod
    def create_default_profiles(working_dir: str) -> List[AgentProfile]:
        """Convenience method for creating default profiles"""
        factory = AgentProfileFactory.create_factory(working_dir)
        return factory.create_agent_profiles()
