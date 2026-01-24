# BUSINESS_NAME Agentic Development Space

> **🤖 YOU are the AI agent.** These instructions are for you—the AI assistant working on this codebase. When this documentation says "you" or "agent," that means you.
>
> Your job: autonomously write code, create PRs, and iterate on feedback—while humans control via design review, code review, and merge decisions.

---

## Perplexity Space Setup

If you are working in a Perplexity Space:

1. Paste this `instructions.md` into the Space instructions.
2. Upload the remaining files from `docs/agentic/` (including `docs/agentic/adr/`).
3. Keep the Space files in sync with the repo when updates land.

---

## Your Core References (Always Read First)

### 1. **Agentic Coding** (Comprehensive Specification) ⭐

`docs/agentic/agentic_coding.md`  
What you CAN/MUST/NEVER do, 14-step workflow, escalation rules, PR management.

### 2. **Autonomy Boundaries** (Quick Reference)

`docs/agentic/autonomy_boundaries.md`  
Capability matrix and escalation procedures.

### 3. **Workflow Guide** (Process Steps)

`docs/agentic/workflow_guide.md`  
14-step transparent process with human checkpoints.

---

## Backlog Usage (BACKLOG.md)

**Format convention:**

- Each backlog line is a checklist item: `- [ ] [P#] [domain] Description...` or `- [x] [P#] [domain] Description...`.
- **Status** is the checkbox: `[ ]` for open, `[x]` for done.
- **Priority** is one of `[P0]`, `[P1]`, `[P2]`, `[P3]` (P0 highest).
- **Domain** is a free-text tag like `[auth]`, `[infra]`, `[backend]`, `[ux]`.

**Adding items:**

- Put all new work into `## 📋 To Triage (New Items)` in `BACKLOG.md`.
- Use: `- [ ] [P#] [domain] Short description. Est: Nd.`  
  Example: `- [ ] [P1] [auth] Implement JWT auth ... Est: 2d.`
- Include enough detail that an agent can start a design doc without more clarification when possible.

**Updating items while working:**

- When starting work from a backlog item, create a feature branch and PR as usual, then append back on that same line:  
  `BRANCH: \`branch-name\` PR: #NNN` once those exist.
- Move the item between sections (`To Triage` → `High Priority` → `In Progress` → `Done`) by cutting/pasting the same line; keep the text (including BRANCH/PR) intact so agents can jump directly.
- When closing work, mark it checked (`- [x] ...`) and ensure final PR/issue links are present so future agents can trace context quickly.

This keeps the backlog as the **single lightweight index** for in-repo work, with a consistent `[status] [priority] [domain]` tag order agents can rely on.

---

## Before Starting Your Task

**Simple fixes or small features:**

- ✅ `contribute_standards.md` (code style, testing, docs)
- ✅ `custom-instructions.md` (repo-specific decisions)

**Complex refactors or infrastructure changes:**

- ✅ `operational_readiness.md` (constraints & limits)
- ✅ `context_budget_guide.md` (token management)
- ✅ `contribute_standards.md` (code standards)
- ✅ `custom-instructions.md` (repo-specific decisions)

---

## If Something Goes Wrong

- **Error occurred?** → `agent_error_recovery.md` (9 error categories, when to escalate)
- **Confused about file locations?** → `file_organization.md` (where files live)
- **Context window running low?** → `context_budget_guide.md` (when to create new thread)

---

## TL;DR: Your Capabilities & Boundaries

✅ **What You Can Do Autonomously:**

- Write code following standards
- Create branches with proper naming
- Make commits with Conventional Commits format
- Push to remote
- Create PRs with comprehensive descriptions
- Respond to feedback and iterate

❌ **What You Cannot Do:**

- Merge PRs (only humans merge)
- Deploy to production (only humans deploy)
- Approve your own PR (can't approve own work)
- Access GitHub Secrets (humans only)
- Force-push or rewrite history

📋 **When You Must Escalate (Ask first):**

- Breaking changes to APIs
- Security/authentication modifications
- Database schema changes
- Major architectural decisions
- Changes affecting 3+ workspaces

---

## The 3 Workflow Checkpoints

**Design Checkpoint (Step 5):** You document approach → Human reviews

**Code Review Checkpoint (Step 9):** You implement → Human reviews code quality

**Status Approval Checkpoint (Step 10):** You mark PR "Ready for Review" ONLY after human confirmation

---

## File Locations & Source of Truth

### Instruction Files (`docs/agentic/`)

**Location:** `docs/agentic/` in this repo  
**Purpose:** Your operating instructions and workflow guides  
**Source of truth:** This repo. For Spaces, upload copies of the same files.

### Development Work (Actual Code)

**Default branch:** `main` (unless human directs you to use another base branch)  
**Your workflow:**

```bash
# When starting new work:
git checkout main
git pull origin main
git checkout -b feat/your-feature-name

# Unless human says: "Branch from step/cloudflare-setup instead"
```

---

## Your Startup Checklist

1. ✅ Read `docs/agentic/instructions.md`
2. → Read `agentic_coding.md` (5-min, comprehensive spec)
3. → Read `autonomy_boundaries.md` (2-min, quick reference)
4. → Read `workflow_guide.md` (5-min, process steps)
5. → Ask the human to describe their task
6. → You decide what else to read based on task complexity

---

## All Files Available

**Core Documentation** (`docs/agentic/`):

- `README.md` - Visual overview with diagrams
- `agentic_coding.md` - Comprehensive agent specification ⭐
- `autonomy_boundaries.md` - Capability matrix
- `workflow_guide.md` - 14-step workflow
- `contribute_standards.md` - Code style, testing, docs
- `custom-instructions.md` - Repo-specific rules
- `operational_readiness.md` - System constraints & limits
- `context_budget_guide.md` - Token management
- `agent_error_recovery.md` - Error recovery procedures
- `file_organization.md` - File sync strategy

**Architecture Records** (`docs/agentic/adr/`):

- `ADR-001-perplexity-spaces.md` - Why this architecture
- `ADR-002-monorepo-structure.md` - Monorepo decisions
- `ADR-003-idempotent-scripts.md` - Deployment safety
- `ADR-004-error-recovery.md` - Error procedures

---

**Last updated:** 2026-01-24  
**Development base branch:** `main` (unless directed otherwise)  
**Status:** Production-ready
