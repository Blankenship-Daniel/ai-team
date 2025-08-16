#!/usr/bin/env python3
"""
Technical Debt Fixes
Addresses timestamp formatting and shell character escaping issues
"""

import re
import shlex
from pathlib import Path
from typing import List, Tuple
from logging_config import setup_logging

logger = setup_logging(__name__)


class TechnicalDebtFixer:
    """Systematic fixes for known technical debt issues"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = 0

    def fix_timestamp_formatting(self) -> int:
        """Fix timestamp formatting variable expansion issues"""
        fixes = 0

        # Pattern 1: Wrong timestamp formatting in shell heredocs
        timestamp_issues = [
            # Issue: $(date +%s%3N) should be $(date +%s%N | cut -c1-13) for milliseconds
            (r"\$\(date \+%s%3N\)", "$(date +%s%N | cut -c1-13)"),
            # Issue: Inconsistent timestamp formats
            (r'date -u \+"%Y-%m-%dT%H:%M:%S\.%3NZ"', 'date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"'),
        ]

        files_to_check = ["ai-team-connect.py", "unified_context_manager.py"]

        for file_name in files_to_check:
            file_path = self.project_root / file_name
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                original_content = content

                for pattern, replacement in timestamp_issues:
                    content = re.sub(pattern, replacement, content)
                    if content != original_content:
                        fixes += 1
                        logger.info(f"Fixed timestamp pattern in {file_name}: {pattern}")

                if content != original_content:
                    with open(file_path, "w") as f:
                        f.write(content)

            except Exception as e:
                logger.error(f"Failed to fix timestamps in {file_name}: {e}")

        return fixes

    def fix_shell_escaping(self) -> int:
        """Fix shell special character escaping in context injection"""
        fixes = 0

        # Files with shell injection vulnerabilities
        files_to_fix = ["ai-team-connect.py", "unified_context_manager.py"]

        for file_name in files_to_fix:
            file_path = self.project_root / file_name
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                original_content = content

                # Fix unescaped $MESSAGE in tmux send-keys
                content = self._fix_tmux_send_keys_escaping(content)

                # Fix unescaped variables in heredocs
                content = self._fix_heredoc_escaping(content)

                if content != original_content:
                    fixes += 1
                    with open(file_path, "w") as f:
                        f.write(content)
                    logger.info(f"Fixed shell escaping in {file_name}")

            except Exception as e:
                logger.error(f"Failed to fix shell escaping in {file_name}: {e}")

        return fixes

    def _fix_tmux_send_keys_escaping(self, content: str) -> str:
        """Fix tmux send-keys commands to properly escape variables"""

        # Pattern: tmux send-keys with unescaped $MESSAGE
        # Replace: tmux send-keys -t "target" "message with $MESSAGE"
        # With: tmux send-keys -t "target" "message with $(printf '%q' "$MESSAGE")"

        patterns = [
            # Fix: tmux send-keys with unescaped variables
            (
                r'tmux send-keys -t "([^"]+)" "([^"]*)\$MESSAGE([^"]*)" Enter',
                r'tmux send-keys -t "\1" "\2$(printf \'%q\' "$MESSAGE")\3" Enter',
            ),
            # Alternative pattern without Enter
            (
                r'tmux send-keys -t "([^"]+)" "([^"]*)\$MESSAGE([^"]*)"',
                r'tmux send-keys -t "\1" "\2$(printf \'%q\' "$MESSAGE")\3"',
            ),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        return content

    def _fix_heredoc_escaping(self, content: str) -> str:
        """Fix heredoc content to properly escape variables"""

        # In JSON heredocs, $MESSAGE should be properly escaped
        # But we need to be careful not to break legitimate JSON

        # Pattern: "message": "$MESSAGE" in JSON
        # This is actually OK in JSON context, but we should validate
        # that the MESSAGE variable is properly sanitized before use

        # The real fix is to ensure MESSAGE is sanitized before the script runs
        # Add sanitization at the top of scripts

        # Look for scripts that use $MESSAGE without sanitization
        if "$MESSAGE" in content and "MESSAGE=" in content:
            # Check if we already have sanitization
            if "printf" not in content and "shlex" not in content:
                # Add sanitization after MESSAGE assignment
                sanitization_code = """
# Sanitize message to prevent injection
MESSAGE=$(printf '%q' "$MESSAGE")
"""

                # Insert after first MESSAGE= assignment
                content = re.sub(r'(MESSAGE="[^"]*")\n', r"\1\n" + sanitization_code, content, count=1)

        return content

    def audit_timestamp_patterns(self) -> List[Tuple[str, str, str]]:
        """Audit all timestamp formatting patterns"""
        issues = []

        python_files = list(self.project_root.glob("*.py"))
        shell_scripts = list(self.project_root.glob("*.sh"))

        # Patterns that might be problematic
        problematic_patterns = [
            r"%3N",  # Wrong millisecond format
            r"strftime\([^)]*\)",  # Check strftime usage
            r'date \+[^"\']*["\']',  # Shell date commands
        ]

        for file_path in python_files + shell_scripts:
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern in problematic_patterns:
                        if re.search(pattern, line):
                            issues.append((str(file_path), str(line_num), line.strip()))

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return issues

    def test_shell_escaping(self) -> List[str]:
        """Test shell escaping with edge case characters"""
        test_cases = [
            "normal message",
            'message with "quotes"',
            "message with 'single quotes'",
            "message with $(command)",
            "message with `backticks`",
            "message with $VARIABLE",
            "message with \\ backslash",
            "message with ; semicolon",
            "message with | pipe",
            "message with & ampersand",
            "message with > redirect",
            "message with newline\nhere",
            "message with tab\there",
        ]

        failures = []

        for test_message in test_cases:
            try:
                # Test shlex.quote
                escaped = shlex.quote(test_message)

                # Test printf %q
                import subprocess

                result = subprocess.run(
                    ["bash", "-c", f'printf "%q" {escaped}'], capture_output=True, text=True, timeout=5
                )

                if result.returncode != 0:
                    failures.append(f"Printf failed for: {test_message}")

            except Exception as e:
                failures.append(f"Escaping test failed for '{test_message}': {e}")

        return failures

    def generate_fix_report(self) -> str:
        """Generate comprehensive fix report"""
        timestamp_fixes = self.fix_timestamp_formatting()
        shell_fixes = self.fix_shell_escaping()
        timestamp_audit = self.audit_timestamp_patterns()
        escaping_test_failures = self.test_shell_escaping()

        report = f"""
🔧 TECHNICAL DEBT FIX REPORT
============================

## Issues Fixed:
- Timestamp formatting: {timestamp_fixes} fixes applied
- Shell escaping: {shell_fixes} fixes applied

## Timestamp Audit Results:
Found {len(timestamp_audit)} potential timestamp issues:
"""

        for file_path, line_num, line in timestamp_audit[:5]:  # First 5
            report += f"- {file_path}:{line_num} - {line}\n"

        if len(timestamp_audit) > 5:
            report += f"... and {len(timestamp_audit) - 5} more\n"

        report += f"""
## Shell Escaping Test Results:
{len(escaping_test_failures)} test failures:
"""

        for failure in escaping_test_failures:
            report += f"- {failure}\n"

        report += f"""
## Recommendations:
1. Use SecurityValidator.sanitize_message() for all user input
2. Use shlex.quote() for shell command arguments
3. Use parameterized queries for any database operations
4. Standardize on ISO 8601 timestamps with timezone info
5. Add automated tests for special character handling

## Security Notes:
- All tmux send-keys operations should use -l flag for literal mode
- Context injection must sanitize variables before shell execution
- Consider using Python's subprocess with list arguments instead of shell=True
"""

        return report


def main():
    """Run technical debt fixes"""
    fixer = TechnicalDebtFixer()

    print("🔧 Running Technical Debt Fixes...")

    report = fixer.generate_fix_report()
    print(report)

    # Save report
    report_file = Path("technical_debt_report.txt")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n✅ Fix report saved to: {report_file}")


if __name__ == "__main__":
    main()
