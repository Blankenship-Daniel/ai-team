#!/bin/bash
# AI Team CLI Enhanced Installation Script
# Completely removes any existing installation and reinstalls with all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.local/bin"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND_NAME="ai-team"
BACKUP_DIR="$HOME/.ai-team-backup"
LOG_FILE="$HOME/.ai-team-install.log"
MANIFEST_FILE="$INSTALL_DIR/.ai-team-manifest.json"

# Flags
DRY_RUN=false
VERIFY_ONLY=false
UNINSTALL_ONLY=false
VERBOSE=false
SKIP_DEPS=false

# Comprehensive file lists (ALL dependencies mapped correctly)
CORE_PYTHON_FILES=(
    "create_ai_team.py"
    "tmux_utils.py"
    "security_validator.py"
    "logging_config.py"
    "unified_context_manager.py" 
    "interfaces.py"
    "context_registry.py"  # This was the missing dependency!
    "bridge_registry.py"   # Required for ai-bridge send-to-peer functionality
)

SHELL_SCRIPTS=(
    "ai-team"
    "ai-bridge"
    "ai-bridge-old"
    "send-claude-message.sh"
    "send-to-peer.sh"
    "schedule_with_note.sh"
    "check-peer-messages.sh"
    "context-status.sh"
)

DIRECTORIES=(
    "implementations"
)

DOCUMENTATION=(
    "ORCHESTRATOR_GUIDE.md"
)

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verify)
                VERIFY_ONLY=true
                shift
                ;;
            --uninstall)
                UNINSTALL_ONLY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
AI Team CLI Enhanced Installation Script

Usage: $0 [options]

Options:
    --dry-run      Show what would be done without making changes
    --verify       Test existing installation without modifying
    --uninstall    Remove existing installation only (no reinstall)
    --verbose, -v  Enable detailed logging output
    --skip-deps    Skip system dependency checks (tmux, claude, jq)
    --help, -h     Show this help message

Examples:
    $0                    # Full install (removes existing first)
    $0 --dry-run          # Preview what would be installed
    $0 --verify           # Test current installation
    $0 --uninstall        # Remove installation only
    $0 --verbose          # Detailed output

EOF
}

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $*" >> "$LOG_FILE"
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[LOG]${NC} $*"
    fi
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): ERROR: $*" >> "$LOG_FILE"
    echo -e "${RED}❌ ERROR: $*${NC}"
}

warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): WARNING: $*" >> "$LOG_FILE"
    echo -e "${YELLOW}⚠️  WARNING: $*${NC}"
}

success() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): SUCCESS: $*" >> "$LOG_FILE"
    echo -e "${GREEN}✓ $*${NC}"
}

info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): INFO: $*" >> "$LOG_FILE"
    echo -e "${BLUE}ℹ️  $*${NC}"
}

progress() {
    echo -e "${PURPLE}🔄 $*${NC}"
}

# Trap handler for cleanup on interruption
cleanup_on_exit() {
    if [[ $? -ne 0 ]]; then
        error "Installation interrupted or failed"
        if [[ -f "$BACKUP_DIR/.ai-team-backup.tar.gz" ]]; then
            warning "Backup available at: $BACKUP_DIR/.ai-team-backup.tar.gz"
            echo -e "${YELLOW}To restore: tar -xzf $BACKUP_DIR/.ai-team-backup.tar.gz -C $INSTALL_DIR${NC}"
        fi
    fi
}

trap cleanup_on_exit EXIT

# System dependency checks
check_system_dependencies() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        info "Skipping system dependency checks"
        return 0
    fi

    progress "Checking system dependencies..."
    
    local missing_deps=()

    # Check tmux
    if ! command -v tmux &> /dev/null; then
        missing_deps+=("tmux")
    else
        success "tmux found: $(tmux -V)"
    fi

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        success "Python found: $(python3 --version)"
    fi

    # Check jq (required for bridge messaging)
    if ! command -v jq &> /dev/null; then
        warning "jq not found - bridge messaging may not work"
        echo "Install: brew install jq (macOS) or apt install jq (Ubuntu)"
    else
        success "jq found: $(jq --version)"
    fi

    # Check Claude CLI (optional but recommended)
    if ! command -v claude &> /dev/null; then
        warning "Claude CLI not found - AI agents won't work without it"
        echo "The AI team requires Claude CLI to function"
    else
        success "Claude CLI found"
        info "Note: All Claude instances will start with --dangerously-skip-permissions"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Missing required dependencies: ${missing_deps[*]}"
        echo "Please install missing dependencies and try again:"
        echo "  macOS: brew install ${missing_deps[*]}"
        echo "  Ubuntu/Debian: sudo apt install ${missing_deps[*]}"
        echo "  CentOS/RHEL: sudo yum install ${missing_deps[*]}"
        return 1
    fi

    return 0
}

# Validate source files exist
validate_source_files() {
    progress "Validating source files..."
    local missing_files=()

    # Check core Python files
    for file in "${CORE_PYTHON_FILES[@]}"; do
        if [[ ! -f "$SOURCE_DIR/$file" ]]; then
            missing_files+=("$file")
        fi
    done

    # Check shell scripts  
    for file in "${SHELL_SCRIPTS[@]}"; do
        if [[ ! -f "$SOURCE_DIR/$file" ]]; then
            missing_files+=("$file")
        fi
    done

    # Check directories
    for dir in "${DIRECTORIES[@]}"; do
        if [[ ! -d "$SOURCE_DIR/$dir" ]]; then
            missing_files+=("$dir/")
        fi
    done

    # Check documentation (non-critical)
    for file in "${DOCUMENTATION[@]}"; do
        if [[ ! -f "$SOURCE_DIR/$file" ]]; then
            warning "Optional file missing: $file"
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        error "Missing required source files in $SOURCE_DIR:"
        for file in "${missing_files[@]}"; do
            echo "  • $file"
        done
        return 1
    fi

    success "All required source files found"
    return 0
}

# Test Python module imports
test_python_imports() {
    progress "Testing Python module dependencies..."
    
    # Create a temporary test script
    local test_script=$(mktemp)
    cat > "$test_script" << 'EOF'
#!/usr/bin/env python3
import sys
import tempfile
import os

# Add current directory to path for testing
sys.path.insert(0, os.getcwd())

modules_to_test = [
    'logging_config',
    'security_validator', 
    'context_registry',
    'bridge_registry',
    'interfaces',
    'unified_context_manager',
    'tmux_utils',
]

failed_imports = []

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✓ {module}")
    except ImportError as e:
        print(f"✗ {module}: {e}")
        failed_imports.append(module)
    except Exception as e:
        print(f"? {module}: {e}")

if failed_imports:
    print(f"\nFailed to import: {', '.join(failed_imports)}")
    sys.exit(1)
else:
    print("\nAll imports successful!")
    sys.exit(0)
EOF

    chmod +x "$test_script"
    
    if (cd "$SOURCE_DIR" && python3 "$test_script"); then
        success "Python module dependencies verified"
        rm -f "$test_script"
        return 0
    else
        error "Python import test failed"
        rm -f "$test_script"
        return 1
    fi
}

# Create backup of existing installation
create_backup() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        info "No existing installation to backup"
        return 0
    fi

    progress "Creating backup of existing installation..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create timestamped backup
    local backup_name="ai-team-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name.tar.gz"
    
    # Find all ai-team related files
    local ai_files=()
    while IFS= read -r -d '' file; do
        ai_files+=("$file")
    done < <(find "$INSTALL_DIR" -name "*ai-team*" -o -name "*ai-bridge*" -o -name "tmux_utils.py" -o -name "context_registry.py" -o -name "unified_context_manager.py" -o -name "logging_config.py" -o -name "security_validator.py" -o -name "interfaces.py" -o -name "create_ai_team.py" -print0 2>/dev/null || true)

    if [[ ${#ai_files[@]} -gt 0 ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would backup ${#ai_files[@]} files to: $backup_path"
            return 0
        fi

        # Create backup archive (BSD tar compatible)
        # Create a temporary directory for the backup structure
        local temp_backup_dir=$(mktemp -d)
        mkdir -p "$temp_backup_dir/ai-team-installation"
        
        # Copy files to the structured directory
        for file in "${ai_files[@]}"; do
            local relative_path="${file##$INSTALL_DIR/}"
            local dest_dir="$temp_backup_dir/ai-team-installation/$(dirname "$relative_path")"
            mkdir -p "$dest_dir" 2>/dev/null || true
            cp "$file" "$temp_backup_dir/ai-team-installation/$relative_path" 2>/dev/null || true
        done
        
        # Create the archive from the structured directory
        (cd "$temp_backup_dir" && tar -czf "$backup_path" ai-team-installation/ 2>/dev/null || true)
        
        # Clean up temporary directory
        rm -rf "$temp_backup_dir" 2>/dev/null || true
        
        if [[ -f "$backup_path" ]]; then
            success "Backup created: $backup_path"
            log "Backup contains: ${ai_files[*]}"
        else
            warning "Could not create backup (non-critical)"
        fi
    else
        info "No existing ai-team files found to backup"
    fi
}

# Remove existing installation completely
uninstall_existing() {
    progress "Removing existing ai-team installation..."
    
    local removed_files=()
    local files_to_remove=(
        # Core files from our lists
        "${CORE_PYTHON_FILES[@]}"
        "${SHELL_SCRIPTS[@]}"
        "${DOCUMENTATION[@]}"
        # Additional cleanup
        ".ai-team-manifest.json"
    )
    
    # Remove individual files
    for file in "${files_to_remove[@]}"; do
        local target="$INSTALL_DIR/$file"
        if [[ -f "$target" ]]; then
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${CYAN}[DRY-RUN]${NC} Would remove: $target"
            else
                rm -f "$target"
                removed_files+=("$file")
                log "Removed file: $target"
            fi
        fi
    done

    # Remove directories
    for dir in "${DIRECTORIES[@]}"; do
        local target="$INSTALL_DIR/$dir"
        if [[ -d "$target" ]]; then
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${CYAN}[DRY-RUN]${NC} Would remove directory: $target"
            else
                rm -rf "$target"
                removed_files+=("$dir/")
                log "Removed directory: $target"
            fi
        fi
    done

    # Clean up coordination files
    local coord_dir="$HOME/.ai-coordination"
    if [[ -d "$coord_dir" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would clean coordination files in: $coord_dir"
        else
            # Only remove generated files, keep user data
            find "$coord_dir" -name "*.pid" -delete 2>/dev/null || true
            find "$coord_dir" -name "active-bridges.json" -delete 2>/dev/null || true
            info "Cleaned coordination files"
        fi
    fi

    if [[ ${#removed_files[@]} -gt 0 ]]; then
        success "Removed ${#removed_files[@]} files/directories"
    else
        info "No existing installation found to remove"
    fi
}

# Install files with verification
install_files() {
    progress "Installing AI Team CLI files..."
    
    # Create install directory
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$INSTALL_DIR"
    fi

    local installed_files=()
    local checksums=()

    # Install Python files
    for file in "${CORE_PYTHON_FILES[@]}"; do
        local src="$SOURCE_DIR/$file"
        local dest="$INSTALL_DIR/$file"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would copy: $file"
        else
            cp "$src" "$dest"
            chmod 644 "$dest"
            installed_files+=("$file")
            if command -v sha256sum &> /dev/null; then
                checksums+=("$file:$(sha256sum "$dest" | cut -d' ' -f1)")
            fi
            log "Installed Python file: $file"
        fi
    done

    # Install shell scripts
    for file in "${SHELL_SCRIPTS[@]}"; do
        local src="$SOURCE_DIR/$file"
        local dest="$INSTALL_DIR/$file"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would copy: $file (executable)"
        else
            cp "$src" "$dest"
            chmod +x "$dest"
            installed_files+=("$file")
            if command -v sha256sum &> /dev/null; then
                checksums+=("$file:$(sha256sum "$dest" | cut -d' ' -f1)")
            fi
            log "Installed shell script: $file"
        fi
    done

    # Install directories
    for dir in "${DIRECTORIES[@]}"; do
        local src="$SOURCE_DIR/$dir"
        local dest="$INSTALL_DIR/$dir"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would copy directory: $dir"
        else
            cp -r "$src" "$dest"
            find "$dest" -name "*.py" -exec chmod 644 {} \;
            find "$dest" -name "*.sh" -exec chmod +x {} \;
            installed_files+=("$dir/")
            log "Installed directory: $dir"
        fi
    done

    # Install documentation
    for file in "${DOCUMENTATION[@]}"; do
        local src="$SOURCE_DIR/$file"
        local dest="$INSTALL_DIR/$file"
        
        if [[ -f "$src" ]]; then
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${CYAN}[DRY-RUN]${NC} Would copy: $file"
            else
                cp "$src" "$dest"
                chmod 644 "$dest"
                installed_files+=("$file")
                log "Installed documentation: $file"
            fi
        fi
    done

    if [[ "$DRY_RUN" == "false" ]] && command -v jq &> /dev/null; then
        # Create installation manifest
        cat > "$MANIFEST_FILE" << EOF
{
    "version": "1.1.0",
    "install_date": "$(date -Iseconds)",
    "source_dir": "$SOURCE_DIR",
    "files": [$(printf '"%s",' "${installed_files[@]}" | sed 's/,$//')],
    "checksums": [$(printf '"%s",' "${checksums[@]}" | sed 's/,$//')],
    "python_version": "$(python3 --version)",
    "installer_version": "2.0"
}
EOF
        success "Installation manifest created"
    fi

    success "Installed ${#installed_files[@]} files"
}

# Setup PATH if needed
setup_path() {
    if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
        success "$INSTALL_DIR already in PATH"
        return 0
    fi

    progress "Setting up PATH configuration..."
    
    local shell_config=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        if [[ -f "$HOME/.bashrc" ]]; then
            shell_config="$HOME/.bashrc"
        else
            shell_config="$HOME/.bash_profile"
        fi
    else
        warning "Unknown shell: $SHELL"
        echo "Please manually add $INSTALL_DIR to your PATH"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}[DRY-RUN]${NC} Would add PATH to: $shell_config"
        return 0
    fi

    echo "" >> "$shell_config"
    echo "# AI Team CLI" >> "$shell_config"
    echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$shell_config"
    
    success "Added $INSTALL_DIR to PATH in $shell_config"
    info "Run 'source $shell_config' or restart your terminal"
    
    return 0
}

# Test installation
test_installation() {
    progress "Testing installation..."
    
    # Test main command
    if [[ -x "$INSTALL_DIR/ai-team" ]]; then
        if "$INSTALL_DIR/ai-team" --help > /dev/null 2>&1; then
            success "ai-team command works"
        else
            error "ai-team command failed to run"
            return 1
        fi
    else
        error "ai-team command not found or not executable"
        return 1
    fi

    # Test Python imports in install directory
    progress "Testing Python modules in install directory..."
    local test_script=$(mktemp)
    cat > "$test_script" << EOF
#!/usr/bin/env python3
import sys
sys.path.insert(0, '$INSTALL_DIR')

# Test core modules
modules = ['logging_config', 'security_validator', 'context_registry', 'bridge_registry', 'tmux_utils', 'unified_context_manager']
failed = []

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except Exception as e:
        print(f"✗ {module}: {e}")
        failed.append(module)

if failed:
    print(f"Failed: {', '.join(failed)}")
    sys.exit(1)
else:
    print("All modules imported successfully!")
    sys.exit(0)
EOF

    if python3 "$test_script"; then
        success "Python module imports verified"
    else
        error "Python module import test failed"
        rm -f "$test_script"
        return 1
    fi
    
    rm -f "$test_script"

    # Test bridge registry (if available)
    if [[ -x "$INSTALL_DIR/ai-bridge" ]]; then
        if "$INSTALL_DIR/ai-bridge" help > /dev/null 2>&1; then
            success "ai-bridge command works"
        else
            warning "ai-bridge command test failed (non-critical)"
        fi
    fi

    success "Installation test completed successfully"
    return 0
}

# Verify existing installation
verify_installation() {
    progress "Verifying existing installation..."
    
    local errors=0
    local warnings=0

    # Check if installation exists
    if [[ ! -d "$INSTALL_DIR" ]]; then
        error "Installation directory $INSTALL_DIR does not exist"
        return 1
    fi

    # Check manifest
    if [[ -f "$MANIFEST_FILE" ]]; then
        success "Installation manifest found"
        if command -v jq &> /dev/null; then
            local install_date=$(jq -r '.install_date' "$MANIFEST_FILE" 2>/dev/null || echo "unknown")
            local version=$(jq -r '.version' "$MANIFEST_FILE" 2>/dev/null || echo "unknown")
            info "Installation: version $version, date $install_date"
        fi
    else
        warning "No installation manifest found"
        ((warnings++))
    fi

    # Check core files
    for file in "${CORE_PYTHON_FILES[@]}" "${SHELL_SCRIPTS[@]}"; do
        local target="$INSTALL_DIR/$file"
        if [[ -f "$target" ]]; then
            success "$file present"
        else
            error "$file missing"
            ((errors++))
        fi
    done

    # Check executable permissions
    for file in "${SHELL_SCRIPTS[@]}"; do
        local target="$INSTALL_DIR/$file"
        if [[ -x "$target" ]]; then
            success "$file is executable"
        elif [[ -f "$target" ]]; then
            error "$file exists but is not executable"
            ((errors++))
        fi
    done

    # Test functionality
    if test_installation; then
        success "Functionality test passed"
    else
        error "Functionality test failed"
        ((errors++))
    fi

    # Summary
    if [[ $errors -eq 0 ]]; then
        success "Installation verification completed successfully"
        if [[ $warnings -gt 0 ]]; then
            info "$warnings warnings found (non-critical)"
        fi
        return 0
    else
        error "Installation verification failed with $errors errors and $warnings warnings"
        return 1
    fi
}

# Main installation process
main() {
    # Parse arguments first
    parse_args "$@"
    
    # Initialize log
    echo "$(date '+%Y-%m-%d %H:%M:%S'): AI Team CLI installation started" > "$LOG_FILE"
    
    echo -e "${BLUE}🚀 AI Team CLI Enhanced Installation${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}🔍 DRY-RUN MODE: No changes will be made${NC}"
    fi

    # Handle special modes
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        verify_installation
        return $?
    fi

    if [[ "$UNINSTALL_ONLY" == "true" ]]; then
        create_backup
        uninstall_existing
        success "Uninstall completed"
        return 0
    fi

    # Full installation process
    check_system_dependencies || return 1
    validate_source_files || return 1
    test_python_imports || return 1
    
    create_backup
    uninstall_existing
    install_files
    setup_path
    
    if [[ "$DRY_RUN" == "false" ]]; then
        test_installation || return 1
    fi

    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}🎉 AI Team CLI installation completed successfully!${NC}"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        echo ""
        echo "Files installed:"
        echo "  • Core Python modules: ${#CORE_PYTHON_FILES[@]} files"
        echo "  • Shell scripts: ${#SHELL_SCRIPTS[@]} files"  
        echo "  • Directories: ${#DIRECTORIES[@]} directories"
        echo ""
        echo "What's created:"
        echo "  • Orchestrator: Coordinates and mediates"
        echo "  • Alex: Perfectionist architect (quality-focused)"
        echo "  • Morgan: Pragmatic shipper (speed-focused)"
        echo "  • Sam: Code janitor (cleanup-focused)"
        echo ""
        echo "Usage:"
        echo -e "  ${BLUE}ai-team${NC}                    # Create default team"
        echo -e "  ${BLUE}ai-team --help${NC}             # Show help"
        echo -e "  ${BLUE}ai-team --verify${NC}           # Verify installation"
        
        # Check PATH
        if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
            echo ""
            echo -e "${YELLOW}⚠️  To use immediately, run:${NC}"
            echo -e "  ${BLUE}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
            echo -e "  ${BLUE}ai-team${NC}"
            echo ""
            echo -e "Or restart your terminal and run: ${BLUE}ai-team${NC}"
        else
            echo ""
            echo -e "Ready to use! Run: ${BLUE}ai-team${NC}"
        fi
    fi
    
    echo -e "${BLUE}================================================${NC}"
}

# Run main function with all arguments
main "$@"
