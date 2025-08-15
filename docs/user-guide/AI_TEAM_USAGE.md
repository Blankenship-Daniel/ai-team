# AI Team CLI Usage Guide

## Installation

First, install the AI Team CLI globally:

```bash
./install.sh
```

## Quick Start

Create an AI team with one orchestrator and two opinionated engineers:

```bash
ai-team
```

This creates a tmux session with a split pane layout:

```
┌─────────────────────────────────┐
│         Orchestrator            │ <- You (pane 0.0)
├─────────────┬───────────────────┤
│    Alex     │      Morgan       │
│ (pane 0.1)  │   (pane 0.2)      │
└─────────────┴───────────────────┘
```

- **Orchestrator** (Pane 0.0): You coordinate and mediate between agents
- **Alex** (Pane 0.1): Perfectionist architect - quality-focused, advocates for best practices
- **Morgan** (Pane 0.2): Pragmatic shipper - speed-focused, advocates for MVP and shipping

## Usage

### Creating a Team
```bash
# Default team
ai-team

# Custom session name
ai-team --session my-dev-team

# With verbose output
ai-team --verbose
```

### Connecting to Your Team
```bash
# Attach to the session
tmux attach -t ai-team

# List all panes
tmux list-panes -t ai-team
```

### Navigating Panes
- `Ctrl+B, ↑` - Move to orchestrator pane
- `Ctrl+B, ↓` - Move to agent panes
- `Ctrl+B, ←/→` - Move between Alex and Morgan
- All agents are visible simultaneously!

## Agent Personalities

### Alex - The Perfectionist Architect
- **Focus**: Clean code, proper architecture, long-term maintainability
- **Beliefs**: "Code is read more than it's written", "If it's not tested, it's broken"
- **Style**: Direct, technical, will push back on shortcuts
- **Strengths**: Quality, testing, documentation, architectural decisions

### Morgan - The Pragmatic Shipper
- **Focus**: Delivering working software quickly, business value
- **Beliefs**: "Perfect is the enemy of good", "Ship early, ship often"
- **Style**: Results-oriented, deadline-driven, business-focused
- **Strengths**: Velocity, MVP thinking, user value, practical solutions

## Communication Examples

The orchestrator can send messages to agents:

```bash
# Message Alex about architecture
send-claude-message.sh ai-team:0.1 "Alex, what's your take on using microservices vs monolith for this project?"

# Message Morgan about timeline
send-claude-message.sh ai-team:0.2 "Morgan, we need to ship the MVP in 2 weeks. What would you prioritize?"

# Check what an agent said recently
tmux capture-pane -t ai-team:0.1 -p | tail -20
```

## Sample Scenarios

### Code Review Debate
Give both agents the same code to review - watch Alex focus on technical debt and testing while Morgan focuses on whether it solves the user problem.

### Architecture Decision
Present a technical decision (database choice, framework selection, etc.) and watch them debate the tradeoffs from their different perspectives.

### Timeline Pressure
Give them a project with a tight deadline and watch how they balance quality vs speed.

## Tips for the Orchestrator

1. **Let them debate**: The value comes from their different perspectives
2. **Ask specific questions**: "Alex, what are the risks?" "Morgan, what's the MVP version?"
3. **Make decisions when needed**: If they can't agree, you decide
4. **Keep them focused**: Redirect if they get off-topic
5. **Leverage their strengths**: Use Alex for quality/architecture, Morgan for user value/speed

## Troubleshooting

### Session Already Exists
The script will automatically kill and recreate existing sessions.

### Claude Not Starting
Make sure you have Claude CLI installed and accessible via the `claude` command.

### Messages Not Sending
Verify the `send-claude-message.sh` script is executable:
```bash
chmod +x send-claude-message.sh
```

### Pane Not Found
Check available panes:
```bash
tmux list-panes -t ai-team
```