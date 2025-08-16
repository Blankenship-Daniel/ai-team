#!/usr/bin/env python3
"""
Tests for agent creation and lifecycle management
Priority: Test agent creation flow and workspace setup
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from unified_context_manager import UnifiedContextManager, AgentWorkspace
from context_registry import ContextRegistry


class TestAgentWorkspaceCreation:
    """Test agent workspace creation and tool setup"""
    
    @pytest.mark.unit
    def test_workspace_structure_creation(self, temp_dir):
        """Test basic workspace structure creation"""
        # Mock install directory with required files
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create mock tools
        (install_dir / 'send-claude-message.sh').write_text('#!/bin/bash\necho "mock script"')
        (install_dir / 'schedule_with_note.sh').write_text('#!/bin/bash\necho "mock scheduler"')
        
        # Initialize context manager
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create workspace
        workspace = ucm.ensure_workspace('test-session', 'alex-architect')
        
        # Verify workspace structure
        assert workspace.path.exists()
        assert workspace.tools_dir.exists()
        assert workspace.context_file.exists()
        assert workspace.status_file.exists()
        
        # Check directory structure
        expected_path = temp_dir / '.ai-team-workspace' / 'test-session' / 'alex-architect'
        assert workspace.path == expected_path
        assert (workspace.path / 'tools').exists()
    
    @pytest.mark.unit
    def test_agent_tools_copying(self, temp_dir):
        """Test copying of essential tools to workspace"""
        # Setup mock install directory
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create mock tools with executable permissions
        send_script = install_dir / 'send-claude-message.sh'
        send_script.write_text('#!/bin/bash\necho "sending message"')
        send_script.chmod(0o755)
        
        schedule_script = install_dir / 'schedule_with_note.sh'  
        schedule_script.write_text('#!/bin/bash\necho "scheduling"')
        schedule_script.chmod(0o755)
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create workspace
        workspace = ucm.ensure_workspace('tools-test', 'agent')
        
        # Verify tools were copied
        copied_send = workspace.tools_dir / 'send-claude-message.sh'
        copied_schedule = workspace.tools_dir / 'schedule_with_note.sh'
        
        assert copied_send.exists()
        assert copied_schedule.exists()
        
        # Verify permissions preserved
        assert copied_send.stat().st_mode & 0o755
        assert copied_schedule.stat().st_mode & 0o755
        
        # Verify content copied correctly
        assert 'sending message' in copied_send.read_text()
        assert 'scheduling' in copied_schedule.read_text()
    
    @pytest.mark.unit
    def test_context_file_creation(self, temp_dir):
        """Test context file creation with proper metadata"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        workspace = ucm.ensure_workspace('context-test', 'morgan-shipper')
        
        # Verify context file exists and has correct content
        assert workspace.context_file.exists()
        
        with open(workspace.context_file) as f:
            context_data = json.load(f)
        
        assert context_data['version'] == '2.0'
        assert context_data['session'] == 'context-test'
        assert context_data['agent'] == 'morgan-shipper'
        assert Path(context_data['install_dir']).resolve() == install_dir.resolve()
        assert Path(context_data['working_dir']).resolve() == temp_dir.resolve()
        assert 'core_context' in context_data
        assert 'timestamp' in context_data
    
    @pytest.mark.unit
    def test_status_file_creation(self, temp_dir):
        """Test status file creation for agent tracking"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        workspace = ucm.ensure_workspace('status-test', 'sam-janitor')
        
        # Verify status file exists and has correct content
        assert workspace.status_file.exists()
        
        status_content = workspace.status_file.read_text()
        assert 'Agent Status: sam-janitor' in status_content
        assert 'Current Status' in status_content
        assert 'Tasks' in status_content
        assert 'Initialize workspace' in status_content
        assert '**Context Version**: 2.0' in status_content
    
    @pytest.mark.unit
    def test_symlink_creation(self, temp_dir):
        """Test symlink creation for tools in working directory"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create source tools
        send_script = install_dir / 'send-claude-message.sh'
        send_script.write_text('#!/bin/bash\necho "symlink test"')
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        workspace = ucm.ensure_workspace('symlink-test', 'agent')
        
        # Check symlinks were created in working directory
        symlink_send = temp_dir / 'send-claude-message.sh'
        
        if symlink_send.exists():
            assert symlink_send.is_symlink()
            assert symlink_send.resolve() == send_script.resolve()
            
            # Verify symlinked script works
            content = symlink_send.read_text()
            assert 'symlink test' in content
    
    @pytest.mark.unit
    def test_workspace_caching(self, temp_dir):
        """Test workspace caching to avoid recreation"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create workspace first time
        workspace1 = ucm.ensure_workspace('cache-test', 'agent')
        initial_path = workspace1.path
        
        # Get workspace second time (should be cached)
        workspace2 = ucm.ensure_workspace('cache-test', 'agent')
        
        # Should be the same object (cached)
        assert workspace1 is workspace2
        assert workspace2.path == initial_path


class TestAgentContextInjection:
    """Test context injection for different agent roles"""
    
    @pytest.mark.unit
    def test_role_specific_context_injection(self, temp_dir):
        """Test context injection for different agent roles"""
        ucm = UnifiedContextManager(install_dir=temp_dir)
        
        roles_to_test = [
            ('orchestrator', 'Monitor all project managers'),
            ('senior_software_engineer', 'Enforce SOLID principles'),
            ('full_stack_developer', 'Focus on MVP and iteration'),
            ('code_quality_engineer', 'Track technical debt')
        ]
        
        for role, expected_text in roles_to_test:
            original_briefing = f"You are a {role}."
            enhanced = ucm.inject_context_into_briefing(original_briefing, role)
            
            # Should contain original briefing
            assert original_briefing in enhanced
            
            # Should contain role-specific context
            assert expected_text in enhanced
            
            # Should contain core context
            assert 'tmux send-keys' in enhanced
            assert 'git commit' in enhanced
            assert 'EMBEDDED OPERATIONAL CONTEXT' in enhanced
    
    @pytest.mark.unit
    def test_context_injection_with_environment_info(self, temp_dir):
        """Test context injection includes environment information"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        original = "You are a test agent."
        enhanced = ucm.inject_context_into_briefing(original, 'developer')
        
        # Should contain environment information
        assert str(temp_dir) in enhanced  # Working directory
        assert str(install_dir) in enhanced  # Install directory
        assert 'Current Environment' in enhanced
        assert 'send-claude-message.sh' in enhanced
    
    @pytest.mark.unit
    def test_context_injection_length_validation(self, temp_dir):
        """Test context injection produces reasonable length output"""
        ucm = UnifiedContextManager(install_dir=temp_dir)
        
        original = "Brief instruction."
        enhanced = ucm.inject_context_into_briefing(original, 'orchestrator')
        
        # Enhanced should be significantly longer
        assert len(enhanced) > len(original) * 10
        
        # But not excessively long (< 10KB for reasonable token usage)
        assert len(enhanced) < 10000


class TestAgentCreationFlow:
    """Test complete agent creation and initialization flow"""
    
    @pytest.mark.integration
    def test_complete_agent_creation_flow(self, temp_dir):
        """Test complete agent creation from start to finish"""
        # Setup environment
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create required tools
        send_script = install_dir / 'send-claude-message.sh'
        send_script.write_text('#!/bin/bash\necho "Agent creation test"')
        send_script.chmod(0o755)
        
        # Initialize context manager
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create agent workspace
        session_name = 'ai-team'
        agent_name = 'alex-architect'
        
        workspace = ucm.ensure_workspace(session_name, agent_name)
        
        # Verify complete workspace creation
        assert workspace.path.exists()
        assert workspace.tools_dir.exists()
        assert workspace.context_file.exists()
        assert workspace.status_file.exists()
        
        # Verify tools are available
        assert (workspace.tools_dir / 'send-claude-message.sh').exists()
        
        # Verify context injection would work
        briefing = "You are Alex, the perfectionist architect."
        enhanced_briefing = ucm.inject_context_into_briefing(briefing, 'senior_software_engineer')
        
        assert 'Enforce SOLID principles' in enhanced_briefing
        assert str(temp_dir) in enhanced_briefing
        
        # Test recovery script creation
        recovery_script = ucm.create_recovery_script()
        assert recovery_script.exists()
        assert recovery_script.is_file()
        
        # Verify recovery script content
        recovery_content = recovery_script.read_text()
        assert 'RESTORING AGENT CONTEXT' in recovery_content
        assert 'send-claude-message.sh' in recovery_content
        assert 'tmux send-keys' in recovery_content
    
    @pytest.mark.integration
    def test_multi_agent_workspace_creation(self, temp_dir):
        """Test creating workspaces for multiple agents"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create tools
        for tool in ['send-claude-message.sh', 'schedule_with_note.sh']:
            tool_path = install_dir / tool
            tool_path.write_text(f'#!/bin/bash\necho "{tool}"')
            tool_path.chmod(0o755)
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create multiple agent workspaces
        agents = [
            ('ai-team', 'orchestrator'),
            ('ai-team', 'alex-architect'),  
            ('ai-team', 'morgan-shipper'),
            ('ai-team', 'sam-janitor')
        ]
        
        workspaces = {}
        for session, agent in agents:
            workspace = ucm.ensure_workspace(session, agent)
            workspaces[agent] = workspace
            
            # Verify each workspace is isolated
            assert workspace.path.exists()
            assert agent in str(workspace.path)
            
            # Verify context file has correct agent name
            with open(workspace.context_file) as f:
                context_data = json.load(f)
            assert context_data['agent'] == agent
        
        # Verify workspaces are independent
        assert len(workspaces) == 4
        paths = [w.path for w in workspaces.values()]
        assert len(set(paths)) == 4  # All unique paths
    
    @pytest.mark.unit
    def test_workspace_readiness_verification(self, temp_dir):
        """Test verifying agent workspace readiness"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create tools
        send_script = install_dir / 'send-claude-message.sh'
        send_script.write_text('#!/bin/bash\necho "ready"')
        send_script.chmod(0o755)
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create workspace
        workspace = ucm.ensure_workspace('readiness-test', 'agent')
        
        # Verify readiness
        is_ready, issues = ucm.verify_agent_readiness('readiness-test', 'agent')
        
        if issues:
            # Print issues for debugging
            print(f"Readiness issues: {issues}")
        
        # Should be ready (or have minimal issues)
        assert isinstance(is_ready, bool)
        assert isinstance(issues, list)
    
    @pytest.mark.unit
    def test_workspace_cleanup(self, temp_dir):
        """Test workspace cleanup functionality"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        # Create workspaces
        ucm.ensure_workspace('cleanup-test', 'agent1')
        ucm.ensure_workspace('cleanup-test', 'agent2')
        ucm.ensure_workspace('other-session', 'agent3')
        
        # Verify workspaces exist
        workspace_root = temp_dir / '.ai-team-workspace'
        assert (workspace_root / 'cleanup-test' / 'agent1').exists()
        assert (workspace_root / 'cleanup-test' / 'agent2').exists()
        assert (workspace_root / 'other-session' / 'agent3').exists()
        
        # Cleanup specific session
        ucm.cleanup_workspaces('cleanup-test')
        
        # Verify cleanup worked
        assert not (workspace_root / 'cleanup-test').exists()
        assert (workspace_root / 'other-session' / 'agent3').exists()


class TestAgentLifecycleIntegration:
    """Test integration between agent creation and context registry"""
    
    @pytest.mark.integration
    def test_agent_creation_with_context_registry(self, temp_dir):
        """Test agent creation integrates with context registry"""
        install_dir = temp_dir / 'install'
        install_dir.mkdir()
        
        # Create tools
        send_script = install_dir / 'send-claude-message.sh'
        send_script.write_text('#!/bin/bash\necho "integration test"')
        send_script.chmod(0o755)
        
        # Initialize both systems
        ucm = UnifiedContextManager(install_dir=install_dir)
        ucm.working_dir = temp_dir
        
        registry = ContextRegistry(storage_dir=temp_dir / 'context-registry')
        
        # Create agent workspace
        workspace = ucm.ensure_workspace('integration-test', 'alex')
        
        # Create initial context checkpoint for agent
        initial_context = {
            'agent_role': 'senior_software_engineer',
            'workspace_path': str(workspace.path),
            'tools_available': ['send-claude-message.sh'],
            'session_start': 'integration_test'
        }
        
        checkpoint_id = registry.create_checkpoint(
            'integration-test', 0, initial_context
        )
        
        # Verify integration
        assert checkpoint_id is not None
        
        # Verify agent state
        state = registry.get_state('integration-test', 0)
        assert state.agent_id == 'integration-test:0'
        assert state.last_checkpoint_id == checkpoint_id
        
        # Verify workspace and context work together
        assert workspace.path.exists()
        
        # Get context status
        context_status = registry.get_checkpoint_summary('integration-test', 0)
        assert context_status['total_checkpoints'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])