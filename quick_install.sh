#!/bin/bash
# Quick Install Script for AI Team CLI
# One-line installation: curl -sSL https://raw.githubusercontent.com/yourusername/ai-team/main/quick_install.sh | bash

set -e

echo "🚀 Installing AI Team CLI..."

# Install pipx if not present
if ! command -v pipx &> /dev/null; then
    echo "📦 Installing pipx..."
    if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
        brew install pipx
    else
        python3 -m pip install --user pipx
    fi
    pipx ensurepath
fi

# Install ai-team from current directory or from git
if [ -f "setup.py" ]; then
    echo "📁 Installing from current directory..."
    pipx install . --force
else
    echo "🌐 Installing from GitHub..."
    pipx install git+https://github.com/yourusername/ai-team.git --force
fi

echo "✅ Installation complete!"
echo ""
echo "🎯 Quick Start:"
echo "  ai-team              # Create default AI team"
echo "  ai-team -y           # Non-interactive mode"
echo "  ai-team -o -n        # Safe observe-only mode"
echo "  ai-team --help       # Show all options"
echo ""
echo "💡 Tip: You may need to restart your terminal or run: source ~/.bashrc"