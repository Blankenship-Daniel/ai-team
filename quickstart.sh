#!/bin/bash

set -e

# Parse command line arguments
AUTO_YES=false
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "AI Team Quick Start"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --yes, -y    Non-interactive mode (auto-kill existing sessions)"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0           Interactive setup"
    echo "  $0 --yes     Fast setup, no prompts"
    exit 0
elif [[ "$1" == "--yes" || "$1" == "-y" ]]; then
    AUTO_YES=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🚀 AI Team Quick Start 🚀        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
if [ "$AUTO_YES" = true ]; then
    echo -e "${GREEN}🤖 Non-interactive mode: --yes flag detected${NC}"
fi
echo ""

# Function to check if a command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to handle errors
handle_error() {
    echo -e "${RED}❌ Error: $1${NC}"
    exit 1
}

# Step 1: Check dependencies
echo -e "${BLUE}📋 Step 1: Checking dependencies...${NC}"
echo ""

MISSING_DEPS=0

# Check tmux
if check_command tmux; then
    echo -e "  ${GREEN}✅ tmux is installed${NC}"
else
    echo -e "  ${RED}❌ tmux is not installed${NC}"
    echo -e "  ${YELLOW}   Install with:${NC}"
    echo -e "     macOS:  ${CYAN}brew install tmux${NC}"
    echo -e "     Ubuntu: ${CYAN}sudo apt-get install tmux${NC}"
    echo -e "     CentOS: ${CYAN}sudo yum install tmux${NC}"
    MISSING_DEPS=1
fi

# Check Claude CLI
if check_command claude; then
    echo -e "  ${GREEN}✅ Claude CLI is installed${NC}"
else
    echo -e "  ${YELLOW}⚠️  Claude CLI not found${NC}"
    echo -e "  ${YELLOW}   Install from: ${CYAN}https://claude.ai/cli${NC}"
    echo -e "  ${YELLOW}   The AI team will not work without it!${NC}"
    MISSING_DEPS=1
fi

# Check Python3
if check_command python3; then
    echo -e "  ${GREEN}✅ Python3 is installed${NC}"
else
    echo -e "  ${RED}❌ Python3 is not installed${NC}"
    echo -e "  ${YELLOW}   Install with:${NC}"
    echo -e "     macOS:  ${CYAN}brew install python3${NC}"
    echo -e "     Ubuntu: ${CYAN}sudo apt-get install python3${NC}"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Missing dependencies detected!${NC}"
    echo -e "${YELLOW}Please install the missing tools and run this script again.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✨ All dependencies satisfied!${NC}"
echo ""

# Step 2: Check if ai-team command is installed
echo -e "${BLUE}📦 Step 2: Checking AI Team installation...${NC}"
echo ""

NEED_INSTALL=0

# Check if ai-team is available
if check_command ai-team || [ -f "$HOME/.local/bin/ai-team" ]; then
    echo -e "  ${GREEN}✅ ai-team command is installed${NC}"
else
    echo -e "  ${YELLOW}⚠️  ai-team command not found${NC}"
    NEED_INSTALL=1
fi

# Check if we're in the Tmux-Orchestrator directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRENT_DIR="$(pwd)"

# Check if core files exist (either locally or in script directory)
if [ ! -f "create_ai_team.py" ] && [ ! -f "$SCRIPT_DIR/create_ai_team.py" ]; then
    echo -e "  ${RED}❌ Core files missing!${NC}"
    handle_error "Cannot find Tmux-Orchestrator files. Installation may be corrupted."
fi

# Determine if we're running from the installation directory
if [ -f "create_ai_team.py" ] && [ -f "tmux_utils.py" ]; then
    RUNNING_FROM_INSTALL=true
    echo -e "  ${GREEN}✅ Running from Tmux-Orchestrator directory${NC}"
else
    RUNNING_FROM_INSTALL=false
    echo -e "  ${BLUE}📍 Running from project directory${NC}"
fi

# Create logs directory for Sam's logging system
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "  ${GREEN}✅ Created logs directory${NC}"
fi

# Step 2.5: Context Preservation Setup
echo ""
echo -e "${BLUE}🔐 Step 2.5: Preparing workspace context...${NC}"
echo ""

# The AI team will work in the current directory
echo -e "  ${BLUE}Working directory: ${GREEN}$CURRENT_DIR${NC}"

# Create .ai-team directory for context files
if [ ! -d ".ai-team" ]; then
    mkdir -p .ai-team
    echo -e "  ${GREEN}✅ Created .ai-team directory for context${NC}"
fi

# Create workspace structure for agents
mkdir -p .ai-team/workspaces/{orchestrator,alex,morgan,sam}
echo -e "  ${GREEN}✅ Created agent workspace directories${NC}"

# Create context documentation
if [ ! -f ".ai-team/CONTEXT.md" ]; then
    cat > .ai-team/CONTEXT.md << EOF
# AI Team Context - $(date)

## Working Directory
Path: $CURRENT_DIR

## Team Structure
- **Orchestrator** (pane 0.0): Coordinates the team
- **Alex** (pane 0.1): Perfectionist architect
- **Morgan** (pane 0.2): Pragmatic shipper  
- **Sam** (pane 0.3): Code custodian

## Communication Protocol
Use tmux send-keys or send-claude-message.sh:
\`\`\`bash
send-claude-message.sh ai-team:0.1 "Message to Alex"
tmux capture-pane -t ai-team:0.1 -p | tail -20
\`\`\`

## Important Locations
- Context: .ai-team/CONTEXT.md
- Status: .ai-team/STATUS.md
- Logs: logs/
- Agent workspaces: .ai-team/workspaces/

## Recovery
If agents lose context, run: .ai-team/recovery.sh
EOF
    echo -e "  ${GREEN}✅ Created context documentation${NC}"
fi

# Create quick recovery script
if [ ! -f ".ai-team/recovery.sh" ]; then
    cat > .ai-team/recovery.sh << 'EOF'
#!/bin/bash
echo "🔧 AI Team Context Recovery"
echo "Working directory: $(pwd)"
echo ""
echo "Re-establishing context for all agents..."
for pane in 0 1 2 3; do
    tmux send-keys -t ai-team:0.$pane "# Context restored: $(pwd)" Enter
done
echo "✅ Context restoration complete"
EOF
    chmod +x .ai-team/recovery.sh
    echo -e "  ${GREEN}✅ Created recovery script${NC}"
fi

# Link communication script if needed
if [ ! -f "send-claude-message.sh" ] && [ -f "$SCRIPT_DIR/send-claude-message.sh" ]; then
    ln -sf "$SCRIPT_DIR/send-claude-message.sh" send-claude-message.sh
    echo -e "  ${GREEN}✅ Linked communication script${NC}"
fi

echo -e "  ${GREEN}✅ Context preservation ready${NC}"

# Run install.sh if needed
if [ $NEED_INSTALL -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}📥 Installing AI Team CLI...${NC}"
    
    if [ -f "install.sh" ]; then
        echo -e "${CYAN}Running install.sh...${NC}"
        ./install.sh || handle_error "Installation failed"
        
        # Add to PATH for current session if needed
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            export PATH="$PATH:$HOME/.local/bin"
        fi
        echo -e "${GREEN}✅ Installation complete!${NC}"
    else
        echo -e "${RED}❌ install.sh not found!${NC}"
        handle_error "Cannot find install.sh in current directory"
    fi
fi

echo ""

# Step 3: Check for existing AI team session
echo -e "${BLUE}🔍 Step 3: Checking for existing sessions...${NC}"
echo ""

if tmux has-session -t ai-team 2>/dev/null; then
    echo -e "  ${YELLOW}⚠️  AI team session already exists!${NC}"
    echo ""
    echo -e "  ${CYAN}Options:${NC}"
    echo -e "    1. Attach to existing:  ${GREEN}tmux attach -t ai-team${NC}"
    echo -e "    2. Kill and recreate:   ${YELLOW}tmux kill-session -t ai-team${NC}"
    echo ""
    
    if [ "$AUTO_YES" = true ]; then
        echo -e "  ${YELLOW}Auto-kill mode enabled, killing existing session...${NC}"
        REPLY="y"
    else
        read -p "  Would you like to kill the existing session and create a new one? (y/N): " -n 1 -r
        echo ""
    fi
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing existing session...${NC}"
        tmux kill-session -t ai-team
        echo -e "${GREEN}✅ Session killed${NC}"
    else
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ Attach to your existing AI team with:${NC}"
        echo -e "${CYAN}   tmux attach -t ai-team${NC}"
        echo -e "${CYAN}═══════════════════════════════════════${NC}"
        exit 0
    fi
fi

echo ""

# Step 4: Create the AI team
echo -e "${BLUE}🤖 Step 4: Creating your AI team...${NC}"
echo ""

# Try ai-team command first, fall back to python script
if check_command ai-team || [ -x "$HOME/.local/bin/ai-team" ]; then
    echo -e "${CYAN}Starting AI team...${NC}"
    if [ -x "$HOME/.local/bin/ai-team" ]; then
        "$HOME/.local/bin/ai-team"
    else
        ai-team
    fi
elif [ -f "create_ai_team.py" ]; then
    echo -e "${CYAN}Starting AI team with Python script...${NC}"
    python3 create_ai_team.py
else
    handle_error "Cannot find ai-team command or create_ai_team.py"
fi

# Wait a moment for session to initialize
sleep 2

# Step 5: Verify creation and show instructions
echo ""
echo -e "${BLUE}✨ Step 5: Verifying AI team creation...${NC}"
echo ""

if tmux has-session -t ai-team 2>/dev/null; then
    echo -e "${GREEN}✅ AI Team successfully created and running!${NC}"
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    🎉 SUCCESS! 🎉                          ║${NC}"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║  Your AI team is ready with:                              ║${NC}"
    echo -e "${CYAN}║    • Orchestrator (top pane) - Your control center        ║${NC}"
    echo -e "${CYAN}║    • Alex - The perfectionist architect                   ║${NC}"
    echo -e "${CYAN}║    • Morgan - The pragmatic shipper                       ║${NC}"
    echo -e "${CYAN}║    • Sam - The code quality engineer                      ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📋 Next Steps:${NC}"
    echo ""
    echo -e "  1. ${CYAN}Attach to your team:${NC}"
    echo -e "     ${GREEN}tmux attach -t ai-team${NC}"
    echo ""
    echo -e "  2. ${CYAN}Give instructions to the Orchestrator (top pane)${NC}"
    echo ""
    echo -e "  3. ${CYAN}Watch your AI team collaborate!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Tmux Tips:${NC}"
    echo -e "  • Switch panes:  ${CYAN}Ctrl+b${NC} then ${CYAN}arrow keys${NC}"
    echo -e "  • Detach:        ${CYAN}Ctrl+b${NC} then ${CYAN}d${NC}"
    echo -e "  • Scroll mode:   ${CYAN}Ctrl+b${NC} then ${CYAN}[${NC}"
    echo -e "  • Exit scroll:   ${CYAN}q${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Session Management:${NC}"
    echo -e "  • List sessions:  ${CYAN}tmux ls${NC}"
    echo -e "  • Kill session:   ${CYAN}tmux kill-session -t ai-team${NC}"
    echo -e "  • Rename window:  ${CYAN}Ctrl+b${NC} then ${CYAN},${NC}"
    echo ""
    
    # Add context reminder if running from different directory
    if [ "$CURRENT_DIR" != "$SCRIPT_DIR" ]; then
        echo -e "${YELLOW}📁 Context Files:${NC}"
        echo -e "  • Working in:     ${CYAN}$CURRENT_DIR${NC}"
        echo -e "  • Context saved:  ${CYAN}.ai-team/CONTEXT.md${NC}"
        echo -e "  • Status updates: ${CYAN}.ai-team/STATUS.md${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}Ready to attach? Run:${NC} ${CYAN}tmux attach -t ai-team${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
else
    handle_error "AI team session was not created successfully"
fi

# Success!
exit 0