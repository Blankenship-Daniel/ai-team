# v1.1 Dependency Injection Implementation Plan

## Architectural Decision

**USE EXISTING interfaces.py** - The protocols are well-designed and follow SOLID principles.

## Implementation Strategy

### 1. Create Implementation Files

Each interface gets its own implementation file:

```
implementations/
├── tmux_session_manager.py      # implements ITmuxSessionManager
├── agent_profile_factory.py     # implements IAgentProfileFactory
├── context_injector.py          # implements IContextInjector
├── security_validator_impl.py   # moves existing SecurityValidator
└── di_container.py              # Dependency injection container
```

### 2. Dependency Container

```python
# di_container.py
from typing import Dict, Any, Type

class DependencyContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type, implementation: Any) -> None:
        """Register implementation for interface"""
        self._services[interface] = implementation

    def register_singleton(self, interface: Type, implementation: Any) -> None:
        """Register singleton implementation"""
        self._singletons[interface] = implementation

    def resolve(self, interface: Type) -> Any:
        """Resolve implementation for interface"""
        if interface in self._singletons:
            return self._singletons[interface]
        if interface in self._services:
            return self._services[interface]()
        raise ValueError(f"No implementation registered for {interface}")
```

### 3. Refactor AITeamOrchestrator

```python
# create_ai_team.py
from interfaces import (
    ITmuxSessionManager,
    IAgentProfileFactory,
    IContextInjector,
    ISecurityValidator
)

class AITeamOrchestrator:
    def __init__(self, container: DependencyContainer,
                 non_interactive=False, observe_only=False):
        # Resolve dependencies from container
        self.session_manager = container.resolve(ITmuxSessionManager)
        self.profile_factory = container.resolve(IAgentProfileFactory)
        self.context_injector = container.resolve(IContextInjector)
        self.security_validator = container.resolve(ISecurityValidator)

        # Keep existing flags
        self.non_interactive = non_interactive
        self.observe_only = observe_only
```

### 4. Bootstrap in main()

```python
def main():
    # Setup DI container
    container = DependencyContainer()
    container.register_singleton(ITmuxSessionManager, TmuxSessionManagerImpl())
    container.register_singleton(IAgentProfileFactory, AgentProfileFactoryImpl())
    container.register_singleton(IContextInjector, UnifiedContextManager())
    container.register_singleton(ISecurityValidator, SecurityValidator())

    # Create orchestrator with dependencies
    orchestrator = AITeamOrchestrator(
        container,
        non_interactive=args.yes,
        observe_only=args.observe_only
    )
```

## Migration Path

### Phase 1: Context Manager Consolidation (IMMEDIATE)
1. Delete `agent_context_manager.py`
2. Delete `context_manager.py`
3. Keep only `unified_context_manager.py`
4. Update all imports

### Phase 2: Extract Implementations (Day 2)
1. Move tmux operations to `tmux_session_manager.py`
2. Move profile creation to `agent_profile_factory.py`
3. Keep SecurityValidator but make it implement ISecurityValidator

### Phase 3: Wire DI Container (Day 3)
1. Create `di_container.py`
2. Refactor AITeamOrchestrator constructor
3. Update main() to use container
4. Run full test suite

## Benefits

1. **Testability**: Mock any dependency for unit tests
2. **Flexibility**: Swap implementations without changing code
3. **Clarity**: Clear separation of concerns
4. **SOLID**: Proper dependency inversion

## No New Abstractions

The existing interfaces in `interfaces.py` are sufficient. We just need to:
1. Create concrete implementations
2. Wire them with DI container
3. Delete duplicate code

This is refactoring, not rewriting.
