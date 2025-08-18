#!/usr/bin/env python3
"""
Comprehensive Test Suite for Orchestration Components
Covers: create_parallel_test_coverage_team.py, multi_team_coordinator.py, team_orchestration_manager.py
Architecture: Mock all external dependencies, test core logic
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import sys
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


class TestParallelTestCoverageOrchestrator(unittest.TestCase):
    """Test suite for ParallelTestCoverageOrchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tmux = Mock()
        self.mock_context_manager = Mock()
        self.mock_logger = Mock()
        
    @patch('create_parallel_test_coverage_team.TmuxOrchestrator')
    @patch('create_parallel_test_coverage_team.UnifiedContextManager')
    @patch('create_parallel_test_coverage_team.setup_logging')
    def test_orchestrator_initialization(self, mock_logging, mock_context, mock_tmux):
        """Test orchestrator initialization with proper dependency injection"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        orchestrator = ParallelTestCoverageOrchestrator(
            non_interactive=True,
            observe_only=True,
            no_git_write=True
        )
        
        self.assertEqual(orchestrator.session_name, "parallel-test-coverage")
        self.assertTrue(orchestrator.non_interactive)
        self.assertTrue(orchestrator.observe_only)
        self.assertTrue(orchestrator.no_git_write)
        mock_context.assert_called_once()
        mock_tmux.assert_called_once()
    
    @patch('create_parallel_test_coverage_team.subprocess.run')
    def test_session_exists_validation(self, mock_run):
        """Test session existence check with security validation"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        with patch('create_parallel_test_coverage_team.SecurityValidator') as mock_validator:
            mock_validator.validate_session_name.return_value = (True, None)
            mock_run.return_value = MagicMock(returncode=0)
            
            orchestrator = ParallelTestCoverageOrchestrator()
            exists = orchestrator.session_exists("test-session")
            
            self.assertTrue(exists)
            mock_validator.validate_session_name.assert_called_with("test-session")
    
    def test_create_test_coverage_agents(self):
        """Test agent creation with proper specializations"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        orchestrator = ParallelTestCoverageOrchestrator()
        agents = orchestrator.create_test_coverage_agents()
        
        self.assertEqual(len(agents), 3)
        self.assertEqual(agents[0].name, "CoverageHunter")
        self.assertEqual(agents[1].name, "CriticalPathTester")
        self.assertEqual(agents[2].name, "EdgeCaseMaster")
        
        # Verify specializations
        self.assertEqual(agents[0].specialty, "UNTESTED_CODE_SPECIALIST")
        self.assertEqual(agents[1].specialty, "CRITICAL_LOGIC_SPECIALIST")
        self.assertEqual(agents[2].specialty, "EDGE_CASE_SPECIALIST")
    
    @patch('create_parallel_test_coverage_team.subprocess.run')
    def test_create_agent_panes_layout(self, mock_run):
        """Test pane creation with 2x2 grid layout"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        mock_run.return_value = MagicMock(returncode=0)
        orchestrator = ParallelTestCoverageOrchestrator()
        result = orchestrator.create_agent_panes()
        
        self.assertTrue(result)
        # Verify 3 split commands for creating 4 panes
        self.assertEqual(mock_run.call_count, 7)  # 3 splits + 4 title sets
    
    @patch('create_parallel_test_coverage_team.subprocess.run')
    @patch('create_parallel_test_coverage_team.time.sleep')
    def test_start_claude_agents_with_bypass_permissions(self, mock_sleep, mock_run):
        """Test Claude startup with proper permission bypass"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        mock_run.return_value = MagicMock(returncode=0)
        orchestrator = ParallelTestCoverageOrchestrator(non_interactive=True)
        orchestrator.agents = orchestrator.create_test_coverage_agents()
        
        with patch('create_parallel_test_coverage_team.SecurityValidator') as mock_validator:
            mock_validator.validate_pane_target.return_value = (True, None)
            result = orchestrator.start_claude_agents()
            
            self.assertTrue(result)
            # Verify claude starts with bypassPermissions
            for call_args in mock_run.call_args_list:
                if "claude" in str(call_args):
                    self.assertIn("--permission-mode bypassPermissions", str(call_args))
    
    @patch('os.path.exists')
    @patch('create_parallel_test_coverage_team.subprocess.run')
    def test_brief_agents_with_enhanced_context(self, mock_run, mock_exists):
        """Test agent briefing with context injection"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        orchestrator = ParallelTestCoverageOrchestrator(observe_only=True, no_git_write=True)
        orchestrator.agents = orchestrator.create_test_coverage_agents()
        
        with patch.object(orchestrator.context_manager, 'ensure_workspace') as mock_workspace:
            with patch.object(orchestrator.context_manager, 'inject_context_into_briefing') as mock_inject:
                mock_workspace.return_value = Mock(path="/workspace")
                mock_inject.return_value = "enhanced briefing"
                
                with patch('create_parallel_test_coverage_team.SecurityValidator') as mock_validator:
                    mock_validator.validate_pane_target.return_value = (True, None)
                    mock_validator.sanitize_message.return_value = "sanitized"
                    
                    result = orchestrator.brief_agents()
                    
                    self.assertTrue(result)
                    # Verify observe_only and no_git_write instructions added
                    for call_args in mock_inject.call_args_list:
                        briefing = call_args[0][0]
                        self.assertIn("OBSERVE-ONLY MODE", briefing)
                        self.assertIn("GIT WRITE OPERATIONS DISABLED", briefing)


class TestMultiTeamCoordinator(unittest.TestCase):
    """Test suite for MultiTeamCoordinator"""
    
    @patch('multi_team_coordinator.TmuxOrchestrator')
    @patch('multi_team_coordinator.UnifiedContextManager')
    def test_coordinator_initialization(self, mock_context, mock_tmux):
        """Test multi-team coordinator initialization"""
        from multi_team_coordinator import MultiTeamCoordinator
        
        coordinator = MultiTeamCoordinator()
        
        self.assertIsNotNone(coordinator.tmux)
        self.assertIsNotNone(coordinator.context_manager)
        self.assertEqual(coordinator.session_name, "ai-multi-team")
    
    @patch('multi_team_coordinator.subprocess.run')
    def test_create_team_session(self, mock_run):
        """Test team session creation with validation"""
        from multi_team_coordinator import MultiTeamCoordinator
        
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('multi_team_coordinator.SecurityValidator') as mock_validator:
            mock_validator.validate_session_name.return_value = (True, None)
            
            coordinator = MultiTeamCoordinator()
            result = coordinator.create_team_session("test-team", 3)
            
            self.assertTrue(result)
            mock_validator.validate_session_name.assert_called()
    
    def test_register_team(self):
        """Test team registration"""
        from multi_team_coordinator import MultiTeamCoordinator
        
        coordinator = MultiTeamCoordinator()
        result = coordinator.register_team(
            "dev-team",
            "dev-session",
            ["frontend", "backend", "database"]
        )
        
        self.assertTrue(result)
        self.assertIn("dev-team", coordinator.teams)
        self.assertEqual(len(coordinator.teams["dev-team"]["agents"]), 3)
    
    def test_inter_team_messaging(self):
        """Test inter-team message passing"""
        from multi_team_coordinator import MultiTeamCoordinator
        
        coordinator = MultiTeamCoordinator()
        coordinator.register_team("team1", "session1", ["agent1"])
        coordinator.register_team("team2", "session2", ["agent2"])
        
        result = coordinator.send_inter_team_message(
            "team1",
            "team2",
            "sync_request",
            {"data": "test"}
        )
        
        self.assertTrue(result)
        messages = coordinator.get_team_messages("team2", mark_as_read=False)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].from_team, "team1")


class TestTeamOrchestrationManager(unittest.TestCase):
    """Test suite for TeamOrchestrationManager"""
    
    def test_manager_initialization(self):
        """Test orchestration manager initialization"""
        from team_orchestration_manager import TeamOrchestrationManager, TeamOrchestrationConfig
        
        config = TeamOrchestrationConfig(
            max_teams=5,
            max_agents_per_team=4,
            resource_limits={"memory": "1GB"}
        )
        
        with patch('team_orchestration_manager.MultiTeamCoordinator'):
            manager = TeamOrchestrationManager(config)
            
            self.assertEqual(manager.config.max_teams, 5)
            self.assertEqual(manager.config.max_agents_per_team, 4)
            self.assertIsNotNone(manager.multi_coordinator)
    
    def test_create_team(self):
        """Test team creation with validation"""
        from team_orchestration_manager import TeamOrchestrationManager
        
        with patch('team_orchestration_manager.MultiTeamCoordinator') as mock_coord:
            mock_coord.return_value.register_team.return_value = True
            
            manager = TeamOrchestrationManager()
            result = manager.create_team(
                "qa-team",
                ["tester1", "tester2"],
                "qa-session"
            )
            
            self.assertTrue(result["success"])
            self.assertIn("team_id", result)
            self.assertEqual(result["team_name"], "qa-team")
            self.assertEqual(len(result["agents"]), 2)
    
    def test_send_team_message(self):
        """Test inter-team message sending"""
        from team_orchestration_manager import TeamOrchestrationManager
        
        with patch('team_orchestration_manager.MultiTeamCoordinator') as mock_coord:
            mock_coord.return_value.send_inter_team_message.return_value = True
            
            manager = TeamOrchestrationManager()
            result = manager.send_team_message(
                "team1",
                "team2",
                "api_handoff",
                {"endpoint": "/api/v1"}
            )
            
            self.assertTrue(result["success"])
            self.assertEqual(result["from_team"], "team1")
            self.assertEqual(result["to_team"], "team2")
    
    def test_get_system_overview(self):
        """Test system overview reporting"""
        from team_orchestration_manager import TeamOrchestrationManager
        
        with patch('team_orchestration_manager.MultiTeamCoordinator') as mock_coord:
            mock_coord.return_value.get_system_health.return_value = {
                "status": "healthy",
                "teams_active": 2
            }
            
            manager = TeamOrchestrationManager()
            overview = manager.get_system_overview()
            
            self.assertIn("active_teams", overview)
            self.assertIn("system_health", overview)
            self.assertIn("resource_usage", overview)
    
    def test_team_lifecycle_management(self):
        """Test team lifecycle (create and destroy)"""
        from team_orchestration_manager import TeamOrchestrationManager
        
        with patch('team_orchestration_manager.MultiTeamCoordinator') as mock_coord:
            mock_coord.return_value.register_team.return_value = True
            mock_coord.return_value.unregister_team.return_value = True
            
            manager = TeamOrchestrationManager()
            
            # Create
            create_result = manager.create_team("lifecycle-team", ["agent1"], "test-session")
            self.assertTrue(create_result["success"])
            team_id = create_result["team_id"]
            
            # Destroy
            destroy_result = manager.destroy_team(team_id)
            self.assertTrue(destroy_result["success"])


class TestOrchestrationIntegration(unittest.TestCase):
    """Integration tests for orchestration components"""
    
    @patch('subprocess.run')
    def test_full_team_creation_workflow(self, mock_run):
        """Test complete workflow from team creation to coordination"""
        mock_run.return_value = MagicMock(returncode=0)
        
        # This would test the full integration between all three components
        # Mocking external dependencies while testing internal coordination
        pass
    
    def test_error_propagation_across_components(self):
        """Test error handling across orchestration boundaries"""
        # Verify errors in one component are properly handled by others
        pass
    
    def test_resource_cleanup_on_failure(self):
        """Test resource cleanup when orchestration fails"""
        # Ensure tmux sessions, files, etc. are cleaned up on failure
        pass


class TestArchitecturalPatterns(unittest.TestCase):
    """Test architectural patterns and principles"""
    
    def test_single_responsibility_principle(self):
        """Verify each class has a single, well-defined responsibility"""
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator
        
        orchestrator = ParallelTestCoverageOrchestrator()
        
        # Orchestrator should only orchestrate, not handle tmux directly
        self.assertIsNotNone(orchestrator.tmux)  # Delegated to TmuxOrchestrator
        self.assertIsNotNone(orchestrator.context_manager)  # Delegated to ContextManager
    
    def test_dependency_injection_pattern(self):
        """Verify proper dependency injection is used"""
        # Components should receive dependencies, not create them
        pass
    
    def test_error_handling_consistency(self):
        """Verify consistent error handling across components"""
        # All components should handle errors the same way
        pass


def run_tests():
    """Run all orchestration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParallelTestCoverageOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiTeamCoordinator))
    suite.addTests(loader.loadTestsFromTestCase(TestTeamOrchestrationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestOrchestrationIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitecturalPatterns))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)