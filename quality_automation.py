#!/usr/bin/env python3
"""
Quality Automation Suite for Tmux Orchestrator
Automated testing, coverage, linting, and security scanning
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from logging_config import setup_logging

logger = setup_logging(__name__)


class QualityAutomation:
    """Comprehensive quality automation system"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.reports_dir = self.project_root / "quality_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_full_quality_check(self) -> Dict[str, Any]:
        """Run comprehensive quality assessment"""
        logger.info("Starting full quality check")

        results = {"timestamp": datetime.now().isoformat(), "project_root": str(self.project_root), "checks": {}}

        # Run all quality checks
        checks = [
            ("test_coverage", self.check_test_coverage),
            ("code_style", self.check_code_style),
            ("security_scan", self.security_scan),
            ("dependency_check", self.check_dependencies),
            ("documentation", self.check_documentation),
            ("git_health", self.check_git_health),
        ]

        for check_name, check_func in checks:
            try:
                logger.info(f"Running {check_name}")
                results["checks"][check_name] = check_func()
            except Exception as e:
                logger.error(f"Check {check_name} failed: {e}")
                results["checks"][check_name] = {"status": "error", "error": str(e)}

        # Generate overall score
        results["overall_score"] = self._calculate_score(results["checks"])

        # Save report
        report_file = self.reports_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Quality report saved: {report_file}")
        return results

    def check_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        try:
            # First check if we have tests
            test_files = list(self.project_root.glob("test_*.py"))
            if not test_files:
                return {
                    "status": "warning",
                    "message": "No test files found",
                    "coverage": 0,
                    "recommendations": ["Add unit tests", "Create test_*.py files"],
                }

            # Run coverage if available
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "coverage", "run", "--source=.", "-m", "pytest"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    # Get coverage report
                    cov_result = subprocess.run(
                        [sys.executable, "-m", "coverage", "report", "--format=json"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                    )

                    if cov_result.returncode == 0:
                        coverage_data = json.loads(cov_result.stdout)
                        return {
                            "status": "success",
                            "coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                            "files_tested": len(coverage_data.get("files", {})),
                            "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0),
                        }
            except FileNotFoundError:
                # Try running tests without coverage
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "--tb=short"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                return {
                    "status": "partial",
                    "message": "Tests run but coverage not available",
                    "test_result": "passed" if result.returncode == 0 else "failed",
                    "recommendations": ["Install coverage: pip install coverage pytest"],
                }

            return {
                "status": "warning",
                "message": "Could not run tests",
                "recommendations": ["Check test configuration", "Install pytest"],
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_code_style(self) -> Dict[str, Any]:
        """Check code style and quality"""
        issues = []
        recommendations = []

        # Check for common style issues
        python_files = list(self.project_root.glob("*.py"))

        for file_path in python_files:
            try:
                with open(file_path) as f:
                    content = f.read()

                # Check for print statements (should use logging)
                if "print(" in content and str(file_path).endswith(".py"):
                    issues.append(f"{file_path.name}: Contains print() statements")

                # Check for TODO/FIXME comments
                for line_num, line in enumerate(content.splitlines(), 1):
                    if any(marker in line.upper() for marker in ["TODO", "FIXME", "HACK"]):
                        issues.append(f"{file_path.name}:{line_num}: {line.strip()}")

            except Exception as e:
                issues.append(f"{file_path.name}: Could not analyze - {e}")

        # Try running flake8 if available
        try:
            result = subprocess.run(
                ["flake8", "--max-line-length=100", "."], cwd=self.project_root, capture_output=True, text=True
            )

            if result.stdout:
                flake8_issues = result.stdout.strip().split("\n")
                issues.extend(flake8_issues)

        except FileNotFoundError:
            recommendations.append("Install flake8 for automated style checking")

        status = "success" if len(issues) == 0 else "warning" if len(issues) < 10 else "error"

        return {
            "status": status,
            "issues_count": len(issues),
            "issues": issues[:20],  # Limit to first 20
            "recommendations": recommendations,
            "files_checked": len(python_files),
        }

    def security_scan(self) -> Dict[str, Any]:
        """Basic security scanning"""
        issues = []
        recommendations = []

        # Check for common security issues
        python_files = list(self.project_root.glob("*.py"))

        dangerous_patterns = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("shell=True", "shell=True in subprocess calls is risky"),
            ("input(", "Unvalidated input() usage"),
            ("os.system(", "os.system() usage should be avoided"),
        ]

        for file_path in python_files:
            try:
                with open(file_path) as f:
                    content = f.read()
                    for pattern, message in dangerous_patterns:
                        if pattern in content:
                            issues.append(f"{file_path.name}: {message}")
            except Exception as e:
                issues.append(f"{file_path.name}: Could not scan - {e}")

        # Check for secrets in files
        secret_patterns = [
            ("password", "Possible hardcoded password"),
            ("secret", "Possible hardcoded secret"),
            ("token", "Possible hardcoded token"),
            ("api_key", "Possible hardcoded API key"),
        ]

        for file_path in python_files:
            try:
                with open(file_path) as f:
                    content = f.read().lower()
                    for pattern, message in secret_patterns:
                        if f"{pattern} =" in content or f'"{pattern}"' in content:
                            issues.append(f"{file_path.name}: {message}")
            except Exception:
                pass

        # Try bandit if available
        try:
            result = subprocess.run(
                ["bandit", "-r", ".", "-f", "json"], cwd=self.project_root, capture_output=True, text=True
            )

            if result.stdout:
                bandit_data = json.loads(result.stdout)
                bandit_issues = len(bandit_data.get("results", []))
                if bandit_issues > 0:
                    issues.append(f"Bandit found {bandit_issues} security issues")

        except (FileNotFoundError, json.JSONDecodeError):
            recommendations.append("Install bandit for automated security scanning")

        status = "success" if len(issues) == 0 else "warning" if len(issues) < 5 else "critical"

        return {"status": status, "issues_count": len(issues), "issues": issues, "recommendations": recommendations}

    def check_dependencies(self) -> Dict[str, Any]:
        """Check dependency health"""
        issues = []
        recommendations = []

        # Check for requirements files
        req_files = list(self.project_root.glob("requirements*.txt"))
        if not req_files:
            issues.append("No requirements.txt found")
            recommendations.append("Create requirements.txt for dependency management")

        # Try safety check if available
        try:
            result = subprocess.run(
                ["safety", "check", "--json"], cwd=self.project_root, capture_output=True, text=True
            )

            if result.stdout:
                safety_data = json.loads(result.stdout)
                if safety_data:
                    issues.extend([f"Security vulnerability: {vuln['advisory']}" for vuln in safety_data])

        except (FileNotFoundError, json.JSONDecodeError):
            recommendations.append("Install safety for dependency vulnerability scanning")

        return {
            "status": "success" if len(issues) == 0 else "warning",
            "issues": issues,
            "recommendations": recommendations,
            "requirements_files": [str(f) for f in req_files],
        }

    def check_documentation(self) -> Dict[str, Any]:
        """Check documentation completeness"""
        issues = []
        score = 0

        # Check for README
        readme_files = list(self.project_root.glob("README*"))
        if readme_files:
            score += 20
        else:
            issues.append("No README file found")

        # Check for docstrings in Python files
        python_files = list(self.project_root.glob("*.py"))
        documented_functions = 0
        total_functions = 0

        for file_path in python_files:
            try:
                with open(file_path) as f:
                    content = f.read()

                # Simple function detection
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if line.strip().startswith("def "):
                        total_functions += 1
                        # Check if next few lines contain docstring
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if '"""' in lines[j] or "'''" in lines[j]:
                                documented_functions += 1
                                break

            except Exception:
                pass

        if total_functions > 0:
            doc_percentage = (documented_functions / total_functions) * 100
            score += min(doc_percentage, 40)  # Max 40 points for docstrings

            if doc_percentage < 50:
                issues.append(f"Only {doc_percentage:.1f}% of functions have docstrings")

        # Check for inline comments
        comment_density = self._calculate_comment_density(python_files)
        score += min(comment_density * 40, 40)  # Max 40 points for comments

        return {
            "status": "success" if score > 70 else "warning" if score > 40 else "poor",
            "score": score,
            "issues": issues,
            "documentation_percentage": doc_percentage if total_functions > 0 else 0,
            "comment_density": comment_density,
        }

    def check_git_health(self) -> Dict[str, Any]:
        """Check git repository health"""
        issues = []

        if not (self.project_root / ".git").exists():
            return {"status": "warning", "message": "Not a git repository"}

        try:
            # Check for untracked files
            result = subprocess.run(
                ["git", "status", "--porcelain"], cwd=self.project_root, capture_output=True, text=True
            )

            if result.stdout:
                untracked = [line for line in result.stdout.splitlines() if line.startswith("??")]
                if untracked:
                    issues.append(f"{len(untracked)} untracked files")

            # Check for large files
            result = subprocess.run(["git", "ls-files"], cwd=self.project_root, capture_output=True, text=True)

            large_files = []
            if result.stdout:
                for filename in result.stdout.splitlines():
                    file_path = self.project_root / filename
                    if file_path.exists() and file_path.stat().st_size > 1024 * 1024:  # 1MB
                        large_files.append(filename)

            if large_files:
                issues.append(f"Large files in repo: {', '.join(large_files[:3])}")

            return {"status": "success" if len(issues) == 0 else "warning", "issues": issues}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _calculate_score(self, checks: Dict[str, Any]) -> int:
        """Calculate overall quality score"""
        scores = []
        weights = {
            "test_coverage": 30,
            "code_style": 20,
            "security_scan": 25,
            "dependency_check": 10,
            "documentation": 10,
            "git_health": 5,
        }

        for check_name, result in checks.items():
            weight = weights.get(check_name, 5)

            if result.get("status") == "success":
                scores.append(weight)
            elif result.get("status") == "warning":
                scores.append(weight * 0.6)
            elif result.get("status") == "partial":
                scores.append(weight * 0.8)
            else:
                scores.append(0)

        return int(sum(scores))

    def _calculate_comment_density(self, python_files: List[Path]) -> float:
        """Calculate comment density across Python files"""
        total_lines = 0
        comment_lines = 0

        for file_path in python_files:
            try:
                with open(file_path) as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    comment_lines += sum(1 for line in lines if line.strip().startswith("#"))
            except Exception:
                pass

        return comment_lines / total_lines if total_lines > 0 else 0


def main():
    """CLI entry point"""
    qa = QualityAutomation()
    results = qa.run_full_quality_check()

    print(f"\n🔍 Quality Report - Score: {results['overall_score']}/100")
    print("=" * 50)

    for check_name, result in results["checks"].items():
        status = result.get("status", "unknown")
        icon = {"success": "✅", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(status, "❓")
        print(f"{icon} {check_name.replace('_', ' ').title()}: {status}")

        if result.get("issues"):
            for issue in result["issues"][:3]:  # Show first 3 issues
                print(f"   • {issue}")


if __name__ == "__main__":
    main()
