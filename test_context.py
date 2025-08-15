#!/usr/bin/env python3
"""Test that agent context works across different directories"""

from pathlib import Path
from agent_context import AgentContextManager
import tempfile
import os

def test_context_embedding():
    """Test that context is properly embedded"""
    
    print("=== Testing Agent Context Management ===\n")
    
    # Initialize context manager
    manager = AgentContextManager()
    
    # Test 1: Build context for different roles
    print("1. Testing role-specific context building:")
    for role in ["orchestrator", "project_manager", "developer"]:
        context = manager.build_agent_context(role)
        print(f"   {role}: {len(context)} characters of context")
        assert "Git Discipline" in context, f"Missing core context for {role}"
        assert "Communication Protocol" in context, f"Missing communication info for {role}"
    
    # Test 2: Inject context into briefing
    print("\n2. Testing context injection:")
    original = "You are a test agent."
    enhanced = manager.inject_context_into_briefing(original, "developer")
    print(f"   Original: {len(original)} chars")
    print(f"   Enhanced: {len(enhanced)} chars")
    assert len(enhanced) > len(original) * 10, "Context not properly injected"
    
    # Test 3: Create context files in temp directory
    print("\n3. Testing context file creation:")
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create context file
        context_file = manager.create_context_file()
        assert context_file.exists(), "Context file not created"
        print(f"   ✓ Created: {context_file}")
        
        # Create fallback script
        script = manager.create_fallback_script()
        assert script.exists(), "Fallback script not created"
        print(f"   ✓ Created: {script}")
        
        # Test loading context
        loaded = AgentContextManager.load_context_file()
        assert loaded is not None, "Could not load context file"
        assert "core_context" in loaded, "Missing core context in file"
        print(f"   ✓ Loaded context successfully")
    
    print("\n✅ All context tests passed!")
    print("\nSolution Benefits:")
    print("1. Context embedded directly in agent briefings")
    print("2. No dependency on external CLAUDE.md location")
    print("3. Fallback script for context recovery")
    print("4. Context file for persistence (.tmux-orchestrator-context)")
    print("5. Works from ANY directory")

if __name__ == "__main__":
    test_context_embedding()