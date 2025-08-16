# AI Team Context - Sat Aug 16 15:06:26 CDT 2025

## Working Directory
Path: /Users/ship/Documents/code/Tmux-Orchestrator

## Team Structure
- **Orchestrator** (pane 0.0): Coordinates the team
- **Alex** (pane 0.1): Perfectionist architect
- **Morgan** (pane 0.2): Pragmatic shipper  
- **Sam** (pane 0.3): Code custodian

## Communication Protocol
Use tmux send-keys or send-claude-message.sh:
```bash
send-claude-message.sh ai-team:0.1 "Message to Alex"
tmux capture-pane -t ai-team:0.1 -p | tail -20
```

## Important Locations
- Context: .ai-team/CONTEXT.md
- Status: .ai-team/STATUS.md
- Logs: logs/
- Agent workspaces: .ai-team/workspaces/

## Recovery
If agents lose context, run: .ai-team/recovery.sh
