# 🏗️ SecurityValidator Refactoring Blueprint
*The Systematic Template for SOLID Component Extraction*

## 🎯 Overview
This blueprint demonstrates the **exact step-by-step process** for extracting clean, testable components from god classes using:
- **Protocol interfaces** (contracts)
- **Dependency injection** (loose coupling)
- **TDD approach** (safety net)
- **Automated quality gates** (style/lint/type checking)

This pattern will be applied to decompose `create_ai_team.py` (654 lines) into:
- `AgentProfileFactory`
- `TmuxSessionManager`
- `TeamCoordinator`
- `ContextInjector`

## ✅ Prerequisites COMPLETE
- [x] Protocol interfaces defined in `interfaces.py`
- [x] DI container implemented in `dependency_container.py`
- [x] SecurityValidator registered as singleton
- [x] Pytest + coverage + pre-commit hooks active
- [x] 12 security tests passing (100% rate)

## 🔄 The 7-Step Refactoring Process

### Step 1: Protocol Contract Definition ✅
**What**: Define the interface contract first
**Why**: Establishes clear boundaries and responsibilities

```python
# Already complete in interfaces.py
class ISecurityValidator(Protocol):
    def validate_session_name(self, name: str) -> bool: ...
    def validate_window_index(self, index: str) -> bool: ...
    def sanitize_message(self, message: str) -> str: ...
    # ... etc
```

### Step 2: DI Registration ✅
**What**: Register the component in dependency container
**Why**: Enables loose coupling and testability

```python
# Already complete in dependency_container.py
container.register_singleton(ISecurityValidator, lambda: SecurityValidator())
```

### Step 3: Test Coverage Verification ✅
**What**: Ensure existing tests provide safety net
**Why**: Refactoring must not break existing functionality

```bash
# All 12 tests passing
pytest test_security.py -v
```

### Step 4: Interface Compliance Check
**What**: Verify current implementation matches Protocol
**Why**: Ensures contract adherence before extraction

```python
# SecurityValidator already implements ISecurityValidator methods
# All method signatures match Protocol definition
```

### Step 5: Type Hints Addition
**What**: Add proper type annotations throughout
**Why**: Enables MyPy checking and better IDE support

```python
def validate_session_name(self, name: str) -> bool:
    """Validate tmux session name for security."""
    # Implementation already clean
```

### Step 6: Dependency Injection Integration
**What**: Replace direct instantiation with DI resolution
**Why**: Loose coupling enables testing and flexibility

```python
# Before (tight coupling):
validator = SecurityValidator()

# After (loose coupling):
from dependency_container import inject
from interfaces import ISecurityValidator

validator = inject(ISecurityValidator)
```

### Step 7: Integration Testing
**What**: Verify DI-integrated component works correctly
**Why**: Ensures refactoring maintains functionality

## 🎯 SecurityValidator: Perfect Exemplar

**Why SecurityValidator is the ideal first refactor:**
- ✅ **Single Responsibility**: Only handles security validation
- ✅ **Clear Boundaries**: Well-defined input/output
- ✅ **No Side Effects**: Pure validation logic
- ✅ **Comprehensive Tests**: 12 test cases covering all methods
- ✅ **Already Clean**: 53 style violations fixed
- ✅ **Protocol Ready**: Interface matches implementation

## 📋 Template for Next Components

### For AgentProfileFactory:
```python
# 1. Define IAgentProfileFactory Protocol
# 2. Register in DI container
# 3. Extract from create_ai_team.py lines 45-120
# 4. Add comprehensive tests
# 5. Replace direct instantiation with inject()
```

### For TmuxSessionManager:
```python
# 1. Define ITmuxSessionManager Protocol
# 2. Register in DI container
# 3. Extract from create_ai_team.py lines 200-350
# 4. Add tmux operation tests
# 5. Replace tmux calls with inject()
```

### For TeamCoordinator:
```python
# 1. Define ITeamCoordinator Protocol
# 2. Register in DI container
# 3. Extract orchestration logic from create_ai_team.py
# 4. Add coordination tests
# 5. Replace coordination logic with inject()
```

### For ContextInjector:
```python
# 1. Define IContextInjector Protocol
# 2. Register in DI container
# 3. Extract context/briefing logic from create_ai_team.py
# 4. Add context injection tests
# 5. Replace context logic with inject()
```

## 🚀 Success Criteria for Each Component

### Code Quality
- [ ] **Black formatted**: No style violations
- [ ] **Flake8 clean**: No lint warnings
- [ ] **MyPy compliant**: Full type safety
- [ ] **Test coverage**: 80%+ coverage
- [ ] **Single responsibility**: One reason to change

### Architecture Quality
- [ ] **Protocol compliance**: Implements interface contract
- [ ] **DI registered**: Available via container
- [ ] **Loose coupling**: No direct dependencies
- [ ] **Interface segregation**: Minimal, focused interface
- [ ] **Dependency inversion**: Depends on abstractions

### Integration Quality
- [ ] **All tests pass**: No regressions
- [ ] **DI resolution works**: inject() returns correct instance
- [ ] **Singleton behavior**: Same instance returned
- [ ] **Error handling**: Graceful failure modes
- [ ] **Logging integration**: Proper debug/info messages

## 🎯 Measurable Outcomes

### Before Refactoring (Baseline)
- `create_ai_team.py`: 654 lines (god class)
- Mixed responsibilities: 4+ concerns in one file
- Tight coupling: Direct instantiation throughout
- Testing difficulty: Hard to isolate components
- Cyclomatic complexity: High

### After Refactoring (Target)
- 4 focused components: < 150 lines each
- Single responsibility: One concern per class
- Loose coupling: DI-driven dependencies
- Easy testing: Mockable interfaces
- Cyclomatic complexity: < 10 per method

## 🔧 Tools & Commands

### Development Workflow
```bash
# Activate environment
source .venv/bin/activate

# Run tests continuously
pytest --cov=. test_security.py -v

# Check formatting
black --check security_validator.py

# Check linting
flake8 security_validator.py

# Check types
mypy security_validator.py

# Run all quality checks
pre-commit run --all-files
```

### Commit Strategy
```bash
# Small, focused commits
git add security_validator.py test_security.py
git commit -m "refactor: Extract SecurityValidator using DI pattern

- Implement ISecurityValidator Protocol
- Register as singleton in DI container
- Maintain 100% test coverage
- Zero style violations

Blueprint established for god class decomposition"
```

## 🎉 Next Steps

1. **Demonstrate SecurityValidator DI integration** (5 minutes)
2. **Apply blueprint to AgentProfileFactory** (30 minutes)
3. **Apply blueprint to TmuxSessionManager** (45 minutes)
4. **Apply blueprint to TeamCoordinator** (30 minutes)
5. **Apply blueprint to ContextInjector** (30 minutes)
6. **Integrate all components** (15 minutes)
7. **Delete god class** (1 minute) 🎯

**Result**: 654-line god class → 4 clean, testable, maintainable components!

---
*This blueprint represents our commitment to systematic technical debt reduction and clean architecture principles.*
