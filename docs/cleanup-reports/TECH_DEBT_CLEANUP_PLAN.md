# Technical Debt Cleanup Plan
*Generated: August 25, 2025*

## Executive Summary
Found significant technical debt and obsolete artifacts that need cleanup:
- **34 test files** (many duplicates/stubs)
- **27 markdown files** (many obsolete migration docs)
- **19 shell scripts** (several duplicates)
- **4 archive files** (.tar.gz releases)
- **Duplicate CLI tools** (ai-bridge vs ai-bridge-old)
- **Coverage artifacts** (htmlcov directory)
- **Old release directory** (release-v1.0.0)

## Priority 1: Archive Files (Immediate Removal)
These files are taking up space and serve no purpose:
```bash
# Archive files to remove:
./tmux-orchestrator-v1.0.0-20250817_221809.tar.gz
./tmux-orchestrator-v1.0.0-20250817_221756.tar.gz
./tmux-orchestrator-v1.0.0-20250817_221809.tar.gz.sha256
./tmux-orchestrator-v1.0.0-20250817_221756.tar.gz.sha256
```

## Priority 2: Test File Consolidation
Found multiple test file patterns that need cleanup:
```bash
# Stub/MVP test files to remove:
./test_bridge_registry_fixed.py
./test_bridge_registry_mvp.py
./test_chaos_prevention_fixed.py
./test_coverage_boost_mvp.py
./test_orchestration_stubs.py

# Redundant test files (34 total test_*.py files):
./test_100_percent_machine.py
./test_final_coverage_push.py
./test_final_coverage_sprint.py
./test_hit_lines_only.py
./test_implementations_fast.py
./test_line_coverage_focused.py
./test_line_hitters.py
./test_line_hitters_simple.py
./test_maximum_coverage.py
```

## Priority 3: Duplicate CLI Tools
```bash
# Obsolete tools to remove:
./ai-bridge-old  # Old version, replaced by ai-bridge
./migration-stub.sh  # Migration complete
```

## Priority 4: Old Documentation
```bash
# Obsolete migration docs to archive:
./BRIDGE_MIGRATION.md  # Superseded by BRIDGE_MIGRATION_FINAL.md
./BRIDGE_MIGRATION_FINAL.md  # Migration complete
./UX_MIGRATION_TEST_REPORT.md  # Old test report
./USER_MIGRATION_GUIDE.md  # Migration complete
./v1.1_CONSOLIDATION_COMPLETE.md  # Old release notes
./DEPRECATED_SYSTEMS.md  # Should be archived
```

## Priority 5: Coverage Artifacts
```bash
# Remove entire htmlcov directory (regenerated on test runs)
./htmlcov/  # Contains 50+ HTML files
```

## Priority 6: Release Directory
```bash
# Old release directory (code already in main):
./release-v1.0.0/  # Contains duplicate files from v1.0.0
```

## Priority 7: Obsolete Scripts
```bash
# Check and potentially remove:
./verify_context_solution.sh  # One-time verification
./setup_quality_automation.sh  # Setup already done
./parallel_performance_demo.sh  # Demo script
./test_observe_only.sh  # Old test script
./package-release.sh  # If using different release process
```

## Priority 8: Log Files
```bash
# Clean or rotate logs in ./logs/ directory
# 40+ log files that should be rotated/archived
```

## Cleanup Commands

### Step 1: Backup before cleanup
```bash
mkdir -p .archive/tech-debt-cleanup-2025-08-25
cp -r release-v1.0.0 .archive/tech-debt-cleanup-2025-08-25/
cp *.tar.gz* .archive/tech-debt-cleanup-2025-08-25/
```

### Step 2: Remove archive files
```bash
rm -f *.tar.gz *.tar.gz.sha256
```

### Step 3: Remove test stubs
```bash
rm -f test_*_fixed.py test_*_mvp.py test_orchestration_stubs.py
rm -f test_100_percent_machine.py test_final_coverage_*.py
rm -f test_hit_lines_only.py test_line_hitters*.py test_maximum_coverage.py
```

### Step 4: Remove old CLI tools
```bash
rm -f ai-bridge-old migration-stub.sh
```

### Step 5: Archive old documentation
```bash
mkdir -p docs/archive/migration
mv BRIDGE_MIGRATION*.md docs/archive/migration/
mv UX_MIGRATION_TEST_REPORT.md docs/archive/migration/
mv USER_MIGRATION_GUIDE.md docs/archive/migration/
mv DEPRECATED_SYSTEMS.md docs/archive/
```

### Step 6: Clean coverage artifacts
```bash
rm -rf htmlcov/
```

### Step 7: Remove old release directory
```bash
rm -rf release-v1.0.0/
```

## Expected Impact
- **Disk space saved**: ~50MB
- **File count reduction**: ~150 files
- **Improved clarity**: Removes confusion from duplicate files
- **Better maintainability**: Clear separation of active vs archived code

## Verification After Cleanup
```bash
# Verify tests still pass
pytest

# Check for broken imports
python verify_imports.py

# Ensure core functionality works
./ai-team --help
```