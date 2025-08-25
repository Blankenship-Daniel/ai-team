#!/bin/bash

# Context Manager Migration Script for v1.1
# Ensures smooth transition while Sam consolidates duplicate managers
# Maintains backward compatibility and allows rollback

set -e

VERSION="1.1.0"
BACKUP_DIR=".context-backup-$(date +%Y%m%d_%H%M%S)"

echo "========================================"
echo "Context Manager Migration Tool v${VERSION}"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print status
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Detect current context manager setup
echo "Step 1: Analyzing current context managers..."
echo "---------------------------------------------"

MANAGERS_FOUND=0
UNIFIED_EXISTS=false
AGENT_EXISTS=false
BASIC_EXISTS=false

if [ -f "unified_context_manager.py" ]; then
    UNIFIED_EXISTS=true
    ((MANAGERS_FOUND++))
    print_success "Found unified_context_manager.py"
fi

if [ -f "agent_context_manager.py" ]; then
    AGENT_EXISTS=true
    ((MANAGERS_FOUND++))
    print_success "Found agent_context_manager.py"
fi

if [ -f "context_manager.py" ]; then
    BASIC_EXISTS=true
    ((MANAGERS_FOUND++))
    print_success "Found context_manager.py"
fi

echo ""
echo "Total context managers found: $MANAGERS_FOUND"

if [ $MANAGERS_FOUND -eq 0 ]; then
    print_error "No context managers found. Nothing to migrate."
    exit 1
fi

# Step 2: Create backup
echo ""
echo "Step 2: Creating backup..."
echo "--------------------------"

mkdir -p "$BACKUP_DIR"

# Backup all context-related files
for file in *context*.py; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        print_success "Backed up $file"
    fi
done

# Backup imports that use context managers
echo ""
echo "Finding files that import context managers..."
IMPORT_FILES=$(grep -l "from.*context.*import\|import.*context" *.py 2>/dev/null || true)

if [ ! -z "$IMPORT_FILES" ]; then
    echo "$IMPORT_FILES" > "$BACKUP_DIR/files_with_imports.txt"
    print_success "Saved list of files with context imports"
fi

# Step 3: Create migration plan
echo ""
echo "Step 3: Creating migration plan..."
echo "----------------------------------"

cat > "$BACKUP_DIR/migration_plan.json" << EOF
{
  "version": "$VERSION",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "managers_found": $MANAGERS_FOUND,
  "unified_exists": $UNIFIED_EXISTS,
  "agent_exists": $AGENT_EXISTS,
  "basic_exists": $BASIC_EXISTS,
  "strategy": "consolidate_to_unified",
  "rollback_available": true
}
EOF

print_success "Migration plan created"

# Step 4: Create compatibility shim
echo ""
echo "Step 4: Creating compatibility shim..."
echo "--------------------------------------"

cat > context_manager_shim.py << 'EOF'
"""
Compatibility shim for v1.0 -> v1.1 context manager migration
This ensures existing code continues to work during the transition
"""

import warnings
from pathlib import Path

# Try to import the new unified manager
try:
    from unified_context_manager import UnifiedContextManager

    # Create compatibility aliases for old imports
    class ContextManager(UnifiedContextManager):
        """Backward compatibility for basic context_manager.py"""
        def __init__(self, *args, **kwargs):
            warnings.warn(
                "ContextManager is deprecated, use UnifiedContextManager",
                DeprecationWarning,
                stacklevel=2
            )
            super().__init__(*args, **kwargs)

    class AgentContextManager(UnifiedContextManager):
        """Backward compatibility for agent_context_manager.py"""
        def __init__(self, *args, **kwargs):
            warnings.warn(
                "AgentContextManager is deprecated, use UnifiedContextManager",
                DeprecationWarning,
                stacklevel=2
            )
            super().__init__(*args, **kwargs)

    print("✓ Context manager shim loaded - backward compatibility enabled")

except ImportError:
    # Fallback to original imports if unified doesn't exist yet
    try:
        from context_manager import ContextManager
    except ImportError:
        pass

    try:
        from agent_context_manager import AgentContextManager
    except ImportError:
        pass

    print("⚠ Using original context managers - migration pending")

# Export the appropriate manager
__all__ = ['UnifiedContextManager', 'ContextManager', 'AgentContextManager']
EOF

print_success "Compatibility shim created"

# Step 5: Create rollback script
echo ""
echo "Step 5: Creating rollback script..."
echo "-----------------------------------"

cat > rollback-context.sh << EOF
#!/bin/bash
# Rollback script for context manager migration

echo "Rolling back context manager changes..."

if [ -d "$BACKUP_DIR" ]; then
    cp $BACKUP_DIR/*.py .
    echo "✓ Context managers restored from backup"
    rm -f context_manager_shim.py
    echo "✓ Compatibility shim removed"
    echo "✓ Rollback complete"
else
    echo "✗ Backup directory not found: $BACKUP_DIR"
    exit 1
fi
EOF

chmod +x rollback-context.sh
print_success "Rollback script created: ./rollback-context.sh"

# Step 6: Update imports (dry run)
echo ""
echo "Step 6: Analyzing import updates needed..."
echo "------------------------------------------"

UPDATE_COUNT=0
if [ ! -z "$IMPORT_FILES" ]; then
    for file in $IMPORT_FILES; do
        if grep -q "from context_manager import\|from agent_context_manager import" "$file"; then
            ((UPDATE_COUNT++))
            print_warning "Will update imports in: $file"
        fi
    done
fi

echo ""
echo "Files needing import updates: $UPDATE_COUNT"

# Step 7: Create update script
cat > apply-migration.sh << 'EOF'
#!/bin/bash
# Apply the context manager migration

echo "Applying context manager migration..."

# Update imports to use shim
for file in *.py; do
    if [ -f "$file" ]; then
        # Skip the shim itself
        if [ "$file" != "context_manager_shim.py" ]; then
            # Replace old imports with shim import
            sed -i.bak 's/from context_manager import/from context_manager_shim import/g' "$file"
            sed -i.bak 's/from agent_context_manager import/from context_manager_shim import/g' "$file"
        fi
    fi
done

echo "✓ Imports updated to use compatibility shim"
echo ""
echo "Next steps for Sam:"
echo "1. Consolidate duplicate code into unified_context_manager.py"
echo "2. Test with: python -m pytest test_context*.py"
echo "3. Remove old managers when ready"
echo ""
echo "To rollback: ./rollback-context.sh"
EOF

chmod +x apply-migration.sh
print_success "Migration script created: ./apply-migration.sh"

# Final summary
echo ""
echo "========================================"
echo "Migration Preparation Complete!"
echo "========================================"
echo ""
echo "📋 Summary:"
echo "  • Found $MANAGERS_FOUND context managers"
echo "  • Created backup in $BACKUP_DIR"
echo "  • Generated compatibility shim"
echo "  • Prepared rollback capability"
echo ""
echo "🚀 To apply migration:"
echo "  ./apply-migration.sh"
echo ""
echo "↩️  To rollback if needed:"
echo "  ./rollback-context.sh"
echo ""
echo "👍 This keeps everything working while Sam consolidates!"
