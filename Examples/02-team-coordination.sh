#!/bin/bash

# Team Coordination Demo - See how Alex, Morgan & Sam work together
# This demonstrates the three opinionated agents coordinating on a task

set -e

echo "🤝 Team Coordination Demo - Three Opinionated Agents"
echo "====================================================="
echo ""
echo "This demo will:"
echo "1. Create an AI team with Orchestrator + 3 agents"
echo "2. Use --observe-only mode to prevent chaos"
echo "3. Show how different personalities approach the same problem"
echo ""

# Check prerequisites
if ! command -v tmux &> /dev/null; then
    echo "❌ Error: tmux is not installed. Please install tmux first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed. Please install python3 first."
    exit 1
fi

# Setup paths
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CREATE_TEAM="$SCRIPT_DIR/create_ai_team.py"

if [ ! -f "$CREATE_TEAM" ]; then
    echo "❌ Error: create_ai_team.py not found at $CREATE_TEAM"
    exit 1
fi

SESSION="demo-coordination"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null || true

echo "📦 Creating AI team with --observe-only mode..."
python3 "$CREATE_TEAM" --session "$SESSION" --observe-only --yes

echo ""
echo "✅ Team created in observe-only mode!"
echo ""
echo "The team consists of:"
echo "  🎯 Alex: Perfectionist architect (focuses on quality)"
echo "  ⚡ Morgan: Pragmatic shipper (focuses on delivery)"
echo "  🧹 Sam: Code custodian (focuses on cleanup)"
echo ""
echo "Example coordination scenario to try:"
echo "1. Attach to session: tmux attach -t $SESSION"
echo "2. Ask the orchestrator to have the team design a REST API"
echo "3. Watch as:"
echo "   - Alex advocates for proper RESTful design and OpenAPI specs"
echo "   - Morgan pushes for a quick MVP with just working endpoints"
echo "   - Sam identifies potential technical debt and cleanup needs"
echo ""
echo "💡 Tip: The agents will disagree! The orchestrator mediates and finds balance."
echo ""
echo "To clean up:"
echo "  tmux kill-session -t $SESSION"
