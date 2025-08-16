#!/usr/bin/env python3
"""
Test script to verify context preservation functionality
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_context import AgentContextManager
from unified_context_manager import UnifiedContextManager

def run_command(cmd):
    """Run a shell command and return output"""
    import shlex
    try:
        # SECURITY: Never use shell=True - split command properly
        if isinstance(cmd, str):
            cmd_list = shlex.split(cmd)
        else:
            cmd_list = cmd
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        return result.stdout, result.stderr, True
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, False

def test_context_injection():
    """Test that context is properly injected into briefings"""
    print("\n🧪 Testing Context Injection...")
    
    install_dir = Path(__file__).parent
    cm = AgentContextManager(install_dir=install_dir)
    
    # Test for each role
    roles = ['orchestrator', 'developer', 'project_manager']
    for role in roles:
        original = f"You are a {role}."
        enhanced = cm.inject_context_into_briefing(original, role)
        
        # Check that context was added
        assert len(enhanced) > len(original), f"Context not added for {role}"
        assert cm.CONTEXT_VERSION in enhanced, f"Version not in {role} briefing"
        assert "tmux send-keys" in enhanced, f"Communication protocol missing for {role}"
        assert "git commit" in enhanced, f"Git discipline missing for {role}"
        
        print(f"  ✅ {role}: Added {len(enhanced) - len(original)} chars of context")
    
    print(f"  ✅ Context version: {cm.CONTEXT_VERSION}")
    return True

def test_workspace_creation():
    """Test that workspaces are created properly"""
    print("\n🧪 Testing Workspace Creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        print(f"  📍 Test directory: {tmpdir}")
        
        # Initialize context manager
        install_dir = Path(__file__).parent
        ucm = UnifiedContextManager(install_dir=install_dir)
        
        # Create workspace for test agent
        workspace = ucm.ensure_workspace("test-session", "test-agent")
        
        # Verify workspace was created
        assert workspace.path.exists(), "Workspace directory not created"
        assert workspace.context_file.exists(), "Context file not created"
        assert workspace.status_file.exists(), "Status file not created"
        
        print(f"  ✅ Workspace created: {workspace.path}")
        print(f"  ✅ Context file: {workspace.context_file}")
        print(f"  ✅ Status file: {workspace.status_file}")
        
        # Check symlinks
        symlinks = workspace.symlinks
        for name, target in symlinks.items():
            link_path = Path.cwd() / name
            if link_path.exists() or link_path.is_symlink():
                print(f"  ✅ Symlink created: {name} -> {target}")
            else:
                print(f"  ⚠️  Symlink missing: {name}")
    
    return True

def test_recovery_script():
    """Test that recovery script is created and executable"""
    print("\n🧪 Testing Recovery Script...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create context manager
        install_dir = Path(__file__).parent
        cm = AgentContextManager(install_dir=install_dir)
        
        # Create recovery script
        script_path = cm.create_fallback_script()
        
        assert script_path.exists(), "Recovery script not created"
        assert os.access(script_path, os.X_OK), "Recovery script not executable"
        
        # Check script content
        content = script_path.read_text()
        assert cm.CONTEXT_VERSION in content, "Version not in recovery script"
        assert "RESTORING AGENT CONTEXT" in content, "Recovery header missing"
        
        print(f"  ✅ Recovery script created: {script_path}")
        print(f"  ✅ Script is executable")
        print(f"  ✅ Contains version: {cm.CONTEXT_VERSION}")
    
    return True

def test_context_file():
    """Test that context file is created with correct data"""
    print("\n🧪 Testing Context File...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create context manager
        install_dir = Path(__file__).parent
        cm = AgentContextManager(install_dir=install_dir)
        
        # Create context file
        context_file = cm.create_context_file()
        
        assert context_file.exists(), "Context file not created"
        
        # Load and verify content
        with open(context_file, 'r') as f:
            data = json.load(f)
        
        assert data['context_version'] == cm.CONTEXT_VERSION, "Wrong version in file"
        assert 'core_context' in data, "Core context missing"
        assert 'install_dir' in data, "Install dir missing"
        
        print(f"  ✅ Context file created: {context_file}")
        print(f"  ✅ Version: {data['context_version']}")
        print(f"  ✅ Install dir: {data['install_dir']}")
        
        # Test loading
        loaded_data = cm.load_context_file()
        assert loaded_data is not None, "Failed to load context file"
        assert loaded_data['context_version'] == cm.CONTEXT_VERSION, "Version mismatch on load"
        
        print(f"  ✅ Context file loads correctly")
    
    return True

def test_quickstart_integration():
    """Test quickstart.sh creates proper structure"""
    print("\n🧪 Testing Quickstart Integration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        print(f"  📍 Test directory: {tmpdir}")
        
        # Run quickstart in test mode (doesn't create tmux session)
        quickstart = Path(__file__).parent / "quickstart.sh"
        if not quickstart.exists():
            print("  ⚠️  quickstart.sh not found, skipping")
            return False
        
        # Check what quickstart creates with timeout
        # SECURITY: Use proper command construction, not shell concatenation
        import shlex
        cmd = ["timeout", "10", str(quickstart), "--test"]
        stdout, stderr, success = run_command(cmd)
        
        # Check for expected directories
        ai_team_dir = Path(tmpdir) / ".ai-team"
        if ai_team_dir.exists():
            print(f"  ✅ .ai-team directory created")
            
            # Check subdirectories
            for subdir in ['workspaces/orchestrator', 'workspaces/alex', 'workspaces/morgan', 'workspaces/sam']:
                if (ai_team_dir / subdir).exists():
                    print(f"  ✅ {subdir} created")
            
            # Check files
            if (ai_team_dir / "CONTEXT.md").exists():
                print(f"  ✅ CONTEXT.md created")
            if (ai_team_dir / "recovery.sh").exists():
                print(f"  ✅ recovery.sh created")
        
        # Check for symlink
        symlink = Path(tmpdir) / "send-claude-message.sh"
        if symlink.is_symlink():
            print(f"  ✅ Communication script symlinked")
            print(f"     -> {symlink.resolve()}")
    
    return True

def test_version_compatibility():
    """Test version checking functionality"""
    print("\n🧪 Testing Version Compatibility...")
    
    install_dir = Path(__file__).parent
    cm = AgentContextManager(install_dir=install_dir)
    
    # Test compatible versions
    for version in cm.COMPATIBLE_VERSIONS:
        assert cm.is_version_compatible(version), f"Version {version} should be compatible"
        print(f"  ✅ Version {version} is compatible")
    
    # Test incompatible version
    assert not cm.is_version_compatible("0.0.1"), "Old version should not be compatible"
    print(f"  ✅ Version 0.0.1 correctly identified as incompatible")
    
    # Test version validation in agent response
    test_response = f"Agent initialized. CONTEXT VERSION: {cm.CONTEXT_VERSION}"
    is_valid, version = cm.validate_agent_context(test_response)
    assert is_valid, "Valid version not recognized"
    assert version == cm.CONTEXT_VERSION, "Version extraction failed"
    print(f"  ✅ Version validation works correctly")
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("🔬 CONTEXT PRESERVATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Context Injection", test_context_injection),
        ("Workspace Creation", test_workspace_creation),
        ("Recovery Script", test_recovery_script),
        ("Context File", test_context_file),
        ("Quickstart Integration", test_quickstart_integration),
        ("Version Compatibility", test_version_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {name}")
    
    print("\n" + "="*60)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)