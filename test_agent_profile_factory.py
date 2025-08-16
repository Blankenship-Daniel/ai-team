#!/usr/bin/env python3
"""
Comprehensive tests for AgentProfileFactory extraction
Following TDD approach with 80%+ coverage requirement
"""

import pytest
from pathlib import Path
from agent_profile_factory import (
    AgentProfileFactoryAdapter,
    EnhancedAgentProfileFactory,
    AgentProfileFactory,
)
from interfaces import AgentProfile


class TestAgentProfileFactoryAdapter:
    """Test the exact extraction adapter for backward compatibility"""

    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        working_dir = "/test/dir"
        adapter = AgentProfileFactoryAdapter(working_dir)
        assert adapter.working_dir == working_dir

    def test_create_agent_profiles_returns_three_profiles(self):
        """Test adapter creates exactly 3 agent profiles"""
        adapter = AgentProfileFactoryAdapter("/test/dir")
        profiles = adapter.create_agent_profiles()

        assert len(profiles) == 3
        assert all(isinstance(profile, AgentProfile) for profile in profiles)

    def test_alex_profile_content(self):
        """Test Alex profile has correct attributes"""
        adapter = AgentProfileFactoryAdapter("/test/dir")
        profiles = adapter.create_agent_profiles()
        alex = profiles[0]

        assert alex.name == "Alex-Purist"
        assert alex.personality == "PERFECTIONIST_ARCHITECT"
        assert alex.role == "Senior Software Engineer"
        assert alex.window_name == "Agent-Alex"
        assert "You are Alex" in alex.briefing
        assert "/test/dir" in alex.briefing
        assert "pane 0.1" in alex.briefing

    def test_morgan_profile_content(self):
        """Test Morgan profile has correct attributes"""
        adapter = AgentProfileFactoryAdapter("/test/dir")
        profiles = adapter.create_agent_profiles()
        morgan = profiles[1]

        assert morgan.name == "Morgan-Pragmatist"
        assert morgan.personality == "SHIP_IT_ENGINEER"
        assert morgan.role == "Full-Stack Developer"
        assert morgan.window_name == "Agent-Morgan"
        assert "You are Morgan" in morgan.briefing
        assert "/test/dir" in morgan.briefing
        assert "pane 0.2" in morgan.briefing

    def test_sam_profile_content(self):
        """Test Sam profile has correct attributes"""
        adapter = AgentProfileFactoryAdapter("/test/dir")
        profiles = adapter.create_agent_profiles()
        sam = profiles[2]

        assert sam.name == "Sam-Janitor"
        assert sam.personality == "CODE_CUSTODIAN"
        assert sam.role == "Code Quality Engineer"
        assert sam.window_name == "Agent-Sam"
        assert "You are Sam" in sam.briefing
        assert "/test/dir" in sam.briefing
        assert "pane 0.3" in sam.briefing

    def test_working_dir_interpolation(self):
        """Test working directory is properly interpolated in briefings"""
        custom_dir = "/custom/working/directory"
        adapter = AgentProfileFactoryAdapter(custom_dir)
        profiles = adapter.create_agent_profiles()

        for profile in profiles:
            assert custom_dir in profile.briefing


class TestEnhancedAgentProfileFactory:
    """Test the enhanced factory with extensibility features"""

    def test_enhanced_initialization(self):
        """Test enhanced factory initializes correctly"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        assert factory.working_dir == "/test/dir"
        assert factory._adapter is not None

    def test_create_agent_profiles_delegates_to_adapter(self):
        """Test enhanced factory delegates to adapter for backward compatibility"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        profiles = factory.create_agent_profiles()

        # Should return same result as adapter
        adapter = AgentProfileFactoryAdapter("/test/dir")
        adapter_profiles = adapter.create_agent_profiles()

        assert len(profiles) == len(adapter_profiles) == 3
        for i, (enhanced_profile, adapter_profile) in enumerate(zip(profiles, adapter_profiles)):
            assert enhanced_profile.name == adapter_profile.name
            assert enhanced_profile.personality == adapter_profile.personality

    def test_create_custom_agent_profile(self):
        """Test custom agent profile creation"""
        factory = EnhancedAgentProfileFactory("/test/dir")

        custom_profile = factory.create_custom_agent_profile(
            name="TestAgent",
            personality="TEST_PERSONALITY",
            role="Test Role",
            window_name="Test-Window",
            custom_briefing="This is a test briefing",
        )

        assert custom_profile.name == "TestAgent"
        assert custom_profile.personality == "TEST_PERSONALITY"
        assert custom_profile.role == "Test Role"
        assert custom_profile.window_name == "Test-Window"
        assert "This is a test briefing" in custom_profile.briefing
        assert "/test/dir" in custom_profile.briefing

    def test_get_default_profiles(self):
        """Test explicit default profiles method"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        default_profiles = factory.get_default_profiles()
        regular_profiles = factory.create_agent_profiles()

        assert len(default_profiles) == len(regular_profiles) == 3
        for default, regular in zip(default_profiles, regular_profiles):
            assert default.name == regular.name

    def test_validate_profile_valid(self):
        """Test profile validation with valid profile"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        profiles = factory.create_agent_profiles()

        for profile in profiles:
            assert factory.validate_profile(profile) is True

    def test_validate_profile_invalid_missing_name(self):
        """Test profile validation with missing name"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        invalid_profile = AgentProfile(
            name="", personality="TEST", role="Test Role", window_name="Test-Window", briefing="Test briefing"
        )

        assert factory.validate_profile(invalid_profile) is False

    def test_validate_profile_invalid_missing_briefing(self):
        """Test profile validation with missing briefing"""
        factory = EnhancedAgentProfileFactory("/test/dir")
        invalid_profile = AgentProfile(
            name="TestAgent", personality="TEST", role="Test Role", window_name="Test-Window", briefing=""
        )

        assert factory.validate_profile(invalid_profile) is False


class TestAgentProfileFactory:
    """Test the factory creation patterns"""

    def test_create_factory(self):
        """Test factory creation method"""
        factory = AgentProfileFactory.create_factory("/test/dir")
        assert isinstance(factory, EnhancedAgentProfileFactory)
        assert factory.working_dir == "/test/dir"

    def test_create_default_profiles_convenience(self):
        """Test convenience method for creating default profiles"""
        profiles = AgentProfileFactory.create_default_profiles("/test/dir")

        assert len(profiles) == 3
        assert all(isinstance(profile, AgentProfile) for profile in profiles)

        # Should match direct factory creation
        factory = AgentProfileFactory.create_factory("/test/dir")
        factory_profiles = factory.create_agent_profiles()

        for convenience, factory_profile in zip(profiles, factory_profiles):
            assert convenience.name == factory_profile.name


class TestIntegration:
    """Integration tests for complete extraction"""

    def test_backward_compatibility_with_original(self):
        """Test that extraction maintains exact compatibility with original"""
        # This would test against original create_ai_team.py method
        # For now, we verify the structure matches expectations
        factory = AgentProfileFactory.create_factory("/test/dir")
        profiles = factory.create_agent_profiles()

        # Verify we have the exact 3 agents expected
        names = [p.name for p in profiles]
        assert "Alex-Purist" in names
        assert "Morgan-Pragmatist" in names
        assert "Sam-Janitor" in names

        # Verify personalities match expected
        personalities = [p.personality for p in profiles]
        assert "PERFECTIONIST_ARCHITECT" in personalities
        assert "SHIP_IT_ENGINEER" in personalities
        assert "CODE_CUSTODIAN" in personalities

    def test_working_directory_consistency(self):
        """Test working directory handling across all factory levels"""
        test_dir = "/consistent/test/directory"

        # Test at all levels
        adapter = AgentProfileFactoryAdapter(test_dir)
        enhanced = EnhancedAgentProfileFactory(test_dir)
        factory_created = AgentProfileFactory.create_factory(test_dir)

        adapter_profiles = adapter.create_agent_profiles()
        enhanced_profiles = enhanced.create_agent_profiles()
        factory_profiles = factory_created.create_agent_profiles()

        # All should contain the test directory
        for profiles in [adapter_profiles, enhanced_profiles, factory_profiles]:
            for profile in profiles:
                assert test_dir in profile.briefing

    def test_all_required_fields_present(self):
        """Test that all AgentProfile fields are properly populated"""
        factory = AgentProfileFactory.create_factory("/test/dir")
        profiles = factory.create_agent_profiles()

        for profile in profiles:
            assert profile.name, f"Missing name in profile"
            assert profile.personality, f"Missing personality in profile {profile.name}"
            assert profile.role, f"Missing role in profile {profile.name}"
            assert profile.window_name, f"Missing window_name in profile {profile.name}"
            assert profile.briefing, f"Missing briefing in profile {profile.name}"
            assert len(profile.briefing) > 100, f"Briefing too short in profile {profile.name}"
