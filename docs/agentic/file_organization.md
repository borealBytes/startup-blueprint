# File Organization & Synchronization

> Where files live, which version to use, and how sync works.

**Read this when**: Confused about file locations or which version to trust.  
**Don't read this**: Until you need file location clarity (saves context).

---

## Source of Truth

### Repo is Source of Truth

**This repository** contains:
- ✅ All official files
- ✅ Complete history (git commits)
- ✅ Latest version
- ✅ Backup of everything

**Location**: `docs/agentic/`

**Path structure**:
```
startup-blueprint/
└── docs/
    └── agentic/
        ├── instructions.md
        ├── agentic_coding.md
        ├── autonomy_boundaries.md
        ├── workflow_guide.md
        ├── contribute_standards.md
        ├── custom-instructions.md
        ├── operational_readiness.md
        ├── context_budget_guide.md
        ├── agent_error_recovery.md
        ├── file_organization.md
        └── adr/
            ├── ADR-001-perplexity-spaces.md
            ├── ADR-002-monorepo-structure.md
            ├── ADR-003-idempotent-scripts.md
            └── ADR-004-error-recovery.md
```

---

## Perplexity Space Copies

**Perplexity Space** should contain:
- ✅ `instructions.md` pasted into Space instructions
- ✅ The rest of `docs/agentic/` uploaded as files
- ✅ ADRs from `docs/agentic/adr/`

**Why Space exists**:
- Quick access for agents
- No need to browse repo UI
- Convenience for quick reference

**Important**: Space files are **manual uploads**. If the repo changes, re-upload updated files.

---

## Which Version to Use?

### Simple Decision

```
Need a file?
    |
    ├─ Working in Perplexity Space?
    │  └─ Use the file in Space (if recently updated)
    │
    └─ Working in repo?
       └─ Use the repo version (always newest)
```

### If Versions Disagree

**Use the repo version** (it's authoritative).

---

## File Locations

### Agent Files (Repo + Space)

**These live in** `docs/agentic/`:

```
instructions.md
├─ Entry point
├─ Lists all files to read

agentic_coding.md
├─ Comprehensive spec
├─ Autonomy + workflow

autonomy_boundaries.md
├─ What you can/cannot do
└─ Escalation rules

workflow_guide.md
├─ 14-step workflow
└─ Human checkpoints

contribute_standards.md
├─ Code standards
└─ Testing, docs, formatting

custom-instructions.md
├─ Repo-specific rules
└─ Architecture decisions

agent_error_recovery.md
├─ Error procedures
└─ 9 recovery categories

operational_readiness.md
├─ System constraints
└─ Context limits, rate limits

context_budget_guide.md
├─ Token management
└─ When to create new thread

file_organization.md
├─ This file
└─ Where things are
```

### Architecture Decision Records

**These live in** `docs/agentic/adr/`:

```
ADR-001-perplexity-spaces.md
ADR-002-monorepo-structure.md
ADR-003-idempotent-scripts.md
ADR-004-error-recovery.md
```

---

## Sync Guidance

### When to Re-Upload

Re-upload Space files when:
- A change is committed under `docs/agentic/`
- You update ADRs in `docs/agentic/adr/`
- You modify entry points (`OPENCODE.md`, `CLAUDE.md`)

### Quick Checklist

1. Update files in repo
2. Commit + push
3. Upload updated files to Space
4. Paste new `instructions.md` if changed

---

## Summary

**Quick answers**:

- **Where are files?** `docs/agentic/` in this repo
- **Which version?** Repo version (authoritative)
- **How to sync?** Re-upload Space files when docs change
- **Confused about location?** Start in `docs/agentic/instructions.md`
