#!/bin/bash
# Quick health check for AI Team

echo "🔍 AI Team Health Check"
echo "======================="

# Check tmux
if command -v tmux &> /dev/null; then
    echo "✅ tmux installed"
    tmux list-sessions 2>/dev/null | grep -q "ai-team" && echo "✅ ai-team session running" || echo "⚠️  No ai-team session (run: ai-team)"
else
    echo "❌ tmux not installed"
    exit 1
fi

# Check Claude CLI
if command -v claude &> /dev/null; then
    echo "✅ Claude CLI installed"
else
    echo "❌ Claude CLI not found - install from https://claude.ai/cli"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 installed"
else
    echo "❌ Python3 not installed"
    exit 1
fi

# Check ai-team command
if command -v ai-team &> /dev/null || [ -f "$HOME/.local/bin/ai-team" ]; then
    echo "✅ ai-team command available"
else
    echo "⚠️  ai-team not in PATH (run: ./install.sh)"
fi

echo ""
echo "Ready to ship! 🚀"