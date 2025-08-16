#!/bin/bash
# context-status.sh - Quick context reminder for AI agents in tmux sessions

echo "🔄 TMUX COMMUNICATION CONTEXT"
echo "==============================="

# Show current location
echo "📍 Current Location:"
echo "   Session: $(tmux display-message -p '#{session_name}' 2>/dev/null || echo 'Unknown')"
echo "   Window:  $(tmux display-message -p '#{window_index}' 2>/dev/null || echo 'Unknown')"
echo "   Pane:    $(tmux display-message -p '#{pane_index}' 2>/dev/null || echo 'Unknown')"
echo "   Full ID: $(tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}' 2>/dev/null || echo 'Not in tmux')"
echo ""

# Show available communication tools
echo "🛠️  Communication Tools:"
if command -v send-claude-message.sh >/dev/null 2>&1; then
    echo "   ✅ send-claude-message.sh (in PATH)"
else
    echo "   ❌ send-claude-message.sh (missing from PATH)"
    if [ -f "./send-claude-message.sh" ]; then
        echo "   ✅ ./send-claude-message.sh (local)"
    fi
fi

if command -v schedule_with_note.sh >/dev/null 2>&1; then
    echo "   ✅ schedule_with_note.sh (in PATH)"
else
    echo "   ❌ schedule_with_note.sh (missing from PATH)"
    if [ -f "./schedule_with_note.sh" ]; then
        echo "   ✅ ./schedule_with_note.sh (local)"
    fi
fi

if [ -f "ORCHESTRATOR_GUIDE.md" ]; then
    echo "   ✅ ORCHESTRATOR_GUIDE.md (available)"
else
    echo "   ❌ ORCHESTRATOR_GUIDE.md (not found)"
fi
echo ""

# Show other agents/panes
echo "👥 Team Panes:"
if tmux list-panes -t "$(tmux display-message -p '#{session_name}'):$(tmux display-message -p '#{window_index}')" 2>/dev/null | grep -q .; then
    tmux list-panes -t "$(tmux display-message -p '#{session_name}'):$(tmux display-message -p '#{window_index}')" 2>/dev/null | while read line; do
        pane_num=$(echo "$line" | cut -d: -f1)
        echo "   Pane $pane_num: $(tmux display-message -t "$(tmux display-message -p '#{session_name}'):$(tmux display-message -p '#{window_index}').$pane_num" -p '#{pane_title}' 2>/dev/null || echo 'Agent')"
    done
else
    echo "   (Not in a tmux session or single pane)"
fi
echo ""

# Quick command examples
echo "💬 Quick Commands:"
echo "   Message Agent 1: send-claude-message.sh $(tmux display-message -p '#{session_name}'):0.1 \"Hello\""
echo "   Message Agent 2: send-claude-message.sh $(tmux display-message -p '#{session_name}'):0.2 \"Hello\""
echo "   Message Agent 3: send-claude-message.sh $(tmux display-message -p '#{session_name}'):0.3 \"Hello\""
echo "   Check Agent 1:   tmux capture-pane -t $(tmux display-message -p '#{session_name}'):0.1 -p | tail -10"
echo ""

# Show working directory and git status
echo "📁 Working Directory: $(pwd)"
if git rev-parse --git-dir >/dev/null 2>&1; then
    echo "🔧 Git Branch: $(git branch --show-current 2>/dev/null || echo 'Unknown')"
    echo "📊 Git Status: $(git status --porcelain | wc -l | tr -d ' ') files changed"
fi
echo ""

echo "📖 For full guide: cat ORCHESTRATOR_GUIDE.md"
echo "🔄 Refresh context: ./context-status.sh"