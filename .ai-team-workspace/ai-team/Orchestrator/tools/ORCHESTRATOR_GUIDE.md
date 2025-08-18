# 🎯 Tmux Orchestrator Complete Guide
*Comprehensive guide for AI team coordination with multi-bridge system*

## 🚀 Quick Start

You are the **Orchestrator** managing a team of AI agents in tmux panes. This guide covers everything from basic communication to advanced multi-bridge coordination.

### Your Environment
```bash
# Check your current location
tmux display-message -p "#{session_name}:#{window_index}.#{pane_index}"
# Expected: Tmux-Orchestrator:0.0 (you are the orchestrator)
```

## 📐 Team Layout

### Standard Layout
```
┌─────────────────────────────────────────────────┐
│                 Orchestrator                    │ <- You (pane 0.0)
├───────────────┬───────────────┬─────────────────┤
│     Alex      │    Morgan     │      Sam        │
│ (pane 0.1)    │  (pane 0.2)   │   (pane 0.3)    │
│ Architect     │  Pragmatist   │   Custodian     │
└───────────────┴───────────────┴─────────────────┘
```

### Agent Personalities
- **Alex (0.1)**: Perfectionist Architect - SOLID principles, clean code
- **Morgan (0.2)**: Pragmatic Shipper - MVP approach, rapid delivery
- **Sam (0.3)**: Code Custodian - Technical debt, refactoring, quality

## 💬 Communication Methods

### Method 1: send-claude-message.sh (Preferred)
```bash
# Send message to specific agent
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, review the authentication logic"
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, can you implement the API endpoint?"
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, please audit the security validator"

# Broadcast to all agents
./send-claude-message.sh Tmux-Orchestrator:0.1 "Team meeting: discuss the new requirements"
./send-claude-message.sh Tmux-Orchestrator:0.2 "Team meeting: discuss the new requirements"
./send-claude-message.sh Tmux-Orchestrator:0.3 "Team meeting: discuss the new requirements"
```

### Method 2: Direct tmux Commands (Fallback)
```bash
# If send-claude-message.sh is unavailable
tmux send-keys -t Tmux-Orchestrator:0.1 "Your message here" Enter
tmux send-keys -t Tmux-Orchestrator:0.2 "Your message here" Enter
tmux send-keys -t Tmux-Orchestrator:0.3 "Your message here" Enter
```

## 👀 Monitoring & Status

### Agent Activity Monitoring
```bash
# Check recent agent output (last 20 lines)
tmux capture-pane -t Tmux-Orchestrator:0.1 -p | tail -20  # Alex
tmux capture-pane -t Tmux-Orchestrator:0.2 -p | tail -20  # Morgan
tmux capture-pane -t Tmux-Orchestrator:0.3 -p | tail -20  # Sam

# Check all agents at once
for i in {1..3}; do
    echo "=== Agent $i ==="
    tmux capture-pane -t Tmux-Orchestrator:0.$i -p | tail -10
done
```

### Session Health Check
```bash
# Verify all panes are responsive
tmux list-panes -t Tmux-Orchestrator:0

# Check if agents are running Claude
tmux capture-pane -t Tmux-Orchestrator:0.1 -p | grep -q "claude" && echo "Alex: Active" || echo "Alex: Inactive"
tmux capture-pane -t Tmux-Orchestrator:0.2 -p | grep -q "claude" && echo "Morgan: Active" || echo "Morgan: Inactive"
tmux capture-pane -t Tmux-Orchestrator:0.3 -p | grep -q "claude" && echo "Sam: Active" || echo "Sam: Inactive"
```

## 🌉 Multi-Bridge Coordination System

### Bridge Registry Overview
The multi-bridge system enables coordination between multiple orchestrator teams.

```bash
# View bridge registry status
python3 bridge_registry.py list

# Create bridge to another team
python3 bridge_registry.py create "Tmux-Orchestrator" "External-Team" "Feature collaboration"

# Check your team's bridges
python3 bridge_registry.py status "Tmux-Orchestrator"
```

### Bridge Directory Structure
```
.ai-coordination/
├── registry/
│   ├── bridges/           # Bridge configurations
│   ├── sessions/          # Session mappings
│   └── active-bridges.json
├── messages/              # Inter-team messages
│   └── bridge-{id}/      # Messages per bridge
├── cleanup/               # Cleanup logs
└── bridge_context.json   # Legacy compatibility
```

### Bridge Communication Workflow

#### 1. Establish Bridge Connection
```bash
# Example: Connect with SNES development team
python3 bridge_registry.py create \
  "Tmux-Orchestrator" \
  "SNES-Modder" \
  "ROM analysis and debugging collaboration"
```

#### 2. Send Messages to Peer Teams
```bash
# Send message to peer team (auto-detected)
./send-to-peer-snes-modder.sh "Please analyze the sound driver at $7E2000"

# Check for incoming messages
./check-peer-messages.sh
```

#### 3. Monitor Bridge Status
```bash
# View all active bridges
python3 bridge_registry.py list

# Check bridge health
./bridge-status.sh

# Clean up old bridges (7+ days)
python3 bridge_registry.py cleanup --max-age-days 7
```

## 🛠️ Task Management & Coordination

### Assigning Work Based on Agent Strengths

#### Alex (Architect) - Best for:
```bash
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, design the authentication system architecture"
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, review this code for SOLID principle violations"
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, create interface definitions for the API layer"
```

#### Morgan (Pragmatist) - Best for:
```bash
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, implement the user registration endpoint quickly"
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, create an MVP for the dashboard feature"
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, integrate the third-party payment API"
```

#### Sam (Custodian) - Best for:
```bash
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, audit the codebase for security vulnerabilities"
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, refactor the legacy user service"
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, update dependencies and fix deprecation warnings"
```

### Coordinated Team Workflows

#### Code Review Process
```bash
# 1. Morgan implements feature
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, implement the user profile feature"

# 2. Alex reviews architecture
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, review Morgan's user profile implementation for architecture concerns"

# 3. Sam reviews quality
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, audit Morgan's user profile code for technical debt and security"

# 4. Orchestrator consolidates feedback
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, address Alex's architecture feedback and Sam's quality concerns before merging"
```

#### Technical Debt Management
```bash
# 1. Sam identifies debt
./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, analyze the authentication module for technical debt"

# 2. Alex designs solution
./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, design a refactoring plan for the authentication technical debt Sam identified"

# 3. Morgan implements pragmatically
./send-claude-message.sh Tmux-Orchestrator:0.2 "Morgan, implement Alex's refactoring plan efficiently while maintaining existing functionality"
```

## 🔧 Advanced Features

### Context Management
```bash
# Save current context
./context-status.sh save "feature-implementation-checkpoint"

# Restore context
./context-status.sh restore "feature-implementation-checkpoint"

# View context history
./context-status.sh list
```

### Agent Workspace Management
```bash
# View agent workspaces
ls -la agent-workspaces/
├── alex/     # Alex's personal workspace
├── morgan/   # Morgan's personal workspace
└── sam/      # Sam's personal workspace

# Access agent-specific tools
ls agent-workspaces/sam/tools/
├── debt-analyzer.sh
├── refactoring-toolkit.sh
└── quality-metrics.sh
```

### Automated Quality Gates
```bash
# Run pre-commit hooks (maintained by Sam)
pre-commit run --all-files

# Run test suite (coordinated by Alex)
pytest --cov=. -v

# Check technical debt (monitored by Sam)
./quality_automation.py --check-debt --generate-report
```

## 🚨 Troubleshooting

### Communication Issues

#### Agent Not Responding
```bash
# Check if agent pane exists
tmux list-panes -t Tmux-Orchestrator:0

# Check if Claude is running in agent pane
tmux capture-pane -t Tmux-Orchestrator:0.1 -p | tail -5

# Restart agent if needed
tmux send-keys -t Tmux-Orchestrator:0.1 C-c  # Stop current process
tmux send-keys -t Tmux-Orchestrator:0.1 "claude --permission-mode bypassPermissions" Enter
```

#### Bridge Communication Failures
```bash
# Check bridge status
python3 bridge_registry.py status "Tmux-Orchestrator"

# Test bridge connectivity
./bridge-status.sh

# Clean up broken bridges
python3 bridge_registry.py cleanup --dry-run  # Preview cleanup
python3 bridge_registry.py cleanup            # Execute cleanup
```

### Performance Issues

#### Session Memory Usage
```bash
# Check tmux session resource usage
tmux list-sessions -F "#{session_name}: #{session_windows} windows"

# Monitor pane output buffer
tmux show-options -g history-limit
```

#### Bridge Message Backlog
```bash
# Check message directory size
du -sh .ai-coordination/messages/

# Clean old messages
python3 bridge_registry.py cleanup --max-age-days 3
```

## 📋 Best Practices

### Effective Orchestration

1. **Clear Task Assignment**
   - Specify exactly what you want each agent to accomplish
   - Include relevant context and constraints
   - Set clear success criteria

2. **Agent Personality Matching**
   - Alex: Complex architecture, design patterns, long-term maintainability
   - Morgan: Feature implementation, integration, rapid prototyping
   - Sam: Code quality, refactoring, technical debt, security

3. **Communication Patterns**
   - Use specific, actionable language
   - Reference file paths and line numbers when relevant
   - Provide business context for technical decisions

### Quality Assurance

1. **Code Review Workflow**
   ```bash
   # Always follow this sequence:
   # 1. Morgan implements
   # 2. Alex reviews architecture
   # 3. Sam reviews quality
   # 4. Orchestrator consolidates
   ```

2. **Technical Debt Management**
   ```bash
   # Weekly debt review with Sam
   ./send-claude-message.sh Tmux-Orchestrator:0.3 "Sam, provide weekly technical debt report"

   # Monthly architecture review with Alex
   ./send-claude-message.sh Tmux-Orchestrator:0.1 "Alex, assess overall system architecture health"
   ```

### Bridge Coordination

1. **Inter-Team Communication**
   - Establish clear coordination context when creating bridges
   - Use descriptive bridge names and contexts
   - Monitor bridge activity regularly

2. **Message Management**
   - Send structured, specific messages to peer teams
   - Include relevant technical details and context
   - Follow up on important coordination requests

## 🔗 Quick Reference Commands

### Essential Commands
```bash
# Send message to agent
./send-claude-message.sh Tmux-Orchestrator:0.{1|2|3} "message"

# Check agent status
tmux capture-pane -t Tmux-Orchestrator:0.{1|2|3} -p | tail -10

# Bridge management
python3 bridge_registry.py {list|create|status|cleanup}

# Context management
./context-status.sh {save|restore|list}

# Quality automation
pre-commit run --all-files
pytest --cov=. -v
```

### Agent-Specific Shortcuts
```bash
# Alex (Architecture)
alias alex="./send-claude-message.sh Tmux-Orchestrator:0.1"

# Morgan (Implementation)
alias morgan="./send-claude-message.sh Tmux-Orchestrator:0.2"

# Sam (Quality)
alias sam="./send-claude-message.sh Tmux-Orchestrator:0.3"

# Usage: alex "Design the new API layer"
```

---

## 📚 Additional Resources

- **REFACTORING_BLUEPRINT.md**: Systematic refactoring patterns
- **DEBT.md**: Current technical debt assessment
- **PRODUCTION_CHECKLIST.md**: Pre-deployment verification
- **docs/**: Comprehensive documentation library

---

*This guide is maintained by the AI team. Last updated: $(date +%Y-%m-%d)*
