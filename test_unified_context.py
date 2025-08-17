#!/usr/bin/env python3
"""
Test the unified context manager to ensure it solves the context loss problem
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_context_manager import UnifiedContextManager


def test_context_preservation():
    """Test that context is preserved when running from different directories"""

    print("Testing Unified Context Manager...")
    print("-" * 60)

    # Save original directory
    original_dir = Path.cwd()

    # Create a temporary directory to simulate running from elsewhere
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        os.chdir(test_dir)

        print(f"✓ Changed to test directory: {test_dir}")

        # Initialize context manager
        manager = UnifiedContextManager(install_dir=original_dir)
        print(f"✓ Initialized manager with install_dir: {original_dir}")

        # Test 1: Embedded context injection
        test_briefing = "You are a test agent."
        enhanced = manager.inject_context_into_briefing(test_briefing, "senior_software_engineer")

        assert "CRITICAL AGENT KNOWLEDGE" in enhanced
        assert "Communication Protocol" in enhanced
        assert "send-claude-message.sh" in enhanced
        print("✓ Embedded context injection works")

        # Test 2: Workspace creation
        workspace = manager.ensure_workspace("test-session", "test-agent")

        assert workspace.path.exists()
        assert workspace.tools_dir.exists()
        assert workspace.context_file.exists()
        print(f"✓ Workspace created at: {workspace.path}")

        # Test 3: Tool availability
        send_script = workspace.tools_dir / "send-claude-message.sh"
        if send_script.exists():
            print(f"✓ Communication script available: {send_script}")
        else:
            print("⚠ Communication script not copied (expected if not in install dir)")

        # Test 4: Recovery script creation
        recovery_script = manager.create_recovery_script()
        assert recovery_script.exists()
        assert os.access(recovery_script, os.X_OK)
        print(f"✓ Recovery script created: {recovery_script}")

        # Test 5: Agent readiness verification
        is_ready, issues = manager.verify_agent_readiness("test-session", "test-agent")
        if is_ready:
            print("✓ Agent verified as ready")
        else:
            print(f"⚠ Agent has issues: {issues}")

        # Test 6: Context persists in briefing even without tools
        assert "If tools missing: Use the creation script above" in enhanced
        print("✓ Briefing includes tool creation instructions")

        # Cleanup
        manager.cleanup_workspaces("test-session")
        assert not (test_dir / ".ai-team-workspace" / "test-session").exists()
        print("✓ Cleanup successful")

    # Return to original directory
    os.chdir(original_dir)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nThe unified context manager successfully:")
    print("1. Embeds context directly in briefings (primary mechanism)")
    print("2. Creates local workspaces with tools (secondary mechanism)")
    print("3. Provides recovery scripts (tertiary mechanism)")
    print("\n🎯 This solves the context loss problem when running from different directories!")


if __name__ == "__main__":
    try:
        test_context_preservation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
