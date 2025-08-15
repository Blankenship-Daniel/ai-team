#!/bin/bash
# AI Team CLI Global Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.local/bin"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND_NAME="ai-team"

echo -e "${BLUE}🚀 AI Team CLI Global Installation${NC}"
echo "================================================"

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ Error: tmux is not installed${NC}"
    echo "Please install tmux first:"
    echo "  macOS: brew install tmux"
    echo "  Ubuntu/Debian: sudo apt install tmux"
    echo "  CentOS/RHEL: sudo yum install tmux"
    exit 1
fi

# Check if Claude CLI is available
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'claude' command not found${NC}"
    echo "Make sure Claude CLI is installed and available in PATH"
    echo "The AI team will not work without it."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Claude CLI found${NC}"
    echo -e "${BLUE}ℹ️  Note: All Claude instances will start with --dangerously-skip-permissions${NC}"
fi

# Create install directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${BLUE}📁 Creating install directory: $INSTALL_DIR${NC}"
    mkdir -p "$INSTALL_DIR"
fi

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  $INSTALL_DIR is not in your PATH${NC}"
    echo "Adding to shell configuration..."
    
    # Detect shell and add to appropriate config file
    SHELL_CONFIG=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        if [[ -f "$HOME/.bashrc" ]]; then
            SHELL_CONFIG="$HOME/.bashrc"
        else
            SHELL_CONFIG="$HOME/.bash_profile"
        fi
    else
        echo -e "${YELLOW}⚠️  Unknown shell: $SHELL${NC}"
        echo "Please manually add $INSTALL_DIR to your PATH"
    fi
    
    if [[ -n "$SHELL_CONFIG" ]]; then
        echo "" >> "$SHELL_CONFIG"
        echo "# AI Team CLI" >> "$SHELL_CONFIG"
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_CONFIG"
        echo -e "${GREEN}✓ Added $INSTALL_DIR to PATH in $SHELL_CONFIG${NC}"
        echo -e "${BLUE}📝 Run 'source $SHELL_CONFIG' or restart your terminal${NC}"
    fi
fi

# Copy the main script and dependencies
echo -e "${BLUE}📦 Installing AI Team CLI...${NC}"

# Copy main Python script
cp "$SOURCE_DIR/create_ai_team.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied create_ai_team.py${NC}"

# Copy dependencies
cp "$SOURCE_DIR/tmux_utils.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied tmux_utils.py${NC}"

cp "$SOURCE_DIR/send-claude-message.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/send-claude-message.sh"
echo -e "${GREEN}✓ Copied send-claude-message.sh${NC}"

# Copy the wrapper script
cp "$SOURCE_DIR/ai-team" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/ai-team"
echo -e "${GREEN}✓ Installed ai-team command${NC}"

# Test installation
echo -e "${BLUE}🧪 Testing installation...${NC}"
if [ -x "$INSTALL_DIR/ai-team" ]; then
    echo -e "${GREEN}✓ Installation successful!${NC}"
else
    echo -e "${RED}❌ Installation failed${NC}"
    exit 1
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 AI Team CLI installed successfully!${NC}"
echo ""
echo "Usage:"
echo -e "  ${BLUE}ai-team${NC}                    # Create default team"
echo -e "  ${BLUE}ai-team -s my-team${NC}         # Create with custom name"
echo -e "  ${BLUE}ai-team --help${NC}             # Show help"
echo ""
echo "What's installed:"
echo "  • Command: ai-team (in $INSTALL_DIR)"
echo "  • Creates: Orchestrator + 3 opinionated AI engineers"
echo "  • Alex: Perfectionist architect (quality-focused)"
echo "  • Morgan: Pragmatic shipper (speed-focused)"
echo "  • Sam: Code janitor (cleanup-focused)"
echo ""

# Check if PATH update is needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  To use immediately, run:${NC}"
    echo -e "  ${BLUE}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    echo -e "  ${BLUE}ai-team${NC}"
    echo ""
    echo -e "Or restart your terminal and run: ${BLUE}ai-team${NC}"
else
    echo -e "Ready to use! Run: ${BLUE}ai-team${NC}"
fi

echo "================================================"