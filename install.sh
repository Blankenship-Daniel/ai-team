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

# Check if jq is available (required for bridge messaging)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'jq' command not found${NC}"
    echo "Bridge messaging requires jq for JSON processing"
    echo "Install: brew install jq (macOS) or apt install jq (Ubuntu)"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ jq found${NC}"
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

# Verify all required files exist before installation
echo -e "${BLUE}🔍 Verifying required files...${NC}"
REQUIRED_FILES=("create_ai_team.py" "ai-bridge" "tmux_utils.py" "security_validator.py" "logging_config.py" "unified_context_manager.py" "send-claude-message.sh" "schedule_with_note.sh" "check-peer-messages.sh" "ai-team")

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SOURCE_DIR/$file" ]; then
        echo -e "${RED}❌ Error: Required file '$file' not found in $SOURCE_DIR${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files found${NC}"

# Copy the main script and dependencies
echo -e "${BLUE}📦 Installing AI Team CLI...${NC}"

# Copy main Python script
cp "$SOURCE_DIR/create_ai_team.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied create_ai_team.py${NC}"

# Copy bridge registry
cp "$SOURCE_DIR/ai-bridge" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/ai-bridge"
echo -e "${GREEN}✓ Copied ai-bridge${NC}"

# Copy peer communication tools
cp "$SOURCE_DIR/check-peer-messages.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/check-peer-messages.sh"
echo -e "${GREEN}✓ Copied check-peer-messages.sh${NC}"

# Copy Python dependencies
cp "$SOURCE_DIR/tmux_utils.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied tmux_utils.py${NC}"

cp "$SOURCE_DIR/security_validator.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied security_validator.py${NC}"

cp "$SOURCE_DIR/logging_config.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied logging_config.py${NC}"

cp "$SOURCE_DIR/unified_context_manager.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied unified_context_manager.py${NC}"

# Copy shell script utilities
cp "$SOURCE_DIR/send-claude-message.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/send-claude-message.sh"
echo -e "${GREEN}✓ Copied send-claude-message.sh${NC}"

cp "$SOURCE_DIR/schedule_with_note.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/schedule_with_note.sh"
echo -e "${GREEN}✓ Copied schedule_with_note.sh${NC}"

# Copy the orchestrator guide
cp "$SOURCE_DIR/ORCHESTRATOR_GUIDE.md" "$INSTALL_DIR/"
chmod 644 "$INSTALL_DIR/ORCHESTRATOR_GUIDE.md"
echo -e "${GREEN}✓ Copied ORCHESTRATOR_GUIDE.md${NC}"

# Copy the context helper
cp "$SOURCE_DIR/context-status.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/context-status.sh"
echo -e "${GREEN}✓ Copied context-status.sh${NC}"

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

# Test bridge registry functionality
echo -e "${BLUE}🧪 Testing bridge registry...${NC}"
if python3 "$INSTALL_DIR/ai-bridge" help >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Bridge registry functional${NC}"
else
    echo -e "${YELLOW}⚠️  Bridge registry test failed${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 AI Team CLI installed successfully!${NC}"
echo ""
echo "Files installed:"
echo "  • create_ai_team.py (main script)"
echo "  • ai-bridge (multi-bridge coordination)"
echo "  • tmux_utils.py (tmux management)"
echo "  • check-peer-messages.sh (peer communication)"
echo "  • security_validator.py (input validation)"
echo "  • logging_config.py (logging setup)"
echo "  • unified_context_manager.py (agent context)"
echo "  • send-claude-message.sh (messaging utility)"
echo "  • schedule_with_note.sh (scheduling utility)"
echo "  • ORCHESTRATOR_GUIDE.md (tmux communication guide)"
echo "  • context-status.sh (quick context restoration)"
echo "  • ai-team (command wrapper)"
echo ""
echo "Usage:"
echo -e "  ${BLUE}ai-team${NC}                                           # Create default team"
echo -e "  ${BLUE}ai-team connect session1 session2 \"context\"${NC}     # Connect two teams (via ai-bridge)"
echo -e "  ${BLUE}ai-team -s my-team${NC}         # Create with custom name"
echo -e "  ${BLUE}ai-team --help${NC}             # Show help"
echo ""
echo "Bridge Management (ai-bridge):"
echo -e "  ${BLUE}ai-bridge create team1 team2 \"coordination context\"${NC}  # Connect teams"
echo -e "  ${BLUE}ai-bridge list${NC}                                         # List active bridges"
echo -e "  ${BLUE}ai-bridge status team-name${NC}                             # Check team's bridges"
echo -e "  ${BLUE}ai-bridge cleanup --dry-run --max-age-days 3${NC}          # Clean old bridges"
echo -e "  ${BLUE}ai-bridge help${NC}                                         # Show detailed help"
echo ""
echo "Bridge Workflow Examples:"
echo "  1. Create bridge: ai-bridge create frontend backend \"API sync\""
echo "  2. Send message:  send-to-peer-frontend.sh \"Update ready\""
echo "  3. Check msgs:    check-peer-messages.sh"
echo "  4. Monitor:       ai-bridge status frontend"
echo ""
echo "Real-world Bridge Use Cases:"
echo "  • Mobile ↔ Web teams coordinating UI consistency"
echo "  • Frontend ↔ Backend teams syncing API changes"
echo "  • DevOps ↔ Security teams sharing deployment info"
echo "  • Research ↔ Production teams transferring models"
echo ""
echo "What's created:"
echo "  • Orchestrator: Coordinates and mediates"
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
