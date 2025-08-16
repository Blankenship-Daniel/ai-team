#!/bin/bash
# Agent Context Recovery Script
# Run this if you lose context or tools

echo "=== RESTORING AGENT CONTEXT ==="

# 1. Show core knowledge
cat << 'EOF'

## CRITICAL AGENT KNOWLEDGE

### Communication Protocol
- Use `tmux send-keys -t session:window "message"` to communicate
- Check other agents: `tmux capture-pane -t session:window -p | tail -20`
- Your session/window: Use `tmux display-message -p "#{session_name}:#{window_index}"`

### Tool Creation (If Not Available)
If send-claude-message.sh is not available, create it:
```bash
cat > send-claude-message.sh << 'EOF'
#!/bin/bash
WINDOW="$1"
shift
MESSAGE="$*"
tmux send-keys -t "$WINDOW" "$(printf '%q' "$MESSAGE")"
sleep 1
tmux send-keys -t "$WINDOW" Enter
echo "Message sent to $WINDOW: $MESSAGE"
EOF
chmod +x send-claude-message.sh
```

### Git Discipline (MANDATORY)
1. **Commit every 30 minutes**: `git add -A && git commit -m "Progress: [what you did]"`
2. **Before task switches**: ALWAYS commit
3. **Tag stable versions**: `git tag stable-[feature]-$(date +%Y%m%d)`

### Error Recovery
- If tmux fails: Log error to ERROR.log
- If git conflicts: Create CONFLICT.md with details
- If blocked: Message orchestrator immediately

EOF

# 2. Create missing tools
if [ ! -f "./send-claude-message.sh" ]; then
    echo "Creating send-claude-message.sh..."
    cat > send-claude-message.sh << 'TOOL'
#!/bin/bash
WINDOW="$1"
shift
MESSAGE="$*"
tmux send-keys -t "$WINDOW" "$(printf '%q' "$MESSAGE")"
sleep 1
tmux send-keys -t "$WINDOW" Enter
echo "Message sent to $WINDOW: $MESSAGE"
TOOL
    chmod +x send-claude-message.sh
    echo "✓ Created send-claude-message.sh"
fi

# 3. Check environment
echo ""
echo "Environment Check:"
echo "- Working Directory: $(pwd)"
echo "- Tmux Session: $(tmux display-message -p '#{session_name}')"
echo "- Window/Pane: $(tmux display-message -p '#{window_index}.#{pane_index}')"

echo ""
echo "=== CONTEXT RESTORED ==="
echo "You can now continue with your tasks."
