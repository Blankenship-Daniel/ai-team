# Getting Started with AI Team CLI

A command-line tool that creates an orchestrator and two strongly opinionated AI software engineers in tmux, based on the Tmux Orchestrator framework.

## Installation

Install the AI Team CLI globally:

```bash
./install.sh
```

## Quick Start

Create an AI team with one orchestrator and two opinionated engineers:

```bash
ai-team
```

Connect to the session:
```bash
tmux attach -t ai-team
```

## Team Overview

Your AI team consists of:
- **Orchestrator** - Coordinates between team members and manages high-level tasks
- **Engineer 1** - Opinionated software engineer focused on specific development approaches
- **Engineer 2** - Complementary engineer with different opinions and methodologies

## Pane Layout

The tmux session creates a split pane layout optimized for multi-agent coordination and real-time collaboration between AI team members.

## Next Steps

- See [Advanced Usage](advanced-usage.md) for detailed configuration options
- Check [Troubleshooting](../maintainer/troubleshooting.md) if you encounter issues
- Review [Architecture](../developer/CLAUDE.md) for technical implementation details
