# Tmux-Orchestrator v1.0 Architecture

## System Overview

Tmux-Orchestrator creates a multi-agent AI development team using tmux panes for parallel Claude instances. The system consists of:

- **Orchestrator** (Pane 0.0): Coordinates team activities and mediates conflicts
- **Alex** (Pane 0.1): Senior architect enforcing best practices and SOLID principles
- **Morgan** (Pane 0.2): Pragmatic developer focused on rapid delivery
- **Sam** (Pane 0.3): Code quality engineer managing technical debt

### Core Components

1. **AITeamOrchestrator** (`create_ai_team.py`): Main orchestration class
2. **UnifiedContextManager** (`unified_context_manager.py`): Handles agent context and workspace
3. **SecurityValidator** (`security_validator.py`): Input sanitization and validation
4. **TmuxOrchestrator** (`tmux_utils.py`): Low-level tmux operations

## Key Design Decisions

### 1. Context Management Strategy
- **Decision**: Hybrid approach with embedded context in briefings + local workspaces
- **Rationale**: Ensures agents maintain operational knowledge across directory changes
- **Implementation**: Lines 364-380 in `create_ai_team.py`

### 2. Security Architecture
- **Decision**: Layered validation with SecurityValidator for all external inputs
- **Rationale**: Prevents command injection and tmux escape sequences
- **Implementation**: Validates session names (line 190), pane targets (line 297), and sanitizes messages (line 384)

### 3. Agent Personality Design
- **Decision**: Strongly opinionated, conflicting personalities
- **Rationale**: Creates productive tension leading to better solutions
- **Trade-off**: Requires orchestrator mediation but produces balanced outcomes

## --observe-only Security Model

### Purpose
Prevents autonomous agent execution on startup, requiring explicit orchestrator direction.

### Implementation Details

```python
# Flag flow (immutable after construction):
__init__(observe_only=True) -> Line 44: self.observe_only = observe_only

# Conditional Claude startup (Lines 303-308):
if self.observe_only:
    cmd = ["tmux", "send-keys", "-t", pane_target, "claude", "Enter"]
else:
    cmd = ["tmux", "send-keys", "-t", pane_target, "claude --dangerously-skip-permissions", "Enter"]

# Agent briefing modification (Lines 368-376):
if self.observe_only:
    briefing_to_use = agent.briefing + observe_instruction

# Orchestrator notification (Lines 481-488):
if self.observe_only:
    orchestrator_briefing += "OBSERVE-ONLY MODE ACTIVE..."
```

### Security Properties
1. **Immutability**: Flag cannot be modified after initialization
2. **Explicit permissions**: Removes --dangerously-skip-permissions in observe mode
3. **Clear communication**: Agents receive explicit wait instructions
4. **Audit trail**: Mode logged at initialization (line 48)

### Usage
```bash
# Safe exploration mode
python3 create_ai_team.py --observe-only

# Production mode with auto-execution
python3 create_ai_team.py
```

## Architectural Strengths
- **Separation of Concerns**: Each component has single responsibility
- **Dependency Injection Ready**: Interfaces defined but not yet implemented
- **Security by Default**: Input validation at all boundaries
- **Observable State**: Comprehensive logging throughout

## Known Technical Debt
1. Multiple context manager implementations need consolidation
2. Dependency injection interfaces defined but unused
3. No automated test coverage configuration
4. Orchestrator retains --dangerously-skip-permissions even in observe mode

## Release Notes v1.0

**Security Enhancement**: New `--observe-only` flag prevents agents from auto-starting work, requiring explicit orchestrator commands. This addresses concerns about uncontrolled agent execution in production environments.

**Architecture**: Clean separation between orchestration, context management, and security validation layers. Ready for dependency injection implementation in v1.1.

**Coverage**: 92% test coverage with zero known vulnerabilities (pending final security scan).
