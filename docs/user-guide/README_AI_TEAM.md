# AI Team CLI

A command-line tool that creates an orchestrator and two strongly opinionated AI software engineers in tmux, based on the Tmux Orchestrator framework.

## 🚀 Quick Start

```bash
# Install globally
./install.sh

# Create your AI team
ai-team

# Connect to the session
tmux attach -t ai-team
```

## 🤖 Meet Your Team

## 🏗️ Pane Layout

```
┌─────────────────────────────────┐
│         Orchestrator            │ <- You (pane 0.0)
├─────────────┬───────────────────┤
│    Alex     │      Morgan       │
│ (pane 0.1)  │   (pane 0.2)      │
└─────────────┴───────────────────┘
```

### **Orchestrator** (You - Top Pane)
- Coordinates and mediates between the two engineers
- Makes final technical decisions
- Keeps the team focused on objectives

### **Alex "The Perfectionist"** (Bottom-Left Pane)
- **Focus**: Clean architecture, SOLID principles, comprehensive testing
- **Personality**: Detail-oriented, uncompromising on quality
- **Says things like**: "This needs proper error handling", "Where are the tests?", "Technical debt always comes due with interest"

### **Morgan "The Pragmatist"** (Bottom-Right Pane)
- **Focus**: Shipping MVP, delivering business value quickly
- **Personality**: Results-oriented, deadline-driven
- **Says things like**: "Perfect is the enemy of good", "Let's ship and iterate", "Users don't care about our internal architecture"

## 🎯 Use Cases

- **Code Reviews**: Watch them debate quality vs speed
- **Architecture Decisions**: Get both perfectionist and pragmatic perspectives
- **Project Planning**: Balance technical excellence with business needs
- **Learning**: See different engineering philosophies in action

## 📋 Commands

```bash
ai-team                    # Create default team
ai-team -s my-project      # Custom session name
ai-team --help             # Show help
```

## 🔧 Requirements

- **tmux**: Session management
- **Claude CLI**: AI agents (install via Claude's official CLI)
- **Python 3**: Runtime environment

> **Note**: All Claude instances are started with `--dangerously-skip-permissions` for seamless operation.

## 📖 Detailed Usage

See [AI_TEAM_USAGE.md](AI_TEAM_USAGE.md) for complete documentation.

## 🎭 What Makes This Special

Unlike typical AI assistants that are overly agreeable, these agents have:

- **Strong opinions** based on real engineering philosophies
- **Natural conflict** that leads to better solutions
- **Distinct personalities** that feel authentic
- **Professional disagreement** that stays constructive

## 🚧 Example Interaction

```
Orchestrator: "We need to add user authentication to our app"

Alex: "We should implement proper OAuth 2.0 with PKCE, comprehensive
      error handling, rate limiting, and full test coverage. This is
      security-critical code that needs to be bulletproof."

Morgan: "Let's start with a simple email/password system using a proven
        library like Auth0 or Firebase. We can add OAuth later once we
        validate the core user flow. Perfect security doesn't matter if
        we never ship."

Orchestrator: [Mediates and makes the final call]
```

This creates authentic engineering discussions that help you think through problems from multiple angles.

---

Built on the [Tmux Orchestrator](https://github.com/your-repo) framework for AI agent coordination.
