# BUSINESS_NAME — Project-Specific Rules

> **This document defines rules, conventions, and structure specific to the BUSINESS_NAME monorepo.**
>
> For universal standards that apply to any project, see `contribute_standards.md`.

---

## 📚 Monorepo Structure

The BUSINESS_NAME monorepo uses **pnpm workspaces** with **Turbo** for build orchestration and caching.

### Workspace Layout

```
BUSINESS_NAME/
├── apps/                  # Deployed applications
│   └── [workspace]        # Individual app (Next.js, etc.)
├── packages/              # Shared libraries (npm packages)
│   └── [workspace]        # Shared code, utilities
├── website/               # Main website (if separate)
├── data/                  # Data scripts, migrations, seeds
├── docs/                  # Documentation (architecture, guides, ADRs)
├── scripts/               # Root-level utility scripts
├── docs/agentic/          # Agent instructions (this directory)
├── .github/               # GitHub Actions workflows
├── pnpm-workspace.yaml    # pnpm workspace configuration
├── turbo.json             # Turbo build configuration
├── package.json           # Root package metadata
└── .env.example           # Environment variables template
```

### Workspace Definitions

| Path | Type | Purpose | Deploy Target | Scope Prefix |
|------|------|---------|---------------|--------|
| `apps/*` | Application | Standalone deployed services | Varies per app | `app(<name>)` |
| `packages/*` | Library | Shared code, utilities, design system | NPM / internal | `pkg(<name>)` |
| `website/` | Application | Main BUSINESS_NAME website | Cloudflare Pages | `website` |
| `data/` | Scripts | Database migrations, seeds, data tools | (not deployed) | `data` |

### Configuration Files

- **`pnpm-workspace.yaml`** — defines which directories are workspaces
- **`turbo.json`** — defines task dependencies and caching rules
- **`package.json`** (root) — root workspace metadata (scripts, dependencies)
- **`package.json`** (each workspace) — individual workspace dependencies

See files themselves for current configuration.

---

## 📋 Conventional Commits Scopes

For this monorepo, use scope prefixes matching the workspace:

### Examples

```
feat(website): add dark mode toggle
fix(app-dashboard): handle missing data edge case
feat(pkg-utils): export new validation helper
docs: add deployment guide
chore(deps): bump typescript to 5.3
test(app-dashboard): add integration test for user flow
```

### Scope Rules

- **For workspace changes**: Use `<workspace-name>` (e.g., `website`, `app-dashboard`, `pkg-utils`)
- **For root/config changes**: Omit scope (e.g., `chore(deps)`, `docs`)
- **For changes affecting multiple workspaces**: List primary workspace or use descriptive scope (e.g., `feat(auth): implement JWT refresh across all apps`)
- **For CI/infrastructure**: Use scope like `ci`, `chore` (e.g., `ci: add path-aware linting workflow`)

---

## 🎯 Workspace Development Workflow

### Common Tasks

#### Start a feature in workspace `website`

```bash
# Create branch
git checkout -b feat/website-dark-mode

# Make changes in website/ directory

# Test locally
pnpm --filter website dev

# Commit with scope
git commit -m "feat(website): add dark mode toggle"

# Push and open PR
git push origin feat/website-dark-mode
```

#### Add shared code to `packages/utils`

```bash
git checkout -b feat/pkg-utils-validation-helpers

# Add new functions to packages/utils/src

# Run tests
pnpm --filter pkg-utils test

# Commit
git commit -m "feat(pkg-utils): add email and phone validators"

# Update consuming packages to use new exports
git commit -m "feat(website): use new validators from pkg-utils"

git push origin feat/pkg-utils-validation-helpers
```

#### Update root configuration

```bash
git checkout -b chore/turbo-caching-rules

# Edit turbo.json

# Commit (no scope, since it's root)
git commit -m "chore: enable incremental turbo caching"

git push origin chore/turbo-caching-rules
```

---

## 📚 Source of Truth Hierarchy

When working on BUSINESS_NAME, check for guidance in this order:

1. **Current working branch** → `docs/agentic/custom-instructions.md` (most specific)
2. **Current working branch** → `docs/agentic/agentic_coding.md` (agent boundaries)
3. **Current working branch** → `docs/agentic/contribute_standards.md` (universal standards)
4. **Main branch** → Same files if not overridden in current branch
5. **Documentation** → `docs/adr/`, `docs/guides/` (architecture decisions, procedures)

If you find **conflicting guidance**, stop and ask for confirmation.

---

## 🗣️ Workspace Dependencies

### Dependency Graph

```
website/
    ↓
packages/utils
packages/design-system

app-dashboard/
    ↓
packages/utils
packages/api-client
packages/design-system

app-admin/
    ↓
packages/utils
packages/api-client
```

### CI/CD Impact

- If `packages/utils` changes → rebuild & test `website`, `app-dashboard`, `app-admin`
- If `packages/design-system` changes → rebuild & test `website`, `app-dashboard`
- If `website` changes → test `website` only (no other apps affected)

GitHub Actions workflows use Turbo's dependency graph to run only affected tests (see `docs/guides/06-deployment-cicd.md`).

---

## 🔐 Environment & Secrets

### `.env.example`

The `.env.example` file documents all environment variables needed across the monorepo:

```bash
# Website configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AUTH_DOMAIN=auth.example.com

# API Keys (store actual values in GitHub Secrets or .env.local)
STRIPE_SECRET_KEY=sk_test_...
SENDGRID_API_KEY=SG_...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/business_name
```

### Local Development

1. Copy `.env.example` to `.env.local`
2. Fill in actual values (get from team lead or GitHub Secrets)
3. Never commit `.env.local` or other `.env.*` files
4. `.gitignore` already excludes `.env*` files

### CI/CD & Production

- GitHub Secrets store actual values (non-checking-in)
- GitHub Actions inject secrets into runner environment
- Each environment (staging, production) has separate GitHub Secret values
- Agent cannot read or write GitHub Secrets (humans only)

See `docs/guides/` for detailed configuration management patterns.

---

## 🎯 PR Guidelines for BUSINESS_NAME

### PR Title Format

Use Conventional Commits format in PR title:

```
feat(website): add dark mode toggle
fix(app-dashboard): handle missing user data
chore: update dependencies
```

### PR Description Template

Use the universal template from `contribute_standards.md` with these additions:

```markdown
## 📋 Summary

Brief description of changes.

**Affected workspace(s)**: `website`, `packages/utils`
**Breaking changes**: None (or describe)

---

## 🎉 Success Criteria

- [ ] Criterion specific to this change

---

## ✅ Task Plan

- [ ] Implement feature
- [ ] Add tests
- [ ] Update docs

---

## 🧭 Validation

- [ ] Tests pass: `pnpm test` and `pnpm --filter <workspace> test`
- [ ] Build passes: `pnpm build`
- [ ] Lint passes: `pnpm lint`
- [ ] Manual testing in `website` (or applicable workspace)

---

## 🚀 Status

**Current status**: Ready for review
```

---

## 📋 Testing & CI/CD

### Local Testing Before Push

```bash
# Install dependencies
pnpm install

# Run all tests
pnpm test

# Run tests for specific workspace
pnpm --filter website test

# Lint entire monorepo
pnpm lint

# Format code
pnpm format

# Build
pnpm build
```

### GitHub Actions (Automatic)

On every commit, GitHub Actions runs:

1. **Detect changes** → Which workspaces changed?
2. **Format & Lint** → Auto-fix if needed, commit back
3. **Test** → Run tests only for affected workspaces
4. **Build** → Build affected workspaces

See `docs/guides/06-deployment-cicd.md` for detailed workflow.

---

## 📚 References & Links

- **Monorepo structure**: See `pnpm-workspace.yaml` and `turbo.json`
- **Build tasks**: See individual `package.json` scripts in each workspace
- **CI/CD workflows**: See `.github/workflows/`
- **Architecture decisions**: See `docs/adr/`
- **Configuration management**: See `docs/guides/`
- **Universal standards**: See `contribute_standards.md`
