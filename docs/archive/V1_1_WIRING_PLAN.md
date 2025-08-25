# v1.1 Final Wiring Plan - Systematic Refactoring

## Current Status ✅
- DependencyContainer: Complete (50 lines)
- UnifiedContextManager: Protocol-compliant
- Implementations: Extracted by Morgan
- Bug fixes: Applied
- interfaces.py: Enhanced with IContextManager

## Final Wiring Steps

### Step 1: Refactor AITeamOrchestrator Constructor

**File:** `create_ai_team.py`

**BEFORE:**
```python
class AITeamOrchestrator:
    def __init__(self, non_interactive=False, observe_only=False):
        self.tmux = TmuxOrchestrator()
        self.session_name = "ai-team"
        self.agents: List[AgentProfile] = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_dir = os.getcwd()
        self.context_manager = UnifiedContextManager(install_dir=Path(self.script_dir))
        self.non_interactive = non_interactive
        self.observe_only = observe_only
```

**AFTER:**
```python
from interfaces import IAgentProfileFactory, ITmuxSessionManager, IContextInjector, ISecurityValidator
from implementations import DependencyContainer

class AITeamOrchestrator:
    def __init__(self, container: DependencyContainer, non_interactive=False, observe_only=False):
        # Resolve all dependencies through DI
        self.profile_factory = container.resolve(IAgentProfileFactory)
        self.session_manager = container.resolve(ITmuxSessionManager)
        self.context_injector = container.resolve(IContextInjector)
        self.security_validator = container.resolve(ISecurityValidator)

        # Keep configuration flags
        self.non_interactive = non_interactive
        self.observe_only = observe_only

        # Derived properties
        self.session_name = "ai-team"
        self.agents: List[AgentProfile] = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_dir = os.getcwd()
```

### Step 2: Update main() Bootstrap

**BEFORE:**
```python
def main():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()

    orchestrator = AITeamOrchestrator(non_interactive=args.yes, observe_only=args.observe_only)
    orchestrator.session_name = args.session
```

**AFTER:**
```python
from implementations import (
    DependencyContainer,
    AgentProfileFactory,
    TmuxSessionManager,
    UnifiedContextManager
)
from security_validator import SecurityValidator

def main():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()

    # Bootstrap DI container
    container = DependencyContainer()
    container.register_singleton(IAgentProfileFactory, AgentProfileFactory)
    container.register_singleton(ITmuxSessionManager, TmuxSessionManager)
    container.register_singleton(IContextInjector, UnifiedContextManager)
    container.register_singleton(ISecurityValidator, SecurityValidator)

    # Create orchestrator with injected dependencies
    orchestrator = AITeamOrchestrator(
        container=container,
        non_interactive=args.yes,
        observe_only=args.observe_only
    )
    orchestrator.session_name = args.session
```

### Step 3: Update Method Calls

Replace direct instantiation with dependency usage:

**Profile Creation:**
```python
# BEFORE
self.agents = self.create_agent_profiles()

# AFTER
self.agents = self.profile_factory.create_default_profiles()
```

**Session Management:**
```python
# BEFORE
if self.session_exists(self.session_name):
    # ... tmux operations

# AFTER
if self.session_manager.session_exists(self.session_name):
    # ... use session_manager methods
```

**Context Injection:**
```python
# BEFORE
enhanced_briefing = self.context_manager.inject_context_into_briefing(...)

# AFTER
enhanced_briefing = self.context_injector.inject_context(...)
```

### Step 4: Validation & Testing

1. **Syntax Check:**
   ```bash
   python3 -m py_compile create_ai_team.py
   ```

2. **Type Check:**
   ```bash
   mypy create_ai_team.py --ignore-missing-imports
   ```

3. **Integration Test:**
   ```bash
   python3 create_ai_team.py --session test-di --observe-only --yes
   ```

4. **Demo Verification:**
   ```bash
   cd Examples && ./02-team-coordination.sh
   ```

## Benefits of This Refactoring

1. **Testability:** Each dependency can be mocked independently
2. **Flexibility:** Swap implementations without code changes
3. **Clarity:** Clear separation between orchestration and implementation
4. **SOLID:** Proper dependency inversion achieved
5. **Maintainability:** Single responsibility for each class

## Quality Gates

Before tagging v1.1:
- [ ] All implementations follow their Protocol contracts
- [ ] DI container resolves all dependencies correctly
- [ ] Full test suite passes
- [ ] Demos work with new architecture
- [ ] No regressions from v1.0 functionality

## The Transformation

**v1.0:** Working code with technical debt
**v1.1:** Clean architecture with proper separation

This is disciplined refactoring - transform working code into well-organized code without breaking functionality.
