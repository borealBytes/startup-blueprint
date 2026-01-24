# ADR-004: Explicit Error Recovery Procedures

**Status**: Accepted  
**Date**: 2026-01-12  
**Decision Maker**: [Your Name]  

---

## Problem Statement

When errors occur during development:
1. **Agents don't know what to do** (should they retry? escalate? rollback?)
2. **Humans don't know it happened** (error silently gets buried)
3. **Work is lost or conflicted** (no recovery procedures)
4. **Costs accumulate** (fixing error takes as long as original work)

**Current state**:
- ❌ Agents might panic and escalate unnecessarily
- ❌ Agents might make things worse trying to fix
- ❌ Humans unaware until much later
- ❌ No documented recovery procedures

---

## Constraints

1. **Error Types Vary**
   - Merge conflicts (technical, solvable)
   - Test failures (debugging, solvable)
   - Breaking changes (policy, needs human decision)
   - Unexpected issues (investigable, may need help)

2. **Some Errors Are Agent-Recoverable**
   - Merge conflicts
   - Lint/format errors
   - Test failures (often)
   - Build errors (sometimes)

3. **Some Errors Require Human**
   - Breaking changes
   - Security issues
   - Architectural problems
   - Data loss risks

4. **Escalation Must Be Clear**
   - Agents need explicit rules (ask first vs. handle yourself)
   - Humans need clear error descriptions
   - Recovery procedures must be documented

---

## Decision

**Create explicit error recovery procedures** with:

1. **Categorized errors**
   - Merge conflicts (recoverable)
   - Test failures (recoverable)
   - Lint/format errors (recoverable)
   - Build failures (investigable, may recover)
   - Breaking changes (STOP, ask human)
   - Security issues (STOP, ask human)
   - Data loss (STOP, ask human)

2. **Clear recovery steps for each**
   - What to do first
   - How to investigate
   - How to fix
   - How to verify
   - When to escalate

3. **Escalation template**
   - What error occurred (exact message)
   - What context (branch, task, status)
   - What was tried (recovery steps)
   - What human should do (specific question)

4. **Prevention tips**
   - What to do before coding
   - What to do while coding
   - What to do before pushing
   - What to do after pushing

---

## Consequences

### **Positive**

✅ **Agents know what to do**
- Clear procedures reduce uncertainty
- Confidence to attempt recovery
- Know when to escalate (explicit rules)
- Results in faster error resolution

✅ **Humans get clear error reports**
- Exact error message included
- Context provided (branch, task status)
- Recovery steps already attempted
- Clear question for human
- Reduces back-and-forth clarification

✅ **Fewer wasted attempts**
- Documented procedures prevent trial-and-error
- Proven recovery steps
- Less time debugging
- Less frustration

✅ **Scalable error handling**
- New agents can read procedures
- Consistent response to same error
- Training built-in (procedures = documentation)
- Errors become learning opportunities

✅ **Prevention awareness**
- Tips prevent many errors before they happen
- "Run tests before pushing" catches issues early
- "Pull before working" prevents conflicts
- Shifts from reactive to proactive

### **Negative / Trade-offs**

⚠️ **Requires maintaining procedures**
- As tools/frameworks change, procedures may need updating
- Mitigation: Review procedures every quarter, update as needed

⚠️ **Might not cover all errors**
- New error types might not be in list
- Mitigation: Procedure for unknown errors (investigate then escalate if stuck)

⚠️ **Agents might follow procedures wrong**
- If procedures misunderstood, error might worsen
- Mitigation: Clear step-by-step format, test with first errors

---

## Why This Over Alternatives?

### **Alternative 1: No documented procedures**

**Why rejected**:
- Agents make ad-hoc decisions
- Inconsistent responses to same error
- Humans unaware errors happened
- No learning/improvement over time

### **Alternative 2: Escalate everything**

**Why rejected**:
- Bottleneck on humans
- Simple errors (lint, format) need human approval
- Defeats purpose of having agents
- Slow development cycle

### **Alternative 3: "Try to fix, if stuck ask"**

**Why rejected**:
- Too vague (agents might make things worse)
- No clear criteria for "stuck"
- Humans don't know what was tried
- Creates more work, not less

**Chosen approach** wins because:
- ✅ Clear categories (agents know which applies)
- ✅ Specific procedures (agents follow steps)
- ✅ Escalation rules (agents know when to ask)
- ✅ Human context (humans get full error info)
- ✅ Preventive tips (fewer errors to recover from)

---

## Implementation

### **Phase 1: Procedures Documented**
- ✅ Created `agent_error_recovery.md`
- ✅ Covered 9 error categories
- ✅ Each has clear steps
- ✅ Escalation template provided
- ✅ Prevention tips included

### **Phase 2: Testing** (Pending)
- [ ] First agent encounters first error
- [ ] Follow documented procedures
- [ ] Verify procedure works
- [ ] Update procedure if needed
- [ ] Document what changed

### **Phase 3: Iteration** (Ongoing)
- [ ] Quarterly review of procedures
- [ ] Add new error types as discovered
- [ ] Refine steps based on experience
- [ ] Share learnings (update procedures)

---

## Metrics for Success

1. **Error resolution time**
   - Lint/format errors: < 5 minutes
   - Test failures: < 15 minutes
   - Merge conflicts: < 10 minutes
   - Build errors: < 20 minutes

2. **Agent recovery rate**
   - Merge conflicts: 100% agent-recoverable (no escalation)
   - Lint errors: 100% agent-recoverable
   - Test failures: 80%+ agent-recoverable
   - Build errors: 50%+ agent-recoverable

3. **Escalation clarity**
   - Breaking changes: Always escalated (0 missed)
   - Security issues: Always escalated (0 missed)
   - Humans get clear error descriptions (no "something broke")

4. **Prevention effectiveness**
   - Merge conflicts prevented (agent pulls before working)
   - Build failures reduced (agent tests locally first)
   - Lint errors reduced (agent formats before pushing)

---

## Related ADRs

- **ADR-001**: Perplexity Spaces architecture (provides framework for procedures)
- **ADR-003**: Idempotent scripts (prevents certain error classes)

---

## Open Questions

1. **What about database errors?**
   - Answer: Add to procedures when encountered. For now, escalate (safety first).

2. **What about performance issues (slow tests)?**
   - Answer: Investigate cause (new code? infrastructure?). Escalate if unclear.

3. **How to handle "ghost" errors (error that can't be reproduced)?**
   - Answer: Document context thoroughly. Escalate with full logs.

4. **Should agents attempt rollback?**
   - Answer: Never rollback autonomously. Escalate (human decision). Procedures prevent need.

---

## Approval

- **Proposed by**: AI Assistant
- **Date**: 2026-01-12
- **Status**: Ready for human review
- **Next step**: Test procedures with first real errors, refine as needed

---

## References

- `agent_error_recovery.md` — Full procedure documentation
- `autonomy_boundaries.md` — What agents can/cannot do (context for escalation)
- `workflow_guide.md` — Where errors might occur (context for prevention)
