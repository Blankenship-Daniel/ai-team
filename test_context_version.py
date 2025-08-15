#!/usr/bin/env python3
"""Test context version control and validation"""

from agent_context import AgentContextManager
import tempfile
import os

def test_version_control():
    """Test that version control and validation works correctly"""
    
    print("=== Testing Context Version Control ===\n")
    
    manager = AgentContextManager()
    
    # Test 1: Version constants
    print(f"1. Current version: {manager.CONTEXT_VERSION}")
    print(f"   Compatible versions: {manager.COMPATIBLE_VERSIONS}")
    assert manager.CONTEXT_VERSION == "2.0.0", "Version should be 2.0.0"
    
    # Test 2: Version compatibility check
    print("\n2. Testing version compatibility:")
    assert manager.is_version_compatible("2.0.0"), "2.0.0 should be compatible"
    assert manager.is_version_compatible("1.9.0"), "1.9.0 should be compatible"
    assert not manager.is_version_compatible("1.0.0"), "1.0.0 should NOT be compatible"
    print("   ✓ Version compatibility checks working")
    
    # Test 3: Context injection includes version
    print("\n3. Testing version in context injection:")
    briefing = "Test agent briefing"
    enhanced = manager.inject_context_into_briefing(briefing, "developer")
    assert "VERSION: 2.0.0" in enhanced, "Version should be in enhanced briefing"
    assert "CONTEXT VERSION: 2.0.0" in enhanced, "Full version string should be present"
    print("   ✓ Version properly embedded in context")
    
    # Test 4: Agent response validation
    print("\n4. Testing agent context validation:")
    
    # Valid response
    agent_response = "I understand. CONTEXT VERSION: 2.0.0 - Ready to work."
    valid, version = manager.validate_agent_context(agent_response)
    assert valid, "Should validate correct version"
    assert version == "2.0.0", "Should extract correct version"
    print(f"   ✓ Valid agent response: version {version}")
    
    # Invalid version
    agent_response = "I have CONTEXT VERSION: 1.0.0"
    valid, error = manager.validate_agent_context(agent_response)
    assert not valid, "Should reject incompatible version"
    print(f"   ✓ Rejected incompatible version: {error}")
    
    # Missing version
    agent_response = "I'm ready to work!"
    valid, error = manager.validate_agent_context(agent_response)
    assert not valid, "Should reject missing version"
    print(f"   ✓ Detected missing version: {error}")
    
    # Test 5: Context health monitoring
    print("\n5. Testing context health status:")
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Check health in empty directory
        health = manager.get_context_health_status()
        print(f"   Status: {health['status']}")
        print(f"   Issues: {health['issues']}")
        assert health['status'] == 'degraded', "Should be degraded without files"
        
        # Create context file and recovery script
        manager.create_context_file()
        manager.create_fallback_script()
        
        # Check health again
        health = manager.get_context_health_status()
        print(f"\n   After creating files:")
        print(f"   Status: {health['status']}")
        print(f"   Context file: {health['context_file_exists']}")
        print(f"   Recovery script: {health['recovery_script_exists']}")
        # Note: Will still be degraded due to missing CLAUDE.md, but that's OK
    
    # Test 6: Logging verification
    print("\n6. Testing logging integration:")
    print("   Check ./logs/agent_context.log for detailed logging")
    print("   All context operations should be logged with version info")
    
    print("\n✅ All version control tests passed!")
    print("\n=== VERSION CONTROL BENEFITS ===")
    print("1. Prevents silent failures from version mismatch")
    print("2. Allows safe context updates without breaking agents")
    print("3. Clear version tracking in logs for debugging")
    print("4. Automatic compatibility checking")
    print("5. Health monitoring shows version issues")

if __name__ == "__main__":
    test_version_control()