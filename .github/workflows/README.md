# CI/CD Workflow Architecture

> **Monorepo-friendly, phase-based orchestration for scalable CI/CD**

## 📊 Architecture Overview

```
Pull Request / Push
        ↓
   ci.yml (single entry point)
        ↓
    ┌────────────────────────┐
    │  PHASE 1: CORE CI       │
    │  - Format & Lint        │
    │  - Detect Changes       │
    └──────────┬─────────────┘
               │
    ┌──────────┼─────────────┐
    │  PHASE 2: TEST & BUILD  │
    │  (conditional)          │
    │  - Docs Links           │
    │  - CrewAI               │
    │  - Website (future)     │
    └──────────┬─────────────┘
               │
    ┌──────────┼─────────────┐
    │  PHASE 3: DEPLOY        │
    │  (on success)           │
    │  - Preview (PR)         │
    │  - Production (main)    │
    └────────────────────────┘
               │ (parallel)
    ┌──────────┼─────────────┐
    │  PHASE 4: AGENTS        │
    │  (after core-ci)        │
    │  - CrewAI Review        │
    └────────────────────────┘
```

## 📁 Directory Structure

```
.github/workflows/
├── ci.yml                      # 📥 MAIN ORCHESTRATOR (start here)
│                               # Single workflow with 4 phases
│                               # This is what you see in GitHub UI
│
├── jobs/                       # 🔧 Phase 1: Core CI Jobs
│   ├── format-lint.yml        # Ruff format & lint checks
│   └── detect-changes.yml     # Monorepo change detection
│
├── workspaces/                 # 🧪 Phase 2: Per-Workspace Testing
│   ├── docs-links-test.yml    # Documentation link validation
│   ├── crewai-test.yml        # CrewAI tests & validation
│   └── website-test-build.yml # (Future) Website test+build
│
├── environments/               # 🚀 Phase 3: Deployment (future)
│   ├── preview-deploy.yml     # Deploy to preview env
│   └── production-deploy.yml  # Deploy to production
│
└── agents/                     # 🤖 Phase 4: AI Agents
    └── crewai-review.yml      # AI-powered code review
```

## 📝 How It Works

### Phase 1: Core CI (Always Runs)

**Jobs:**
- `01-core-ci-format-lint` - Checks code formatting and linting
- `01-core-ci-detect-changes` - Determines which workspaces changed

**Outputs:**
- `workspaces` (JSON array) - List of changed workspaces: `["crewai", "docs"]`
- `final-commit-sha` - SHA to use for subsequent jobs

### Phase 2: Test & Build (Conditional)

**Jobs run ONLY if their workspace changed:**

```yaml
if: contains(needs.01-core-ci-detect-changes.outputs.workspaces, 'crewai')
```

**Current workspaces:**
- `docs` - Runs if any `.md` files changed
- `crewai` - Runs if `.crewai/` changed

**Future workspaces:**
- `website` - Will run if `apps/website/` changes
- `api` - Will run if `apps/api/` changes

### Phase 3: Deploy (On Success)

**Not yet implemented** - Infrastructure ready:

```yaml
# Uncomment when ready to deploy
03-deploy-website-preview:     # PRs with 'deploy:preview' label
03-deploy-website-production:  # Push to main branch
```

### Phase 4: Agents (Parallel)

**Runs after Core CI completes:**
- CrewAI Review - AI-powered code analysis
- Posts review comment to PR
- Uses local git (no GitHub API calls for diff)

## ➕ Adding a New Workspace

Let's say you want to add `apps/website/`:

### Step 1: Create Test Workflow

**File:** `.github/workflows/workspaces/website-test-build.yml`

```yaml
name: Website Test & Build

on:
  workflow_call:
    inputs:
      commit_sha:
        required: false
        type: string

jobs:
  test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.commit_sha }}
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install & Test
        working-directory: apps/website
        run: |
          npm ci
          npm test
          npm run build
      
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: website-build
          path: apps/website/dist
```

### Step 2: Update Change Detection

**File:** `.github/workflows/jobs/detect-changes.yml`

```bash
# Add this to the detection script:
if echo "$CHANGED_FILES" | grep -q "^apps/website/"; then
  echo "✅ Website workspace changed"
  WORKSPACES+=("website")
fi
```

### Step 3: Add to Main Orchestrator

**File:** `.github/workflows/ci.yml`

Uncomment the website job:

```yaml
02-test-build-website:
  name: "Phase 2: Test+Build » Website"
  needs: [01-core-ci-format-lint, 01-core-ci-detect-changes]
  if: |
    contains(needs.01-core-ci-detect-changes.outputs.workspaces, 'website')
  uses: ./.github/workflows/workspaces/website-test-build.yml
  with:
    commit_sha: ${{ needs.01-core-ci-format-lint.outputs.final-commit-sha }}
  secrets: inherit
```

### Step 4: (Optional) Add Deployment

Uncomment deploy jobs in `ci.yml`:

```yaml
03-deploy-website-preview:
  name: "Phase 3: Deploy » Website (Preview)"
  needs: [01-core-ci-detect-changes, 02-test-build-website]
  if: |
    needs.02-test-build-website.result == 'success' &&
    github.event_name == 'pull_request' &&
    contains(github.event.pull_request.labels.*.name, 'deploy:preview')
  uses: ./.github/workflows/environments/preview-deploy.yml
  # ... rest of config
```

**Done!** 🎉 Your website now:
- Tests only when `apps/website/` changes
- Builds automatically
- Can deploy to preview (with label)
- Deploys to production (on main push)

## 🛠️ Troubleshooting

### "My workspace tests didn't run"

**Check:**
1. Did your changes affect the workspace path?
2. Is the path pattern correct in `detect-changes.yml`?
3. Is the job condition in `ci.yml` correct?

**Debug:**
```bash
# Run change detection locally
git diff main...your-branch --name-only
```

### "All tests run even though I only changed one file"

**This happens when:**
- You changed `.github/workflows/` (CI affects all workspaces)
- The change detection script has an issue

**Intended behavior:**
- CI changes = run all tests (safety)

### "Deploy job didn't run"

**Check:**
1. Did tests pass? (Deploy requires success)
2. For preview: Does PR have `deploy:preview` label?
3. For production: Are you pushing to `main`?

## 📊 Best Practices

### 1. Keep Workspaces Isolated

✅ **Good:**
```yaml
defaults:
  run:
    working-directory: apps/website
```

❌ **Avoid:**
```yaml
run: cd apps/website && npm test && cd ../api && npm test
```

### 2. Use Meaningful Job Names

✅ **Good:**
```yaml
02-test-build-website:
  name: "Phase 2: Test+Build » Website"
```

❌ **Avoid:**
```yaml
test-1:
  name: "Test"
```

### 3. Pass Commit SHA Forward

Always use the SHA from format-lint job:

```yaml
with:
  commit_sha: ${{ needs.01-core-ci-format-lint.outputs.final-commit-sha }}
```

This ensures all jobs test the same commit (even if auto-fixes were pushed).

### 4. Make Jobs Self-Contained

Each workspace workflow should:
- Check out code
- Set up environment
- Run tests
- Upload artifacts (if needed)
- Not depend on other workspace jobs

## 📚 Reference

### Job Naming Convention

```
<phase>-<category>-<workspace>

Examples:
01-core-ci-format-lint
02-test-crewai
02-test-build-website
03-deploy-website-preview
04-agent-crewai-review
```

### Conditional Execution Patterns

**Run if workspace changed:**
```yaml
if: contains(needs.01-core-ci-detect-changes.outputs.workspaces, 'website')
```

**Run if tests passed:**
```yaml
if: needs.02-test-build-website.result == 'success'
```

**Run on main branch only:**
```yaml
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**Run on PR with label:**
```yaml
if: |
  github.event_name == 'pull_request' &&
  contains(github.event.pull_request.labels.*.name, 'deploy:preview')
```

## 🔗 Related Documentation

- [GitHub Actions: Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [GitHub Actions: workflow_call](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_call)
- [GitHub Actions: Conditional Execution](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idif)

---

**Last Updated:** 2026-01-22  
**Maintainer:** DevOps Team  
**Questions?** Open an issue or ask in #dev-ops
