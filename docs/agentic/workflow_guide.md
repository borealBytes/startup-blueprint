# 14-Step Transparent Agentic Workflow

> Detailed walkthrough of the complete process with human checkpoints.

**Read this before creating a branch for new work.**

---

## The 14 Steps

### **Step 1: Human Creates Task**

```
Human: "Add dark mode toggle to website"
```

Agent receives clear task description.

---

### **Step 2: Agent Creates Branch**

```bash
git checkout -b feat/website-dark-mode
```

Branch naming: `feat/`, `fix/`, `docs/`, `chore/` prefix.

---

### **Step 3: Agent Documents Approach** ← NEW

```
Agent creates design doc:
- What: Dark mode toggle component
- Why: Improves accessibility and user experience
- How: CSS variables + localStorage
- Alternatives: System preference detection, per-device storage

Commit: "docs: add design notes for dark mode feature"
Push to remote
```

**Purpose**: Get feedback on APPROACH before spending time coding.

---

### **Step 4: Agent Creates Draft PR** ← MODIFIED

```
PR title: "feat(website): add dark mode toggle"

PR description includes:
✅ What: Clear feature description
✅ Why: Problem it solves
✅ How: Implementation approach (link to design doc from Step 3)
✅ Status: "🚧 Draft - Design review requested"

Mark as DRAFT (not Ready for Review)
```

**Purpose**: Make intent transparent before implementation.

---

### **Step 5: Human Reviews Design** ← NEW CHECKPOINT

```
Human reviews:
✅ Design doc from Step 3
✅ PR description

Human provides feedback:
✅ "Design looks good, proceed with implementation"
💬 "Let's discuss alternative approach"
⚠️ "Need to address [concern] before building"

Agent responds to feedback in PR comments
```

**Purpose**: Human steers approach BEFORE coding begins (saves ~3.5 hours if wrong direction).

---

### **Step 6: Agent Implements (After Design Approval)** ← MODIFIED

```
Once human approves approach:
✅ Write dark mode toggle component
✅ Add tests (unit + integration)
✅ Update documentation
✅ Add accessibility features

Commit: "feat(website): implement dark mode toggle"
Push to remote
```

**Purpose**: Code with confidence that approach is correct.

---

### **Step 7: GitHub Actions Run (Automatic)**

```bash
pnpm format          # Fix formatting
pnpm lint            # Fix linting issues
pnpm --filter website test   # Run tests
pnpm build           # Build website
```

**If issues found**:
→ Actions auto-commits: `chore: format and lint [skip ci]`
→ Branch shows green checks when resolved

---

### **Step 8: Agent Updates PR Status** ← NEW

```
Agent updates PR description with progress:
✅ Design review completed
✅ Implementation complete
✅ All tests passing
✅ Build verified

Summary: "Ready for code review. See test results above."

Comment in PR:
"Design and implementation complete.
See PR description status checklist.
Awaiting human confirmation before marking as Ready for Review."

DO NOT change from Draft to Ready yet
```

**Purpose**: Self-documenting progress. Human sees what's done.

---

### **Step 9: Human Provides Code Review** ← NEW CHECKPOINT

```
Human reviews:
✅ Actual implementation (code, tests, docs)
✅ Test coverage and results
✅ Accessibility and performance

Human provides feedback:
✅ "Code looks good. Mark as Ready for Review when ready."
💬 "Let's improve this edge case"
⚠️ "Need to add test for this scenario"

Agent responds to feedback (see Step 12 if needed)
```

**Purpose**: Human verifies implementation quality and explicitly confirms readiness.

---

### **Step 10: Agent Marks PR Ready** ← NEW (With Permission)

```
ONLY after human confirmation from Step 9:

Agent updates PR description:
🎯 Status: "Ready for Review - Approved by [human]"

Change from Draft to Ready for Review

Signals to other reviewers:
✅ Design approved
✅ Code approved
✅ Ready for merge decision
```

**Purpose**: Status change is intentional, not automatic. Clear audit trail.

---

### **Step 11: Agent Waits for Final Approval**

```
Agent monitors PR for:
✅ Watching for additional feedback
✅ Responding to comments if needed
✅ Awaiting final approval to merge

Agent CANNOT approve own PR
Agent CANNOT request approval from another agent
```

---

### **Step 12: Agent Responds to Feedback (If Any)**

```
If human provided feedback in Step 9:

Agent:
✅ Reads review comments carefully
✅ Makes requested changes
✅ Commits with clear message: "fix: address review feedback on mobile view"
✅ Pushes to same branch
✅ Responds in PR comments explaining changes
✅ Go back to Step 7 (GitHub Actions runs again)
```

---

### **Step 13: Human Merges**

```
Human:
✅ Final approval
✅ Clicks "Squash and merge" or "Merge"
✅ Branch auto-deleted
```

---

### **Step 14: Deployment (If Applicable)**

```
GitHub Actions may trigger:
✅ Staging deploy (if configured)

Production deploy requires:
✅ Additional human approval (humans only)
```

---

## The 3 Transparent Checkpoints

This workflow includes **3 clear human approval gates**:

| Checkpoint          | Step | When                   | Who   | Why                                         |
| ------------------- | ---- | ---------------------- | ----- | ------------------------------------------- |
| **Design Review**   | 5    | BEFORE coding          | Human | Steer approach early, prevent wasted effort |
| **Code Review**     | 9    | AFTER implementation   | Human | Verify quality before "Ready" status        |
| **Status Approval** | 10   | BEFORE marking "Ready" | Human | Intentional status change, not automatic    |

---

## Why This Workflow

### **Old Workflow** (10 steps, no checkpoints)

- Agent codes → Human reviews → Issue discovered → Agent rewrites
- **Cost**: 8+ hours for mistakes caught too late
- **Frustration**: Wasted effort on wrong direction

### **New Workflow** (14 steps, 3 checkpoints)

- Agent designs → Human approves → Agent codes → Human reviews
- **Cost**: 4.5 hours with early course correction
- **Clarity**: Transparent intent at every stage

**Time saved per rejected approach**: ~3.5 hours ⏱️

---

## Key Principles

### **Transparency**

- ✅ PR description documents progress
- ✅ Status is explicit (Draft vs. Ready)
- ✅ Human feedback is clear
- ✅ Audit trail shows all approvals

### **Human Control**

- ✅ Humans steer design early
- ✅ Humans approve approach before coding
- ✅ Humans review implementation
- ✅ Humans control PR status changes
- ✅ Humans decide merge

### **Efficiency**

- ✅ Design checkpoint prevents wasted coding
- ✅ Status updates prevent surprises
- ✅ Selective file loading manages context
- ✅ Clear boundaries reduce escalations

---

## Common Scenarios

### **Scenario: Design Gets Rejected**

```
Step 5: Human: "This direction won't work. Try approach B instead."

Agent response:
✅ Acknowledge feedback
✅ Update design doc with new approach
✅ Ask clarifying questions if needed
✅ Wait for approval
✅ THEN implement

Time saved: ~6 hours (avoided coding wrong approach)
```

### **Scenario: Code Needs Changes**

```
Step 9: Human: "Add test for edge case X"

Agent response:
✅ Implement edge case test
✅ Commit: "fix: add test for edge case X"
✅ Push to branch
✅ Respond in PR comment
✅ GitHub Actions runs again
✅ Wait for re-approval
```

### **Scenario: Build Fails in GitHub Actions**

```
Step 7: Build fails: "Lint error on line 42"

Agent response:
✅ See `agent_error_recovery.md` for error procedures
✅ Fix lint error
✅ Commit: "fix: resolve lint error"
✅ Push to branch
✅ GitHub Actions runs again
```

### **Scenario: Breaking Change Needed**

```
Step 3 (Design): Agent recognizes breaking change

Agent action:
✅ STOP (don't proceed)
✅ Ask in PR description: "Is this breaking change intentional?"
✅ Wait for human decision
✅ Proceed based on answer
```

---

## Quick Reference: When to Do What

| Step | Who        | Action                       | Status                  |
| ---- | ---------- | ---------------------------- | ----------------------- |
| 1    | Human      | Create task                  | -                       |
| 2    | Agent      | Create branch                | In progress             |
| 3    | Agent      | Document approach            | Awaiting review         |
| 4    | Agent      | Create Draft PR              | Awaiting design review  |
| 5    | **Human**  | **Review design**            | **CHECKPOINT 1**        |
| 6    | Agent      | Implement (if approved)      | In progress             |
| 7    | Automation | Run tests/lint               | In progress             |
| 8    | Agent      | Update PR status             | Awaiting code review    |
| 9    | **Human**  | **Review code**              | **CHECKPOINT 2**        |
| 10   | Agent      | Mark Ready (if approved)     | Awaiting merge          |
| 11   | Agent      | Wait                         | Awaiting final approval |
| 12   | Agent      | Respond to feedback (if any) | Back to Step 7          |
| 13   | **Human**  | **Merge**                    | Complete                |
| 14   | Automation | Deploy (if configured)       | Done                    |

---

## For More Information

- **Autonomy boundaries**: See `autonomy_boundaries.md`
- **Error recovery**: See `agent_error_recovery.md`
- **Company-specific rules**: See `custom-instructions.md`
- **Code standards**: See `contribute_standards.md`

---

**Remember**: This workflow is designed to catch issues early and keep humans in control. When in doubt, ask.
