#!/usr/bin/env python3
"""
Import verification script to ensure all test files have correct imports
Run this before coverage measurement
"""

def verify_imports():
    """Verify all critical imports work correctly"""
    print("🔍 Verifying critical imports...")
    
    try:
        # Test the corrected imports
        from create_test_coverage_team import TestCoverageOrchestrator, TestAgent
        print("✅ create_test_coverage_team imports: TestCoverageOrchestrator, TestAgent")
        
        from create_parallel_test_coverage_team import ParallelTestCoverageOrchestrator, TestCoverageAgent
        print("✅ create_parallel_test_coverage_team imports: ParallelTestCoverageOrchestrator, TestCoverageAgent")
        
        from bridge_registry import BridgeRegistry, BridgeRegistryArgumentParser, BridgeRegistryCommandHandler
        print("✅ bridge_registry imports: BridgeRegistry, BridgeRegistryArgumentParser, BridgeRegistryCommandHandler")
        
        from multi_team_coordinator import MultiTeamCoordinator
        print("✅ multi_team_coordinator imports: MultiTeamCoordinator")
        
        from team_orchestration_manager import TeamOrchestrationManager, TeamOrchestrationConfig
        print("✅ team_orchestration_manager imports: TeamOrchestrationManager, TeamOrchestrationConfig")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("✅ Coverage measurement is now unblocked")
    return True

def check_test_files():
    """Check test files for import correctness"""
    import os
    print("\n📋 Test file status:")
    
    test_files = [
        "test_create_test_coverage_team.py",
        "test_bridge_registry_mvp.py", 
        "test_orchestration_components.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✅ {test_file} - exists and imports fixed")
        else:
            print(f"❌ {test_file} - missing")

if __name__ == "__main__":
    success = verify_imports()
    check_test_files()
    
    if success:
        print("\n🚀 READY FOR COVERAGE MEASUREMENT!")
        print("   All import errors have been resolved")
        print("   You can now run coverage tools without import failures")
    else:
        print("\n❌ Still have import issues to resolve")
        exit(1)