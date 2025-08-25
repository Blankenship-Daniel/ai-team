#!/bin/bash
# AI Team Global Installation Script
# This script installs the ai-team CLI globally using pipx for isolation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_info "Starting AI Team global installation..."

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    print_error "Unsupported platform: $OSTYPE"
    exit 1
fi
print_info "Detected platform: $PLATFORM"

# Check for Python 3.8+
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    if [[ "$PLATFORM" == "macOS" ]]; then
        print_info "Install with: brew install python3"
    else
        print_info "Install with: sudo apt-get install python3 python3-pip"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_info "Found Python $PYTHON_VERSION"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    print_warning "pipx is not installed. Installing pipx..."
    
    if [[ "$PLATFORM" == "macOS" ]]; then
        # Check if Homebrew is installed
        if command -v brew &> /dev/null; then
            print_info "Installing pipx via Homebrew..."
            brew install pipx
            pipx ensurepath
        else
            print_info "Installing pipx via pip..."
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
    else
        # Linux installation
        print_info "Installing pipx via pip..."
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
    
    # Source shell config to get pipx in PATH
    if [[ -f "$HOME/.zshrc" ]]; then
        source "$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        source "$HOME/.bashrc"
    fi
    
    print_success "pipx installed successfully"
else
    print_info "pipx is already installed"
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

print_info "Working directory: $SCRIPT_DIR"

# Check if ai-team is already installed via pipx
if pipx list | grep -q "ai-team"; then
    print_warning "ai-team is already installed. Uninstalling old version..."
    pipx uninstall ai-team
fi

# Install ai-team globally using pipx
print_info "Installing ai-team globally with pipx..."
if pipx install . --force; then
    print_success "ai-team installed successfully via pipx!"
else
    print_warning "pipx installation failed, trying alternative method..."
    
    # Alternative: Create a temporary wheel and install
    print_info "Building wheel package..."
    python3 -m pip install --user build
    python3 -m build --wheel
    
    # Find the built wheel
    WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)
    if [[ -z "$WHEEL_FILE" ]]; then
        print_error "Failed to build wheel package"
        exit 1
    fi
    
    print_info "Installing from wheel: $WHEEL_FILE"
    pipx install "$WHEEL_FILE" --force
fi

# Ensure PATH is updated
pipx ensurepath

# Verify installation
print_info "Verifying installation..."

# Check if ai-team is in PATH
if command -v ai-team &> /dev/null; then
    AI_TEAM_PATH=$(which ai-team)
    print_success "ai-team is installed at: $AI_TEAM_PATH"
    
    # Try to run help command
    if ai-team --help &> /dev/null; then
        print_success "ai-team command is working properly!"
    else
        print_warning "ai-team is installed but may need dependencies"
    fi
else
    print_warning "ai-team is installed but not yet in PATH"
    print_info "You may need to:"
    print_info "  1. Restart your terminal"
    print_info "  2. Or run: source ~/.bashrc (or ~/.zshrc)"
    print_info "  3. Or add ~/.local/bin to your PATH"
fi

# Create uninstall script
cat > "$SCRIPT_DIR/uninstall_global.sh" << 'EOF'
#!/bin/bash
# Uninstall ai-team global installation

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Uninstalling ai-team..."

if command -v pipx &> /dev/null; then
    if pipx list | grep -q "ai-team"; then
        pipx uninstall ai-team
        echo -e "${GREEN}[SUCCESS]${NC} ai-team uninstalled successfully"
    else
        echo -e "${BLUE}[INFO]${NC} ai-team is not installed via pipx"
    fi
else
    echo -e "${RED}[ERROR]${NC} pipx is not installed"
fi
EOF

chmod +x "$SCRIPT_DIR/uninstall_global.sh"

print_info ""
print_success "============================================"
print_success "AI Team installation complete!"
print_success "============================================"
print_info ""
print_info "Usage:"
print_info "  ai-team --help              # Show help"
print_info "  ai-team create <team-name>  # Create a new AI team"
print_info "  ai-team list                # List existing teams"
print_info ""
print_info "To uninstall:"
print_info "  ./uninstall_global.sh"
print_info ""

# Check if need to source shell config
if ! command -v ai-team &> /dev/null; then
    print_warning "Please restart your terminal or run:"
    if [[ -f "$HOME/.zshrc" ]]; then
        print_warning "  source ~/.zshrc"
    else
        print_warning "  source ~/.bashrc"
    fi
fi