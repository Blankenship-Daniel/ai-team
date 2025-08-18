#!/usr/bin/env python3
"""
FAST PRAGMATIC TESTS for create_test_coverage_team.py
Target: 100% coverage in <1 second
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock all dependencies
sys.modules['tmux_utils'] = Mock()
sys.modules['security_validator'] = Mock()
sys.modules['logging_config'] = Mock()
sys.modules['unified_context_manager'] = Mock()

from create_test_coverage_team import TestCoverageOrchestrator, TestCoverageAgent


class TestCoverageTeamFast:
    """Ultra-fast coverage tests - mock everything"""
    
    @pytest.fixture
    def orchestrator(self):
        with patch('create_test_coverage_team.TmuxOrchestrator'), \
             patch('create_test_coverage_team.UnifiedContextManager'), \
             patch('create_test_coverage_team.setup_logging'):
            return TestCoverageOrchestrator(non_interactive=True)
    
    def test_create_test_coverage_agents(self, orchestrator):
        """Test agent creation - covers all agent definitions"""
        agents = orchestrator.create_test_coverage_agents()
        assert len(agents) == 3
        assert agents[0].name == "TestAnalyzer"
        assert agents[1].name == "TestWriter"
        assert agents[2].name == "TestValidator"
        # Verify specialties
        assert "mutation testing" in agents[0].specialty
        assert "pytest" in agents[1].specialty
        assert "test quality" in agents[2].specialty
    
    @patch('subprocess.run')
    def test_session_management(self, mock_run, orchestrator):
        """Test session exists/create/kill flow"""
        # Session exists
        mock_run.return_value = MagicMock(returncode=0)
        assert orchestrator.session_exists("test") == True
        
        # Create session
        with patch.object(orchestrator, 'session_exists', return_value=False):
            assert orchestrator.create_tmux_session() == True
    
    @patch('subprocess.run')
    def test_create_agent_panes(self, mock_run, orchestrator):
        """Test pane creation for 3 agents"""
        mock_run.return_value = MagicMock(returncode=0)
        assert orchestrator.create_agent_panes() == True
        assert mock_run.call_count >= 2  # At least 2 splits
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_start_and_brief_agents(self, mock_sleep, mock_run, orchestrator):
        """Test Claude startup and briefing"""
        mock_run.return_value = MagicMock(returncode=0)
        orchestrator.agents = orchestrator.create_test_coverage_agents()
        
        # Start agents
        assert orchestrator.start_claude_agents() == True
        
        # Brief agents
        with patch('os.path.exists', return_value=True):
            assert orchestrator.brief_agents() == True
    
    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_setup_orchestrator(self, mock_exists, mock_run, orchestrator):
        """Test orchestrator setup"""
        mock_run.return_value = MagicMock(returncode=0)
        assert orchestrator.setup_orchestrator() == True
    
    def test_display_info(self, orchestrator, capsys):
        """Test info display"""
        orchestrator.agents = orchestrator.create_test_coverage_agents()
        orchestrator.display_team_info()
        captured = capsys.readouterr()
        assert "TEST COVERAGE TEAM" in captured.out
    
    @patch.object(TestCoverageOrchestrator, 'create_tmux_session', return_value=True)
    @patch.object(TestCoverageOrchestrator, 'create_agent_panes', return_value=True)
    @patch.object(TestCoverageOrchestrator, 'start_claude_agents', return_value=True)
    @patch.object(TestCoverageOrchestrator, 'brief_agents', return_value=True)
    @patch.object(TestCoverageOrchestrator, 'setup_orchestrator', return_value=True)
    def test_create_team_full(self, *mocks, orchestrator):
        """Test complete flow"""
        assert orchestrator.create_team() == True
        for mock in mocks:
            mock.assert_called_once()
    
    def test_observe_mode(self):
        """Test observe-only mode"""
        with patch('create_test_coverage_team.TmuxOrchestrator'):
            orch = TestCoverageOrchestrator(observe_only=True)
            assert orch.observe_only == True
    
    def test_no_git_mode(self):
        """Test no-git-write mode"""
        with patch('create_test_coverage_team.TmuxOrchestrator'):
            orch = TestCoverageOrchestrator(no_git_write=True)
            assert orch.no_git_write == True


@patch('sys.argv', ['test_coverage_team.py'])
@patch.object(TestCoverageOrchestrator, 'create_team', return_value=True)
def test_main_function(mock_create):
    """Test main entry point"""
    with patch('create_test_coverage_team.SecurityValidator'):
        from create_test_coverage_team import main
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])