#!/bin/bash

# Hello Orchestrator - Your first tmux orchestrator demo
# This demonstrates the basic setup and communication between agents

set -e

echo "🚀 Hello Orchestrator Demo - Basic Agent Communication"
echo "======================================================="
echo ""
echo "This demo will:"
echo "1. Create a tmux session with an orchestrator"
echo "2. Launch a simple agent that says hello"
echo "3. Show how agents communicate through tmux"
echo ""

# Check prerequisites
if ! command -v tmux &> /dev/null; then
    echo "❌ Error: tmux is not installed. Please install tmux first."
    exit 1
fi

# Create tmux session
SESSION="demo-hello"
echo "📦 Creating tmux session: $SESSION"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null || true

# Create new session with orchestrator pane
tmux new-session -d -s $SESSION -n main

# Split window for agent
tmux split-window -h -t $SESSION:main

# Send orchestrator message
echo "💬 Orchestrator starting..."
tmux send-keys -t $SESSION:main.0 "echo '🎯 Orchestrator: Ready to coordinate agents!'" Enter
sleep 1

# Send agent message
echo "🤖 Agent responding..."
tmux send-keys -t $SESSION:main.1 "echo '👋 Agent: Hello Orchestrator! Ready to work!'" Enter
sleep 1

# Show coordination
tmux send-keys -t $SESSION:main.0 "echo '📋 Orchestrator: Agent, please introduce yourself'" Enter
sleep 1
tmux send-keys -t $SESSION:main.1 "echo '🤖 Agent: I am a simple demo agent. I can process tasks!'" Enter
sleep 1

# Final message
tmux send-keys -t $SESSION:main.0 "echo '✅ Orchestrator: Great! Demo complete.'" Enter

echo ""
echo "✨ Demo session created!"
echo ""
echo "To view the demo:"
echo "  tmux attach -t $SESSION"
echo ""
echo "To clean up:"
echo "  tmux kill-session -t $SESSION"
echo ""
echo "💡 Tip: This is just the beginning. Check out the other demos for more advanced features!"
