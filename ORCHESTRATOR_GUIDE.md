# Orchestrator Communication Guide

## Quick Start
You are the Orchestrator for a team of AI agents working in tmux panes. This guide helps you communicate with and coordinate your team.

## Your Current Location
```bash
# Check your current pane location
tmux display-message -p "#{session_name}:#{window_index}.#{pane_index}"
```

## Team Layout
```
┌──────────────────────────────────────────┐
│             Orchestrator                 │ <- You are here (pane 0.0)
├────────────┬──────────────┬──────────────┤
│   Agent 1  │   Agent 2    │   Agent 3    │
│ (pane 0.1) │  (pane 0.2)  │  (pane 0.3)  │
└────────────┴──────────────┴──────────────┘
```

## Communication Methods

### Method 1: Using send-claude-message.sh (Preferred)
```bash
# Send message to specific agent
send-claude-message.sh Tmux-Orchestrator:0.1 "Your message here"
send-claude-message.sh Tmux-Orchestrator:0.2 "Your message here"
send-claude-message.sh Tmux-Orchestrator:0.3 "Your message here"

# The script is available in PATH and handles proper formatting
```

### Method 2: Direct tmux Commands (Fallback)
```bash
# If send-claude-message.sh is not available
tmux send-keys -t session:window.pane "Your message" Enter

# Example:
tmux send-keys -t Tmux-Orchestrator:0.1 "Hello Agent 1" Enter
```

## Monitoring Agent Progress

### View Recent Output
```bash
# Check what an agent is doing (last 20 lines)
tmux capture-pane -t Tmux-Orchestrator:0.1 -p | tail -20
tmux capture-pane -t Tmux-Orchestrator:0.2 -p | tail -20
tmux capture-pane -t Tmux-Orchestrator:0.3 -p | tail -20
```

### View Full Pane Content
```bash
# See everything in an agent's pane
tmux capture-pane -t Tmux-Orchestrator:0.1 -p
```

## Creating Missing Tools

### If send-claude-message.sh is missing:
```bash
cat > send-claude-message.sh << 'EOF'
#!/bin/bash
WINDOW="$1"
shift
MESSAGE="$*"
tmux send-keys -t "$WINDOW" "$MESSAGE"
sleep 1
tmux send-keys -t "$WINDOW" Enter
echo "Message sent to $WINDOW: $MESSAGE"
EOF
chmod +x send-claude-message.sh
```

## Common Orchestrator Tasks

### 1. Initial Team Setup
```bash
# Introduce yourself to all agents
send-claude-message.sh Tmux-Orchestrator:0.1 "Hello Agent 1, I'm your Orchestrator..."
send-claude-message.sh Tmux-Orchestrator:0.2 "Hello Agent 2, I'm your Orchestrator..."
send-claude-message.sh Tmux-Orchestrator:0.3 "Hello Agent 3, I'm your Orchestrator..."
```

### 2. Assign Tasks
```bash
# Delegate specific work
send-claude-message.sh Tmux-Orchestrator:0.1 "Please work on the frontend components"
send-claude-message.sh Tmux-Orchestrator:0.2 "Focus on API integration"
send-claude-message.sh Tmux-Orchestrator:0.3 "Handle testing and documentation"
```

### 3. Coordinate Collaboration
```bash
# Facilitate agent-to-agent communication
send-claude-message.sh Tmux-Orchestrator:0.1 "Agent 2 needs your API schema"
send-claude-message.sh Tmux-Orchestrator:0.2 "Please share your progress with Agent 1"
```

### 4. Check Progress
```bash
# Regular status checks
for pane in 0.1 0.2 0.3; do
  echo "=== Agent in pane $pane ==="
  tmux capture-pane -t Tmux-Orchestrator:$pane -p | tail -10
done
```

## Git Best Practices

### Regular Commits (Every 30 minutes)
```bash
git add -A && git commit -m "Progress: [description]"
```

### Before Task Switches
```bash
git status
git add -A && git commit -m "Checkpoint: Switching from [task A] to [task B]"
```

## Troubleshooting

### Agent Not Responding?
1. Check if pane exists: `tmux list-panes -t Tmux-Orchestrator`
2. View full output: `tmux capture-pane -t Tmux-Orchestrator:0.1 -p`
3. Send a simple test: `send-claude-message.sh Tmux-Orchestrator:0.1 "Status check"`

### Lost Context?
1. Review this guide
2. Check working directory: `pwd`
3. List available tools: `ls *.sh`
4. Check git status: `git status`

### Session Issues?
```bash
# List all tmux sessions
tmux list-sessions

# List all windows in current session
tmux list-windows

# List all panes in current window
tmux list-panes
```

## Important Reminders

1. **Always use absolute paths** when referencing files outside current directory
2. **Commit frequently** to preserve work
3. **Coordinate agents** - they can't see each other's work directly
4. **Monitor progress** - agents may get stuck or need guidance
5. **Use this guide** whenever you need to remember communication protocols

## Environment Variables
- Working Directory: Set by the context when team is created
- Tools Location: Usually in PATH or current directory
- Session Name: Typically "Tmux-Orchestrator"

---
*This guide is automatically deployed when creating new AI teams to ensure orchestrators can always coordinate their agents effectively.*