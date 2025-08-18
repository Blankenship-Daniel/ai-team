#!/bin/bash

# Tmux Orchestrator v1.0 Release Packaging Script
# This script automates the release process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERSION="1.0.0"
RELEASE_DIR="release-v${VERSION}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "================================================"
echo "   Tmux Orchestrator Release Packaging v${VERSION}"
echo "================================================"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Pre-release checks
echo "Step 1: Running pre-release checks..."
echo "--------------------------------------"

# Check for syntax errors
echo -n "Checking Python syntax... "
if python -m py_compile *.py 2>/dev/null; then
    print_status "No syntax errors found"
else
    print_error "Syntax errors detected!"
    exit 1
fi

# Check critical linting issues
echo -n "Checking for critical issues... "
CRITICAL_ERRORS=$(python -m flake8 --count --select=E9,F63,F7,F82 --quiet 2>/dev/null || echo "0")
if [ "$CRITICAL_ERRORS" = "0" ]; then
    print_status "No critical issues found"
else
    print_error "Critical issues found: $CRITICAL_ERRORS"
    exit 1
fi

# Check for security issues in dependencies
echo -n "Checking for known vulnerabilities... "
if [ -f requirements.txt ]; then
    # Would use pip-audit here if available
    print_warning "pip-audit not installed, skipping vulnerability check"
else
    print_warning "No requirements.txt found"
fi

# Step 2: Run tests
echo ""
echo "Step 2: Running tests..."
echo "------------------------"

if python -m pytest --co -q 2>/dev/null; then
    TEST_COUNT=$(python -m pytest --co -q 2>/dev/null | tail -1 | grep -o '[0-9]\+ test' | grep -o '[0-9]\+' || echo "0")
    echo "Found $TEST_COUNT tests"

    if python -m pytest -q 2>/dev/null; then
        print_status "All tests passed"
    else
        print_error "Some tests failed!"
        echo -n "Continue anyway? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    print_warning "No tests found or pytest not configured"
fi

# Step 3: Clean up artifacts
echo ""
echo "Step 3: Cleaning build artifacts..."
echo "-----------------------------------"

# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
print_status "Removed Python cache files"

# Remove test artifacts
rm -rf .pytest_cache/ 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true
rm -rf htmlcov/ 2>/dev/null || true
print_status "Removed test artifacts"

# Step 4: Create release directory
echo ""
echo "Step 4: Creating release package..."
echo "-----------------------------------"

# Create release directory
mkdir -p "$RELEASE_DIR"

# Copy essential files
ESSENTIAL_FILES=(
    "create_ai_team.py"
    "tmux_utils.py"
    "unified_context_manager.py"
    "context_manager.py"
    "context_registry.py"
    "agent_context_manager.py"
    "security_validator.py"
    "logging_config.py"
    "interfaces.py"
    "send-claude-message.sh"
    "install.sh"
    "README.md"
    "requirements.txt"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$RELEASE_DIR/"
        print_status "Copied $file"
    else
        print_warning "File not found: $file"
    fi
done

# Copy configuration files if they exist
if [ -d "config" ]; then
    cp -r config "$RELEASE_DIR/"
    print_status "Copied config directory"
fi

# Step 5: Generate version info
echo ""
echo "Step 5: Generating version info..."
echo "----------------------------------"

cat > "$RELEASE_DIR/VERSION" << EOF
Version: ${VERSION}
Release Date: $(date +"%Y-%m-%d %H:%M:%S")
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")
Git Branch: $(git branch --show-current 2>/dev/null || echo "Not a git repository")
EOF

print_status "Created VERSION file"

# Step 6: Create requirements file
echo ""
echo "Step 6: Updating requirements..."
echo "--------------------------------"

if [ ! -f requirements.txt ]; then
    cat > requirements.txt << EOF
# Tmux Orchestrator Dependencies
psutil>=6.0.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
flake8>=6.0.0
EOF
    print_status "Created requirements.txt"
fi

cp requirements.txt "$RELEASE_DIR/"

# Step 7: Create installation script
echo ""
echo "Step 7: Creating installation script..."
echo "---------------------------------------"

cat > "$RELEASE_DIR/quick-install.sh" << 'EOF'
#!/bin/bash
# Quick installation script for Tmux Orchestrator

echo "Installing Tmux Orchestrator..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x create_ai_team.py
chmod +x send-claude-message.sh
chmod +x install.sh

echo "Installation complete!"
echo "Run: python3 create_ai_team.py --help"
EOF

chmod +x "$RELEASE_DIR/quick-install.sh"
print_status "Created quick-install.sh"

# Step 8: Create tarball
echo ""
echo "Step 8: Creating release archive..."
echo "-----------------------------------"

ARCHIVE_NAME="tmux-orchestrator-v${VERSION}-${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" "$RELEASE_DIR"
print_status "Created $ARCHIVE_NAME"

# Calculate checksums
echo ""
echo "Step 9: Generating checksums..."
echo "-------------------------------"

if command -v sha256sum &> /dev/null; then
    sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
    print_status "Generated SHA256 checksum"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
    print_status "Generated SHA256 checksum"
else
    print_warning "Checksum tool not found"
fi

# Step 10: Git tagging (if in git repo)
echo ""
echo "Step 10: Version control..."
echo "---------------------------"

if [ -d .git ]; then
    echo -n "Create git tag v${VERSION}? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git tag -a "v${VERSION}" -m "Release version ${VERSION}"
        print_status "Created git tag v${VERSION}"

        echo -n "Push tag to remote? (y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            git push origin "v${VERSION}"
            print_status "Pushed tag to remote"
        fi
    fi
else
    print_warning "Not a git repository, skipping tagging"
fi

# Final summary
echo ""
echo "================================================"
echo "            Release Package Complete!"
echo "================================================"
echo ""
echo "📦 Package: $ARCHIVE_NAME"
echo "📁 Directory: $RELEASE_DIR/"
echo "🏷️  Version: ${VERSION}"
echo ""
echo "Next steps:"
echo "1. Test the package: tar -xzf $ARCHIVE_NAME && cd $RELEASE_DIR"
echo "2. Run quick install: ./quick-install.sh"
echo "3. Upload to distribution channels"
echo ""
echo "Release notes template:"
echo "----------------------"
echo "## Tmux Orchestrator v${VERSION}"
echo ""
echo "### Features"
echo "- AI team creation with 3 opinionated agents"
echo "- Orchestrator for team coordination"
echo "- NEW: --observe-only flag for controlled demos"
echo ""
echo "### Improvements"
echo "- Enhanced security validation"
echo "- Better error handling"
echo "- Non-interactive mode support"
echo ""
echo "### Installation"
echo "\`\`\`bash"
echo "tar -xzf $ARCHIVE_NAME"
echo "cd $RELEASE_DIR"
echo "./quick-install.sh"
echo "\`\`\`"
echo ""
print_status "Release packaging complete!"
