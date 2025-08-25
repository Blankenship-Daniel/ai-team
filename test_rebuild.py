#!/usr/bin/env python3
"""
Test script to verify the package rebuild
"""

print("=" * 60)
print("Testing AI Team Package Rebuild")
print("=" * 60)

# Test 1: Package imports
print("\n1. Testing package imports...")
try:
    from ai_team import UnifiedContextManager, TmuxOrchestrator, AgentProfileFactory
    print("   ✅ Main imports successful")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    exit(1)

# Test 2: Core module imports
print("\n2. Testing core module imports...")
try:
    from ai_team.core.interfaces import AgentProfile, SessionInfo
    from ai_team.core.context_registry import ContextRegistry
    from ai_team.core.dependency_container import DependencyContainer
    print("   ✅ Core modules import successful")
except ImportError as e:
    print(f"   ❌ Core module error: {e}")
    exit(1)

# Test 3: Utils module imports
print("\n3. Testing utils module imports...")
try:
    from ai_team.utils.security_validator import SecurityValidator
    from ai_team.utils.logging_config import setup_logging
    from ai_team.utils.chaos_prevention import CircuitBreaker
    print("   ✅ Utils modules import successful")
except ImportError as e:
    print(f"   ❌ Utils module error: {e}")
    exit(1)

# Test 4: CLI module import
print("\n4. Testing CLI module imports...")
try:
    from ai_team.cli.main import main
    print("   ✅ CLI module import successful")
except ImportError as e:
    print(f"   ❌ CLI module error: {e}")
    exit(1)

# Test 5: Create instances
print("\n5. Testing object creation...")
try:
    # Create instances
    orchestrator = TmuxOrchestrator(enable_context_registry=False)
    context_mgr = UnifiedContextManager()
    factory = AgentProfileFactory()
    validator = SecurityValidator()
    
    print("   ✅ Object instantiation successful")
except Exception as e:
    print(f"   ❌ Object creation error: {e}")
    exit(1)

# Test 6: Basic functionality
print("\n6. Testing basic functionality...")
try:
    # Test agent profile creation
    profiles = factory.create_default_profiles(working_dir="/tmp/test")
    assert len(profiles) == 3, "Should create 3 default profiles"
    profile_names = [p.name for p in profiles]
    assert any("Alex" in name for name in profile_names), f"Alex should be in profiles, got: {profile_names}"
    
    # Test security validation
    valid, _ = validator.validate_session_name("test-session")
    assert valid == True, "Valid session name should pass"
    valid, _ = validator.validate_session_name("../../etc/passwd")
    assert valid == False, "Invalid session name should fail"
    
    print("   ✅ Basic functionality working")
except Exception as e:
    print(f"   ❌ Functionality error: {e}")
    exit(1)

# Test 7: Check tmux availability
print("\n7. Checking tmux availability...")
import subprocess
try:
    result = subprocess.run(["tmux", "-V"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Tmux available: {result.stdout.strip()}")
    else:
        print("   ⚠️  Tmux not available (optional)")
except FileNotFoundError:
    print("   ⚠️  Tmux not installed (optional)")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Package rebuild successful!")
print("=" * 60)
print("\nPackage structure verified:")
print("  • ai_team package installed")
print("  • All modules import correctly")
print("  • Core functionality working")
print("  • CLI accessible")
print("\nYou can now use:")
print("  • Python: from ai_team import ...")
print("  • CLI: ai-team --help")
print("=" * 60)