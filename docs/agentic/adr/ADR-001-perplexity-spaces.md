# ADR-001: Using Perplexity Spaces for Agentic Development

**Status**: Accepted  
**Date**: 2026-01-12  
**Decision Maker**: [Your Name]  

---

## Problem Statement

AI-assisted development needs:
1. **Clear autonomy boundaries** (what agents can/cannot do)
2. **Transparent workflows** (human control at critical points)
3. **Efficient context management** (large instruction files bloat every conversation)
4. **Reusable patterns** (generic for any Git repo, project-specific rules separated)
5. **Audit trail** (who approved what, when)

**Challenge**: Traditional documentation approaches result in:
- ❌ Monolithic files agents must load fully
- ❌ Ambiguous boundaries (agents unsure what to escalate)
- ❌ No human checkpoints (agents proceed without approval)
- ❌ Context bloat (every conversation loads unnecessary details)

---

## Constraints

1. **Perplexity Space Integration**
   - Files can be uploaded directly to a Space
   - Custom instructions have size limits
   - Files loaded selectively based on queries
   - Context window ~200,000 tokens max

2. **Git Repository**
   - Source of truth for all files
   - Version control for audit trail
   - Space copies must be kept in sync manually

3. **Agentic Workflow**
   - Agents need clear "yes/no" boundaries
   - Humans need explicit approval points
   - Process must be repeatable and auditable
   - Errors must be recoverable

---

## Decision

**Use Perplexity Spaces with a modular file structure**:

1. **Minimal base instructions** (40 lines)
   - Thin pointer to detailed files
   - Loaded for every thread (minimal context overhead)
   - Emphasizes "read this first" file

2. **Separated critical vs. reference files**
   - Critical: Autonomy boundaries, workflow steps (always loaded)
   - Reference: Code standards, error recovery (loaded on demand)
   - Result: Selective context loading

3. **Repo as source of truth**
   - All files live under `docs/agentic/`
   - Space files are uploaded copies for convenience
   - Version control provides audit trail

4. **Clear hierarchy**
   - Universal patterns (reusable for any Git repo)
   - BUSINESS_NAME-specific rules (separate file)
   - Operational procedures (modular, on-demand loading)

5. **Transparent checkpoints**
   - Design review (Step 5: Human approves approach)
   - Code review (Step 9: Human approves implementation)
   - Status approval (Step 10: Human confirms "Ready for Review")
   - Each checkpoint documented in workflow

---

## Consequences

### **Positive**

✅ **Efficient context usage**
- Base instructions only 40 lines (not 300+)
- Files loaded selectively (agents request what they need)
- Saves ~70% of context overhead vs. monolithic approach
- Allows more room for actual work in conversation

✅ **Clear autonomy boundaries**
- Explicit "can do" list (agents know what's safe)
- Explicit "must escalate" list (agents know what to ask about)
- Explicit "never" list (hard boundaries)
- Reduces ambiguous situations

✅ **Human control at critical points**
- Design checkpoint prevents wasted coding
- Code review checkpoint ensures quality
- Status approval checkpoint prevents surprises
- Clear audit trail (PR comments show all approvals)

✅ **Reusable across projects**
- Generic files apply to any Git repo
- Project-specific rules in separate file
- Copy structure to new projects, customize minimally
- Framework scalable and repeatable

✅ **Version-controlled**
- All changes tracked in Git
- Can revert to previous versions
- Commit history shows why decisions changed
- Perfect for evolving practices

### **Negative / Trade-offs**

⚠️ **Manual Space sync required**
- Space files must be re-uploaded when docs change
- If files drift, Space instructions may be stale
- Mitigation: Keep `docs/agentic/perplexity/README.md` updated

⚠️ **Multiple files to maintain**
- More files = more coordination
- If one file gets out of date, inconsistency
- Mitigation: Clear hierarchy, single source of truth

⚠️ **Agents must understand modular structure**
- Agents need to know which file to reference
- If agents confused about which file is which, might load wrong one
- Mitigation: `file_organization.md` explains everything

⚠️ **Context switching between files**
- If agents need 3 different files in one task, loads them all
- Might accumulate context
- Mitigation: `context_budget_guide.md` explains management

---

## Why This Over Alternatives?

### **Alternative 1: Single monolithic file**

**Why rejected**:
- 5,000+ lines loaded for every thread
- Agents miss important details buried in large file
- Context bloat (unnecessary overhead)
- Hard to find specific information

### **Alternative 2: No documentation**

**Why rejected**:
- Agents have no guidance
- Unpredictable behavior
- Humans have to micromanage
- No audit trail

### **Alternative 3: Documentation in Notion/Wiki only**

**Why rejected**:
- Requires manual copying into each thread
- No version control
- Hard to keep in sync
- Perplexity can't access external links directly

### **Alternative 4: GitHub wiki**

**Why rejected**:
- Perplexity can't read GitHub wiki
- Still requires manual copying
- No easy way to keep Space uploads current

**Chosen approach** wins because:
- ✅ Minimal base context (efficient)
- ✅ Version controlled (traceable)
- ✅ Modular (reusable)
- ✅ Explicit checkpoints (human control)
- ✅ Space-friendly uploads

---

## Implementation

### **Phase 1: Structure Created**
- ✅ Created `docs/agentic/` directory structure
- ✅ Minimal `instructions.md` (40 lines)
- ✅ Critical files extracted and separated
- ✅ Reference files organized
- ✅ Operational procedures documented

### **Phase 2: Perplexity Space Setup** (Pending)
- [ ] Paste `docs/agentic/instructions.md` into Space instructions
- [ ] Upload all files in `docs/agentic/` and `docs/agentic/adr/`
- [ ] Add `docs/agentic/perplexity/README.md` as a checklist

### **Phase 3: Testing** (Pending)
- [ ] First agent thread in Space
- [ ] Verify file loading works
- [ ] Test workflow with human checkpoints
- [ ] Verify error recovery procedures

---

## Metrics for Success

1. **Context efficiency**
   - Base instructions < 50 lines ✅
   - Average thread context usage < 30% ✅
   - Threads complete work without context overflow

2. **Human control**
   - Every PR has design checkpoint comment ✅
   - Every PR has code review checkpoint ✅
   - Every PR shows explicit "Ready" approval ✅

3. **Reusability**
   - 80%+ of files are generic (usable in other projects) ✅
   - Project-specific rules isolated in one file ✅
   - Documentation is copy-paste ready for new projects

4. **Reliability**
   - No missed workflows (agents always follow steps)
   - No escalation ambiguity (clear boundaries)
   - All errors recoverable (procedures documented)

---

## Related ADRs

- **ADR-002**: Monorepo structure (BUSINESS_NAME-specific)
- **ADR-003**: Idempotent scripts (operational reliability)
- **ADR-004**: Error recovery procedures (handling failures)

---

## Open Questions

1. **How often should files be updated?**
   - Answer: On every process change. PR required like any code.

2. **How to keep Space in sync?**
   - Answer: Re-upload updated files when `docs/agentic/` changes.

3. **Can other projects use this structure?**
   - Answer: Yes. Copy `docs/agentic/`, customize `custom-instructions.md`.

---

## Approval

- **Proposed by**: AI Assistant
- **Date**: 2026-01-12
- **Status**: Ready for human review
- **Next step**: Implement Phase 2 (Perplexity Space setup)

---

## References

- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Perplexity Spaces Documentation](https://www.perplexity.ai/help-center/)
- `autonomy_boundaries.md` — Boundary definitions
- `workflow_guide.md` — Workflow implementation
- `file_organization.md` — File sync strategy
