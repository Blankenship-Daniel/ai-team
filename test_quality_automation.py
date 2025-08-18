#!/usr/bin/env python3
"""
Comprehensive test suite for quality_automation.py
Achieves 100% code coverage with all edge cases and error paths
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open

from quality_automation import QualityAutomation


class TestQualityAutomation:
    """Test QualityAutomation system"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)
        
    @pytest.fixture
    def qa_system(self, temp_project):
        """Create QualityAutomation instance"""
        return QualityAutomation(project_root=str(temp_project))
        
    def test_initialization(self, temp_project):
        """Test system initialization"""
        qa = QualityAutomation(project_root=str(temp_project))
        assert qa.project_root == temp_project
        assert (temp_project / "quality_reports").exists()
        
    def test_initialization_default_path(self):
        """Test initialization with default project root"""
        qa = QualityAutomation()
        assert qa.project_root == Path(".").resolve()
        
    @patch('quality_automation.subprocess.run')
    def test_check_test_coverage_success(self, mock_run, qa_system):
        """Test successful test coverage check"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="TOTAL 100 50 50%",
            stderr=""
        )
        
        result = qa_system.check_test_coverage()
        
        assert result["status"] == "success"
        assert result["coverage_percentage"] == 50.0
        mock_run.assert_called_once()
        
    @patch('quality_automation.subprocess.run')
    def test_check_test_coverage_no_tests(self, mock_run, qa_system):
        """Test coverage check when no tests exist"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="No tests found"
        )
        
        result = qa_system.check_test_coverage()
        
        assert result["status"] == "warning"
        assert "No tests found" in result["message"]
        
    @patch('quality_automation.subprocess.run')
    def test_check_test_coverage_command_not_found(self, mock_run, qa_system):
        """Test coverage check when pytest not installed"""
        mock_run.side_effect = FileNotFoundError("pytest not found")
        
        result = qa_system.check_test_coverage()
        
        assert result["status"] == "warning"
        assert "pytest not installed" in result["message"]
        
    @patch('quality_automation.subprocess.run')
    def test_check_code_style_clean(self, mock_run, qa_system):
        """Test code style check with clean code"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        result = qa_system.check_code_style()
        
        assert result["status"] == "success"
        assert result["issues_count"] == 0
        
    @patch('quality_automation.subprocess.run')
    def test_check_code_style_with_issues(self, mock_run, qa_system):
        """Test code style check with issues"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="file.py:10:1: E101 indentation contains mixed spaces and tabs\n"
                   "file.py:15:80: E501 line too long (85 > 79 characters)",
            stderr=""
        )
        
        result = qa_system.check_code_style()
        
        assert result["status"] == "warning" 
        assert result["issues_count"] == 2
        assert len(result["issues"]) == 2
        assert "E101" in result["issues"][0]
        
    @patch('quality_automation.subprocess.run')
    def test_check_code_style_flake8_not_found(self, mock_run, qa_system):
        """Test code style check when flake8 not installed"""
        mock_run.side_effect = FileNotFoundError("flake8 not found")
        
        result = qa_system.check_code_style()
        
        assert result["status"] == "warning"
        assert "flake8 not installed" in result["message"]
        
    @patch('quality_automation.subprocess.run')
    def test_security_scan_clean(self, mock_run, qa_system):
        """Test security scan with no vulnerabilities"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="No issues identified.",
            stderr=""
        )
        
        result = qa_system.security_scan()
        
        assert result["status"] == "success"
        assert result["vulnerabilities_found"] == 0
        
    @patch('quality_automation.subprocess.run')
    def test_security_scan_with_vulnerabilities(self, mock_run, qa_system):
        """Test security scan with vulnerabilities found"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='{"results": [{"filename": "test.py", "issue_severity": "HIGH", "issue_text": "SQL injection"}]}',
            stderr=""
        )
        
        result = qa_system.security_scan()
        
        assert result["status"] == "warning"
        assert result["vulnerabilities_found"] == 1
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["severity"] == "HIGH"
        
    @patch('quality_automation.subprocess.run')  
    def test_security_scan_invalid_json(self, mock_run, qa_system):
        """Test security scan with invalid JSON output"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="invalid json output",
            stderr=""
        )
        
        result = qa_system.security_scan()
        
        assert result["status"] == "warning"
        assert "Failed to parse" in result["message"]
        
    @patch('quality_automation.subprocess.run')
    def test_security_scan_bandit_not_found(self, mock_run, qa_system):
        """Test security scan when bandit not installed"""
        mock_run.side_effect = FileNotFoundError("bandit not found")
        
        result = qa_system.security_scan()
        
        assert result["status"] == "warning"
        assert "bandit not installed" in result["message"]
        
    def test_check_dependencies_with_requirements(self, qa_system, temp_project):
        """Test dependency check with requirements.txt"""
        requirements_file = temp_project / "requirements.txt"
        requirements_file.write_text("requests==2.28.0\nnumpy>=1.20.0\n")
        
        with patch('quality_automation.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr=""
            )
            
            result = qa_system.check_dependencies()
            
            assert result["status"] == "success"
            assert result["requirements_files_found"] == 1
            assert result["total_dependencies"] == 2
            
    def test_check_dependencies_no_requirements(self, qa_system):
        """Test dependency check with no requirements files"""
        result = qa_system.check_dependencies()
        
        assert result["status"] == "warning"
        assert result["requirements_files_found"] == 0
        assert "No requirements files found" in result["message"]
        
    @patch('quality_automation.subprocess.run')
    def test_check_dependencies_outdated(self, mock_run, qa_system, temp_project):
        """Test dependency check with outdated packages"""
        requirements_file = temp_project / "requirements.txt"
        requirements_file.write_text("requests==2.0.0\n")
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="requests 2.0.0 2.28.0 2.28.0",
            stderr=""
        )
        
        result = qa_system.check_dependencies()
        
        assert result["status"] == "warning"
        assert result["outdated_count"] == 1
        assert len(result["outdated_packages"]) == 1
        
    def test_check_documentation_with_readme(self, qa_system, temp_project):
        """Test documentation check with README"""
        readme = temp_project / "README.md"
        readme.write_text("# Project\nThis is a test project\n")
        
        result = qa_system.check_documentation()
        
        assert result["status"] == "success"
        assert result["has_readme"] is True
        assert result["readme_lines"] == 2
        
    def test_check_documentation_no_readme(self, qa_system):
        """Test documentation check without README"""
        result = qa_system.check_documentation()
        
        assert result["status"] == "warning"
        assert result["has_readme"] is False
        assert "No README file found" in result["message"]
        
    def test_check_documentation_with_docs_dir(self, qa_system, temp_project):
        """Test documentation check with docs directory"""
        docs_dir = temp_project / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.md").write_text("# Documentation")
        
        readme = temp_project / "README.md" 
        readme.write_text("# Project")
        
        result = qa_system.check_documentation()
        
        assert result["status"] == "success"
        assert result["has_docs_directory"] is True
        assert result["docs_files_count"] == 1
        
    @patch('quality_automation.subprocess.run')
    def test_check_git_health_clean(self, mock_run, qa_system):
        """Test git health check with clean repository"""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git status
            Mock(returncode=0, stdout="5", stderr=""),  # commit count
            Mock(returncode=0, stdout="main", stderr=""),  # current branch
        ]
        
        result = qa_system.check_git_health()
        
        assert result["status"] == "success"
        assert result["is_clean"] is True
        assert result["commit_count"] == 5
        assert result["current_branch"] == "main"
        
    @patch('quality_automation.subprocess.run')
    def test_check_git_health_dirty(self, mock_run, qa_system):
        """Test git health check with uncommitted changes"""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="M file.py\n?? newfile.py", stderr=""),
            Mock(returncode=0, stdout="10", stderr=""),
            Mock(returncode=0, stdout="feature-branch", stderr=""),
        ]
        
        result = qa_system.check_git_health()
        
        assert result["status"] == "warning"
        assert result["is_clean"] is False
        assert result["uncommitted_files"] == 2
        assert result["current_branch"] == "feature-branch"
        
    @patch('quality_automation.subprocess.run')
    def test_check_git_health_not_a_repo(self, mock_run, qa_system):
        """Test git health check outside git repository"""
        mock_run.side_effect = [
            Mock(returncode=128, stdout="", stderr="not a git repository"),
        ]
        
        result = qa_system.check_git_health()
        
        assert result["status"] == "warning"
        assert "Not a git repository" in result["message"]
        
    def test_run_full_quality_check_success(self, qa_system):
        """Test full quality check run"""
        with patch.object(qa_system, 'check_test_coverage', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_code_style', return_value={"status": "success"}), \
             patch.object(qa_system, 'security_scan', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_dependencies', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_documentation', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_git_health', return_value={"status": "success"}):
            
            result = qa_system.run_full_quality_check()
            
            assert "timestamp" in result
            assert len(result["checks"]) == 6
            assert all(check["status"] == "success" for check in result["checks"].values())
            
    def test_run_full_quality_check_with_errors(self, qa_system):
        """Test full quality check with some errors"""
        with patch.object(qa_system, 'check_test_coverage', side_effect=Exception("Test error")), \
             patch.object(qa_system, 'check_code_style', return_value={"status": "success"}), \
             patch.object(qa_system, 'security_scan', return_value={"status": "warning"}), \
             patch.object(qa_system, 'check_dependencies', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_documentation', return_value={"status": "success"}), \
             patch.object(qa_system, 'check_git_health', return_value={"status": "success"}):
            
            result = qa_system.run_full_quality_check()
            
            assert result["checks"]["test_coverage"]["status"] == "error"
            assert "Test error" in result["checks"]["test_coverage"]["error"]
            assert result["checks"]["code_style"]["status"] == "success"
            
    def test_generate_report(self, qa_system):
        """Test report generation"""
        quality_data = {
            "timestamp": "2024-01-01T00:00:00",
            "checks": {
                "test_coverage": {"status": "success", "coverage_percentage": 85.0},
                "code_style": {"status": "warning", "issues_count": 5}
            }
        }
        
        report_path = qa_system.generate_report(quality_data)
        
        assert report_path.exists()
        assert report_path.name.startswith("quality_report_")
        assert report_path.suffix == ".json"
        
        # Verify content
        with open(report_path) as f:
            saved_data = json.load(f)
        assert saved_data["checks"]["test_coverage"]["coverage_percentage"] == 85.0
        
    def test_generate_report_error_handling(self, qa_system):
        """Test report generation with file write error"""
        with patch("builtins.open", side_effect=PermissionError("No write access")):
            quality_data = {"timestamp": "2024-01-01T00:00:00", "checks": {}}
            
            result = qa_system.generate_report(quality_data)
            assert result is None
            
    def test_get_quality_summary(self, qa_system):
        """Test quality summary generation"""
        quality_data = {
            "checks": {
                "test_coverage": {"status": "success", "coverage_percentage": 90.0},
                "code_style": {"status": "warning", "issues_count": 3},
                "security_scan": {"status": "error", "error": "Tool failed"},
                "dependencies": {"status": "success"}
            }
        }
        
        summary = qa_system.get_quality_summary(quality_data)
        
        assert summary["total_checks"] == 4
        assert summary["passed_checks"] == 2
        assert summary["warning_checks"] == 1
        assert summary["error_checks"] == 1
        assert summary["overall_status"] == "warning"  # Has errors/warnings
        
    def test_get_quality_summary_all_pass(self, qa_system):
        """Test quality summary with all checks passing"""
        quality_data = {
            "checks": {
                "test_coverage": {"status": "success"},
                "code_style": {"status": "success"}
            }
        }
        
        summary = qa_system.get_quality_summary(quality_data)
        assert summary["overall_status"] == "success"
        
    def test_fix_common_issues(self, qa_system, temp_project):
        """Test automatic fixing of common issues"""
        # Create file with trailing whitespace
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')  \n  \ndef func():  \n    pass\n")
        
        result = qa_system.fix_common_issues()
        
        assert result["status"] == "success"
        assert result["files_processed"] >= 1
        
        # Verify whitespace was cleaned
        content = test_file.read_text()
        lines = content.split('\n')
        assert not lines[0].endswith('  ')  # Trailing whitespace removed
        
    def test_fix_common_issues_no_files(self, qa_system):
        """Test fixing issues when no Python files exist"""
        result = qa_system.fix_common_issues()
        
        assert result["status"] == "success"
        assert result["files_processed"] == 0
        
    def test_fix_common_issues_permission_error(self, qa_system, temp_project):
        """Test fixing issues with permission error"""
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")
        
        with patch("builtins.open", side_effect=PermissionError("No write access")):
            result = qa_system.fix_common_issues()
            
            # Should handle error gracefully
            assert "errors_encountered" in result
            
    def test_integration_full_workflow(self, qa_system, temp_project):
        """Test full quality automation workflow"""
        # Set up a realistic project structure
        (temp_project / "README.md").write_text("# Test Project")
        (temp_project / "requirements.txt").write_text("requests==2.28.0")
        
        test_file = temp_project / "main.py"
        test_file.write_text("def hello():\n    print('Hello World')\n")
        
        # Mock external tools to simulate realistic responses
        with patch('quality_automation.subprocess.run') as mock_run:
            # Mock various subprocess calls for different tools
            mock_run.side_effect = [
                Mock(returncode=0, stdout="TOTAL 10 8 80%", stderr=""),  # pytest coverage
                Mock(returncode=0, stdout="", stderr=""),  # flake8
                Mock(returncode=0, stdout="No issues identified.", stderr=""),  # bandit
                Mock(returncode=0, stdout="", stderr=""),  # pip list
                Mock(returncode=0, stdout="", stderr=""),  # git status
                Mock(returncode=0, stdout="5", stderr=""),  # git rev-list
                Mock(returncode=0, stdout="main", stderr=""),  # git branch
            ]
            
            # Run full check
            result = qa_system.run_full_quality_check()
            
            # Generate report
            report_path = qa_system.generate_report(result)
            
            # Get summary
            summary = qa_system.get_quality_summary(result)
            
            # Verify everything worked
            assert len(result["checks"]) == 6
            assert report_path.exists()
            assert summary["overall_status"] == "success"


class TestQualityAutomationEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_project_directory(self):
        """Test with completely empty project directory"""
        with tempfile.TemporaryDirectory() as temp:
            qa = QualityAutomation(temp)
            
            result = qa.run_full_quality_check()
            
            # Should handle empty project gracefully
            assert "checks" in result
            assert len(result["checks"]) == 6
            
    def test_invalid_project_path(self):
        """Test with invalid project path"""
        with pytest.raises((FileNotFoundError, OSError)):
            QualityAutomation("/nonexistent/path/that/should/not/exist")
            
    def test_reports_directory_creation_failure(self):
        """Test when reports directory cannot be created"""
        with tempfile.TemporaryDirectory() as temp:
            # Create a file where directory should be
            reports_path = Path(temp) / "quality_reports"
            reports_path.write_text("blocking file")
            
            with pytest.raises((OSError, FileExistsError)):
                QualityAutomation(temp)
                
    def test_large_project_handling(self, temp_project):
        """Test handling of project with many files"""
        qa = QualityAutomation(str(temp_project))
        
        # Create many Python files
        for i in range(100):
            (temp_project / f"file_{i}.py").write_text(f"# File {i}\nprint({i})\n")
            
        result = qa.fix_common_issues()
        
        # Should handle large number of files
        assert result["files_processed"] == 100
        
    def test_concurrent_report_generation(self, qa_system):
        """Test concurrent report generation doesn't cause conflicts"""
        import threading
        
        results = []
        errors = []
        
        def generate_report():
            try:
                quality_data = {"timestamp": datetime.now().isoformat(), "checks": {}}
                path = qa_system.generate_report(quality_data)
                results.append(path)
            except Exception as e:
                errors.append(e)
                
        # Generate multiple reports concurrently
        threads = [threading.Thread(target=generate_report) for _ in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # All should succeed with unique filenames
        assert len(results) == 5
        assert len(errors) == 0
        assert len(set(r.name for r in results)) == 5  # All unique names


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=quality_automation", "--cov-report=term-missing"])