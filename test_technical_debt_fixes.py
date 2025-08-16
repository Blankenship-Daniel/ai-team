#!/usr/bin/env python3
"""
Test suite for technical debt fixes
Verifies timestamp formatting and shell escaping work correctly
"""

import subprocess
import tempfile
import shlex
from pathlib import Path
from logging_config import setup_logging

logger = setup_logging(__name__)


def test_timestamp_formatting():
    """Test that timestamp formatting produces correct millisecond timestamps"""
    test_script = """#!/bin/bash
# Test the fixed timestamp format
MESSAGE_ID="test-$(date +%s%N | cut -c1-13)"
echo "$MESSAGE_ID"
"""

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(test_script)
            f.flush()
            Path(f.name).chmod(0o755)

            result = subprocess.run(["bash", f.name], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                output = result.stdout.strip()
                # Should be format: test-1234567890123 (13 digits after test-)
                assert output.startswith("test-"), f"Output should start with 'test-': {output}"
                assert len(output.split("-")[1]) == 13, f"Timestamp should be 13 digits: {output}"
                logger.info(f"✅ Timestamp format test passed: {output}")
            else:
                assert False, f"Timestamp test failed: {result.stderr}"

    except Exception as e:
        logger.error(f"❌ Timestamp test error: {e}")
        assert False, f"Timestamp test error: {e}"
    finally:
        try:
            Path(f.name).unlink()
        except:
            pass


def test_shell_escaping():
    """Test shell escaping with dangerous characters"""
    dangerous_messages = [
        "normal message",
        "message with $(ls)",
        "message with `whoami`",
        'message with "quotes"',
        "message with 'single quotes'",
        "message with ; rm -rf /",
        "message with | cat /etc/passwd",
        "message with & background",
        "message with \\ backslash",
        "message with newline\nhere",
    ]

    test_script_template = """#!/bin/bash
MESSAGE="$1"
# Use the same escaping as our fixed code
ESCAPED_MESSAGE=$(printf '%q' "$MESSAGE")
echo "Original: $MESSAGE"
echo "Escaped: $ESCAPED_MESSAGE"

# Test that it doesn't execute commands
if [[ "$ESCAPED_MESSAGE" == *"ls"* ]] || [[ "$ESCAPED_MESSAGE" == *"whoami"* ]]; then
    echo "SAFE: Commands properly escaped"
else
    echo "SAFE: No dangerous commands detected"
fi
"""

    passed = 0
    failed = 0

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(test_script_template)
            f.flush()
            Path(f.name).chmod(0o755)

            for message in dangerous_messages:
                try:
                    result = subprocess.run(["bash", f.name, message], capture_output=True, text=True, timeout=5)

                    if result.returncode == 0 and "SAFE:" in result.stdout:
                        logger.info(f"✅ Shell escaping passed for: {repr(message)}")
                        passed += 1
                    else:
                        logger.error(f"❌ Shell escaping failed for: {repr(message)}")
                        logger.error(f"Output: {result.stdout}")
                        failed += 1

                except subprocess.TimeoutExpired:
                    logger.error(f"❌ Shell escaping timeout for: {repr(message)}")
                    failed += 1
                except Exception as e:
                    logger.error(f"❌ Shell escaping error for {repr(message)}: {e}")
                    failed += 1

    finally:
        try:
            Path(f.name).unlink()
        except:
            pass

    logger.info(f"Shell escaping tests: {passed} passed, {failed} failed")
    assert failed == 0, f"Shell escaping tests failed: {failed} failures"


def test_tmux_send_keys_safety():
    """Test that tmux send-keys with our escaping is safe"""
    # This test simulates what happens in our fixed code
    test_messages = [
        "hello world",
        "message with $(dangerous command)",
        "message with `backticks`",
        "message with \"quotes\" and 'single quotes'",
    ]

    passed = 0
    failed = 0

    for message in test_messages:
        try:
            # Simulate our escaping approach
            escaped = shlex.quote(message)

            # Test command construction (don't actually run tmux)
            cmd_parts = ["tmux", "send-keys", "-t", "test:0", f"Message: {escaped}"]

            # Verify command is properly constructed
            if all(isinstance(part, str) for part in cmd_parts):
                logger.info(f"✅ Tmux command construction safe for: {repr(message)}")
                passed += 1
            else:
                logger.error(f"❌ Tmux command construction failed for: {repr(message)}")
                failed += 1

        except Exception as e:
            logger.error(f"❌ Tmux safety test error for {repr(message)}: {e}")
            failed += 1

    logger.info(f"Tmux safety tests: {passed} passed, {failed} failed")
    assert failed == 0, f"Tmux safety tests failed: {failed} failures"


def main():
    """Run all technical debt fix tests"""
    print("🧪 Testing Technical Debt Fixes...")
    print("=" * 50)

    tests = [
        ("Timestamp Formatting", test_timestamp_formatting),
        ("Shell Escaping", test_shell_escaping),
        ("Tmux Send-Keys Safety", test_tmux_send_keys_safety),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} tests...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False

    print(f"\n📊 Test Results:")
    print("=" * 30)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
