#!/bin/bash

set -e

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

# Check if core files exist
if [ ! -f "create_ai_team.py" ] || [ ! -f "tmux_utils.py" ]; then
    echo -e "  ${RED}❌ Core files missing!${NC}"
    handle_error "Required files not found. Are you in the Tmux-Orchestrator directory?"
fi

# Create logs directory for Sam's logging system
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "  ${GREEN}✅ Created logs directory${NC}"
fi

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
    read -p "  Would you like to kill the existing session and create a new one? (y/N): " -n 1 -r
    echo ""
    
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
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}Ready to attach? Run:${NC} ${CYAN}tmux attach -t ai-team${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
else
    handle_error "AI team session was not created successfully"
fi

# Success!
exit 0