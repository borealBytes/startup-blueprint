# Universal Contribution Standards

> **This document defines universal best practices for code, documentation, and collaboration in monorepos using AI-assisted development workflows.**
>
> These standards are **generic and apply to any project**. For BUSINESS_NAME-specific rules, see `custom-instructions.md`.

---

## 🌿 DRY & Single Source of Truth (SSOT)

These principles apply to **all work**: code, docs, PRs, and AI-assisted changes.

### Canonical Locations

For each type of information, there must be **one canonical home**:

- **Contribution rules & workflows** → This file (`contribute_standards.md`)
- **Project-specific rules** → `custom-instructions.md` (or equivalent for your project)
- **Architecture & product decisions** → ADRs or dedicated docs under `docs/adr/`, `docs/guides/`
- **Configuration & environment** → `.env.example` and configuration docs
- **Shared code behavior** → Reusable functions/modules, not copy-pasted logic

If you need to add a new rule:

1. Choose or create **one canonical file/section** for it
2. Add or update it **there** first
3. In other places, **refer back** to that canonical section instead of repeating

### Documentation DRY Rules

When working with documentation:

- **Before writing**, search the repo for existing coverage of the same topic
- If something already exists:
  - **Link or reference it** (optionally with a short summary)
  - Avoid creating a second "full" version
- If documentation must appear in multiple places:
  - The **reference doc is canonical**
  - Other docs should:
    - Give a brief, high-signal summary
    - Point to specific sections/anchors in the canonical doc
- For examples and snippets:
  - Keep **runnable examples in code files** (e.g., `examples/`, test files)
  - Docs should **embed small snippets** or **link to those files**, not maintain large copies

When editing an existing topic:

1. **Update the canonical doc/section first**
2. Adjust brief summaries or references in other docs
3. If you find duplicate explanations, consolidate:
   - Pick a canonical file/section
   - Move the complete explanation there
   - Replace other copies with brief pointers

### Code DRY Rules

For code changes:

- Avoid duplicating business logic, validation rules, or formatting in multiple places
- When you see copy-paste or near-duplicate code:
  - Extract a **shared function, class, or utility module**
  - Update all call sites to use the shared abstraction
- Prefer:
  - **Small, composable functions** with clear responsibilities
  - **Shared helpers** for cross-cutting concerns (logging, error handling, formatting)
- When updating behavior:
  - Update the **shared abstraction**; let all consumers benefit automatically
  - Update associated docs to **describe the abstraction**, not each individual call site

### PR & Issue Template Rules

- Do **not** re-define repo-wide rules in each PR or issue
- Use PR descriptions to:
  - Describe **this change set** specifically
  - Reference sections in contribution standards rather than re-specifying global rules
- When proposing new standards:
  - Capture them in `contribute_standards.md` (or project-specific equivalent)
  - Reference them from PR templates and docs instead of re-writing

---

## ✅ Commit Standards

Commits must be **small/atomic** and messages must **describe intent clearly** (not just mechanics).

Use **Conventional Commits** format:

```
<type>[optional scope]: <description>
```

### Types

- **`feat`** — new feature or capability
- **`fix`** — bug fix
- **`docs`** — documentation changes
- **`style`** — code style (formatting, missing semicolons, etc.)
- **`refactor`** — code change that neither fixes a bug nor adds a feature
- **`perf`** — performance improvement
- **`test`** — test changes
- **`chore`** — maintenance, dependencies, tooling

### Scope (Optional)

Scope indicates the part of the project affected:

```
feat(website): add dark mode toggle
fix(api): handle missing env var
chore(deps): update eslint to v9.0
```

Project-specific scopes are defined in `custom-instructions.md`.

### Description

- Use imperative mood ("add feature" not "added feature")
- Don't capitalize the first letter
- No period (.) at the end
- Describe what and why, not just the how

### Examples

```
feat(auth): implement JWT token refresh strategy
fix(mobile): correct dark mode toggle in hamburger menu
docs: add ADR for database migration approach
chore(ci): upgrade GitHub Actions to node 20
refactor(utils): extract validation logic to shared helper
test(api): add integration test for rate limiting
```

### Breaking Changes

If a commit introduces a **breaking change**, add `BREAKING CHANGE:` section:

```
feat(api): redesign auth endpoint response

BREAKING CHANGE: /auth/token now returns { accessToken, refreshToken }
instead of { token }. Clients must update to use accessToken field.
```

---

## 📋 PR Description Standards

PR descriptions must be **easy to scan**, consistent, and professional.

### Required Sections

Every PR MUST include:

- **Summary** — what changed and why, with key highlights
- **Success Criteria** — Definition of Done (checklist)
- **Task Plan** — items that satisfy those outcomes (checklist)
- **Validation** — how you tested the change
- **Status** — current state (In progress | Ready for review | Ready to merge | Blocked)

### Styling Rules

- Use emoji headers for major sections (professional + minimal; one emoji per section)
- Use `---` horizontal rules between major sections
- Use **bold** only for key status indicators and high-signal callouts
- Use `inline code` for file paths, commands, branches, and technical terms
- Use `>` blockquotes for warnings/corrections/important notes
- Use bullets for lists; use numbers only when order matters
- Keep paragraphs short (2–3 sentences max)

### PR Template (Copy & Paste)

```markdown
## 📋 Summary

Brief description of what changed and why.

**Key additions/changes:**
- Major point 1
- Major point 2
- Major point 3

---

## 🎉 Success Criteria (Definition of Done)

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

---

## ✅ Task Plan

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

---

## 🧭 Validation

- [ ] Build passes / site runs locally (if applicable)
- [ ] Lint/format passes
- [ ] Tests pass (describe which)
- [ ] Manual testing completed (describe flow)

---

## 🚀 Status

**Current status**: In progress | Ready for review | Ready to merge | Blocked

### Notes

- Key decision or context 1
- Key decision or context 2

### Next Steps

- Follow-up item 1
- Follow-up item 2
```

---

## 🗣️ Comments & Reviews Standards

When writing PR comments, issue comments, or review feedback:

- Keep comments concise, actionable, and specific
- Use Markdown formatting to improve clarity:
  - Bullet lists for multiple points
  - `inline code` for identifiers and paths
  - Code blocks for snippets
- Prefer "what + why + suggested fix" in 1–4 sentences
- Use light structure for longer comments:

```markdown
**Issue**
- Describe the problem

**Why it matters**
- Explain the impact

**Suggested change**
- Provide a solution or question
```

---

## 📋 Documentation Styling Standards

Documentation should be **high-signal and skimmable**, similar to PR descriptions.

### Preferred Structure

- Use `##` for primary sections and `###` for subsections
- Use `---` between major sections when it improves readability
- Keep headers concise (under ~6 words) and meaningful
- Use a small amount of emoji in major sections when helpful (optional), but keep it consistent and professional

### Callouts

Use blockquotes for important notes:

```markdown
> **Note**: Helpful context.
> **Warning**: Important risk or gotcha.
```

### Lists and Tables

- Use bullet lists for sets of related items
- Use numbered lists only for sequences or instructions
- Use tables for comparisons and structured reference information

### Code and Diagrams

- Use fenced code blocks with language tags (e.g., ```javascript, ```bash)
- In `.md` documentation, **prefer Mermaid diagrams** for architecture, workflows, data flows, or state diagrams
- When a diagram is warranted, **default to Mermaid** (instead of ASCII art or embedded images)
- Keep diagrams **close to the section they explain**
- Keep diagrams small and high-signal rather than sprawling

### Example Documentation Structure

```markdown
# Feature Title

Brief introduction (1-2 sentences).

---

## 🎯 Overview

Higher-level explanation.

## 📚 How It Works

Detailed explanation. Include diagrams if helpful.

```mermaid
graph LR
  A[Input] --> B[Process] --> C[Output]
```

## 🛠️ Configuration

How to configure this feature.

## ⚠️ Important Notes

> **Warning**: Common gotcha.
> **Note**: Helpful context.
```

---

## 🔐 Secrets Policy

- **Never commit secrets** (API keys, tokens, passwords, credentials)
- Use `.env.example` for documented config with placeholder values
- Ensure `.env`, `.env.local`, `.env.*.local`, and similar are in `.gitignore`
- For sensitive configuration:
  - Document the key name in `.env.example`
  - Provide instructions (link to docs/guide) on how to set it
  - Store actual values in CI/CD secrets, environment files, or secure vaults

### Example `.env.example`

```bash
# Authentication
JWT_SECRET=your-secret-here-minimum-32-chars
OAUTH_CLIENT_ID=get-from-google-cloud-console

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# Third-party APIs
STRIPE_API_KEY=pk_test_...
SENDGRID_API_KEY=SG_...
```

---

## 📚 Monorepo Expectations

For projects using monorepo structure:

- **Respect workspace boundaries** (e.g., `apps/`, `packages/`, etc.)
- **Follow project-specific conventions** (see `custom-instructions.md` or equivalent)
- **Maintain canonical docs** in `docs/` (one source of truth per topic)
- **Keep examples runnable** (in `examples/` or test files, not drift-prone docs)
- **Extract shared logic** to `packages/` or `shared/` (avoid duplication across workspaces)

---

## 🤐 CI/CD & Quality Gates

All monorepos should implement automated quality checks on every commit:

- **Formatting** — code style consistency (e.g., Prettier)
- **Linting** — code quality rules (e.g., ESLint)
- **Testing** — unit & integration tests for affected packages
- **Building** — verify affected packages build successfully

For detailed CI/CD architecture and GitHub Actions examples, see `docs/guides/06-deployment-cicd.md`.

---

## 🔗 References

- [Conventional Commits](https://www.conventionalcommits.org/) — commit message specification
- [Semantic Versioning](https://semver.org/) — version numbering scheme
- [Architecture Decision Records](https://adr.github.io/) — capturing design decisions
- [Mermaid Diagrams](https://mermaid.js.org/) — documentation visualization
