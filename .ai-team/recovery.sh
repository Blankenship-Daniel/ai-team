#!/bin/bash
echo "🔧 AI Team Context Recovery"
echo "Working directory: $(pwd)"
echo ""
echo "Re-establishing context for all agents..."
for pane in 0 1 2 3; do
    tmux send-keys -t ai-team:0.$pane "# Context restored: $(pwd)" Enter
done
echo "✅ Context restoration complete"
