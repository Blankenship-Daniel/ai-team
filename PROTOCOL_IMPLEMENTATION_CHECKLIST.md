# Protocol Implementation Checklist for v1.1

## 🎯 IAgentProfileFactory
**File:** `implementations/agent_profile_factory.py`
**Current Code Location:** Lines 49-185 in `create_ai_team.py`

### Required Methods:
- [ ] `create_default_profiles() -> List[AgentProfile]`
  - Must return list with Alex, Morgan, and Sam profiles
  - Each profile needs: name, personality, role, briefing, window_name

- [ ] `create_custom_profile(name: str, role: str, personality_type: str) -> AgentProfile`
  - Generate custom agent based on personality type
  - Must include working directory in briefing

- [ ] `validate_profile(profile: AgentProfile) -> Tuple[bool, Optional[str]]`
  - Check all required fields are present
  - Validate name doesn't contain special characters
  - Return (True, None) if valid, (False, "error message") if not

---

## 🖥️ ITmuxSessionManager
**File:** `implementations/tmux_session_manager.py`
**Current Code Location:** Lines 187-278 in `create_ai_team.py`

### Required Methods:
- [ ] `create_session(session_info: SessionInfo) -> bool`
  - Create tmux session with working directory
  - Handle existing session (kill or error)
  - Return True on success

- [ ] `destroy_session(session_name: str) -> bool`
  - Kill tmux session safely
  - Return True even if session doesn't exist

- [ ] `session_exists(session_name: str) -> bool`
  - Check via `tmux has-session -t`
  - Handle subprocess errors gracefully

- [ ] `create_pane_layout(session_name: str, layout_config: Dict[str, Any]) -> bool`
  - Create 4-pane layout (orchestrator + 3 agents)
  - Set pane titles
  - Return True on success

- [ ] `send_to_pane(pane_target: str, message: str) -> bool`
  - Use `tmux send-keys`
  - Validate pane target first
  - Return True on success

---

## 🔐 IContextInjector
**File:** Use existing `unified_context_manager.py` - make it implement Protocol
**Current Code Location:** `unified_context_manager.py`

### Required Methods:
- [ ] `inject_context(briefing: str, role: str, environment: Dict[str, str]) -> str`
  - Add embedded context to briefing
  - Include role-specific context
  - Return enhanced briefing

- [ ] `create_workspace(session_name: str, agent_name: str) -> Path`
  - Create agent workspace directory
  - Copy/link necessary tools
  - Return workspace path

- [ ] `sanitize_briefing(briefing: str) -> str`
  - Remove dangerous characters
  - Escape quotes properly
  - Return safe briefing

### Note: UnifiedContextManager has similar methods - adapt them:
- `inject_context_into_briefing()` → rename to `inject_context()`
- `ensure_workspace()` → rename to `create_workspace()`
- Add `sanitize_briefing()` that calls SecurityValidator

---

## 🛡️ ISecurityValidator
**File:** Keep existing `security_validator.py` - already matches Protocol!
**Current Code Location:** `security_validator.py`

### Required Methods (ALREADY IMPLEMENTED):
- [x] `validate_session_name(session_name: str) -> Tuple[bool, Optional[str]]`
- [x] `validate_pane_target(pane_target: str) -> Tuple[bool, Optional[str]]`
- [x] `sanitize_message(message: str) -> str`
- [x] `validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]`

### Action: Just ensure class methods match Protocol signatures exactly

---

## 🎭 ITeamCoordinator
**File:** `implementations/team_coordinator.py`
**Current Code Location:** This IS `AITeamOrchestrator` - extract coordination logic

### Required Methods:
- [ ] `coordinate_team_creation(session_name: str, agents: List[AgentProfile], working_dir: str) -> Tuple[bool, Optional[str]]`
  - Orchestrate full team setup
  - Return (True, None) or (False, "error")

- [ ] `setup_orchestrator(session_name: str, working_dir: str) -> bool`
  - Start Claude in orchestrator pane
  - Send orchestrator briefing
  - Return True on success

- [ ] `verify_team_readiness(session_name: str, agents: List[AgentProfile]) -> Tuple[bool, List[str]]`
  - Check all panes exist
  - Verify Claude started in each
  - Return (True, []) or (False, ["issue1", "issue2"])

---

## 📦 IDependencyContainer
**File:** `implementations/di_container.py`
**New Implementation Required**

### Required Methods:
- [ ] `register(interface_type: type, implementation: Any) -> None`
  - Store mapping of interface → implementation

- [ ] `resolve(interface_type: type) -> Any`
  - Return implementation for interface
  - Raise error if not registered

- [ ] `register_singleton(interface_type: type, implementation: Any) -> None`
  - Store singleton instance
  - Return same instance on resolve

---

## ⚙️ IConfiguration
**File:** `implementations/configuration.py`
**Optional for v1.1 - defer to v1.2**

### Required Methods (DEFER):
- [ ] `get(key: str, default: Any = None) -> Any`
- [ ] `set(key: str, value: Any) -> None`
- [ ] `load_from_file(config_path: Path) -> None`

---

## 🌉 IMessageRouter & IBridgeEstablisher
**Files:** `implementations/message_router.py`, `implementations/bridge_establisher.py`
**Status:** DEFER TO v1.2 - Not used in current codebase

---

## Implementation Priority

### Phase 1 (Sam - TODAY):
1. Delete duplicate context managers
2. Make UnifiedContextManager implement IContextInjector

### Phase 2 (Morgan - Tomorrow):
1. Create `agent_profile_factory.py` - Extract from create_ai_team.py
2. Create `tmux_session_manager.py` - Extract tmux operations
3. Ensure SecurityValidator matches ISecurityValidator exactly

### Phase 3 (Alex - Day 3):
1. Create `di_container.py`
2. Create `team_coordinator.py` or refactor AITeamOrchestrator
3. Wire everything in main()

## Validation Criteria

Each implementation MUST:
1. Implement ALL methods from the Protocol
2. Match the exact signature (parameters and return types)
3. Include proper error handling
4. Have clear docstrings
5. Follow existing code patterns from create_ai_team.py

## Testing Requirements

For each implementation:
1. Unit test each method independently
2. Integration test with real tmux sessions
3. Verify Protocol compliance with mypy
4. Ensure backward compatibility
