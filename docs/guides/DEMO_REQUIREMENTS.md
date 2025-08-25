# Demo Validation Requirements - Alex

## Required Demos for v1.0

### 1. Team Coordination Demo
**Purpose**: Show how --observe-only prevents chaos in multi-agent scenarios

**Required Elements**:
- Start team with `--observe-only` flag
- Show agents introducing themselves WITHOUT starting work
- Demonstrate orchestrator assigning specific tasks
- Contrast with non-observe mode where agents might conflict

**Validation Criteria**:
- [ ] Uses --observe-only flag explicitly
- [ ] Agents wait for instructions
- [ ] No autonomous execution
- [ ] Clear security benefit demonstrated

### 2. Code Review Demo
**Purpose**: Demonstrate controlled code review process

**Required Elements**:
- Launch team in observe mode
- Orchestrator assigns code review to specific agent (Alex)
- Other agents remain idle until directed
- Show how this prevents multiple agents modifying same files

**Validation Criteria**:
- [ ] Single agent activation
- [ ] Other agents properly idle
- [ ] No file conflicts
- [ ] Audit trail visible

### 3. Technical Debt Demo
**Purpose**: Controlled technical debt analysis

**Required Elements**:
- Start with --observe-only
- Orchestrator requests debt assessment from Sam
- Sam provides analysis without making changes
- Orchestrator then authorizes specific fixes

**Validation Criteria**:
- [ ] Analysis before action
- [ ] Explicit authorization required
- [ ] No premature optimization
- [ ] Clear command flow

## Implementation Requirements

Each demo MUST include:

1. **Script or Documentation** showing exact commands
2. **--observe-only flag** prominently used
3. **Expected Output** demonstrating security benefits
4. **Contrast** with default (unsafe) mode

## Blocking Issues

Cannot approve v1.0 release without:
- Executable demo scripts OR
- Step-by-step demo documentation OR
- Video/screenshot evidence of demos working

Morgan must provide demo artifacts for validation.
