# CI/CD Workflow Architecture

> **Simplified, phase-based orchestration with self-contained change detection**

## 📊 Architecture Overview

```
Pull Request / Push
        ↓
   ci.yml (single entry point)
        ↓
    ┌────────────────────────┐
    │  PHASE 1: CORE CI       │
    │  - Format & Lint        │
    └──────────┬─────────────┘
               │
    ┌──────────┼─────────────┐
    │  PHASE 2: TEST & BUILD  │
    │  (self-detecting)       │
    │  - Docs Links           │ ← Checks if .md files changed
    │  - CrewAI               │ ← Checks if .crewai/ changed
    │  - Website (future)     │ ← Will check apps/website/
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
├── ci.yml                          # 📥 MAIN ORCHESTRATOR (start here)
│                                   # Single workflow with 4 phases
│                                   # This is what you see in GitHub UI
│
├── format-lint-reusable.yml       # 🔧 Phase 1: Core CI
│                                   # Ruff format & lint checks
│
├── link-check-reusable.yml        # 🧪 Phase 2: Docs Testing
│                                   # Self-detecting: runs if .md changed
│
├── test-crewai-reusable.yml       # 🧪 Phase 2: CrewAI Testing
│                                   # Self-detecting: runs if .crewai/ changed
│
├── crewai-review-reusable.yml     # 🤖 Phase 4: AI Code Review
│                                   # AI-powered review agent
│
├── agents/                         # 🤖 Agent configurations
│   └── crewai-review.yml          # CrewAI review job config
│
├── jobs/                           # 🔧 Reusable job components
│   └── (empty - detect-changes removed)
│
└── workspaces/                     # 📦 Future workspace configs
    └── (future website/api workflows)
```

## 📝 How It Works

### Phase 1: Core CI (Always Runs)

**Job:** `core-ci`
- Checks code formatting with Ruff
- Lints Python code
- Auto-fixes and commits if needed

**Outputs:**
- `final-commit-sha` - SHA to use for subsequent jobs (after any auto-fixes)

### Phase 2: Test & Build (Self-Detecting)

**Each test workflow detects its own relevant changes:**

```bash
# link-check-reusable.yml checks:
git diff $BASE $HEAD | grep -E '\.md$|^docs/'

# test-crewai-reusable.yml checks:
git diff $BASE $HEAD | grep '^.crewai/'
```

**Behavior:**
- ✅ If relevant files changed → Runs tests
- ⏭️ If no relevant changes → Skips gracefully with summary message

**Current tests:**
- `test-docs-links` - Validates markdown links
- `test-crewai` - Runs CrewAI test suite

**Future tests:**
- `test-website` - Will check `apps/website/` changes
- `test-api` - Will check `apps/api/` changes

### Phase 3: Deploy (On Success)

**Not yet implemented** - Infrastructure ready:

```yaml
# Uncomment when ready to deploy
deploy-preview:     # PRs with 'deploy:preview' label
deploy-production:  # Push to main branch
```

### Phase 4: Agents (Parallel)

**Runs after Core CI completes:**
- CrewAI Review - AI-powered code analysis
- Posts review to GitHub Actions summary
- Uses local git (no GitHub API rate limits)

## ➕ Adding a New Workspace

Let's say you want to add `apps/website/`:

### Step 1: Create Reusable Test Workflow

**File:** `.github/workflows/test-website-reusable.yml`

```yaml
name: Test Website

on:
  workflow_call:
    inputs:
      commit_sha:
        required: false
        type: string

permissions:
  contents: read
  pull-requests: write

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ inputs.commit_sha || github.sha }}
          fetch-depth: 0

      - name: Check if website files changed
        id: check
        run: |
          set -e
          echo "🔍 Checking if website files changed..."
          
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            BASE="${{ github.event.pull_request.base.sha }}"
            HEAD="${{ github.event.pull_request.head.sha }}"
          else
            BASE="${{ github.event.before }}"
            HEAD="${{ github.sha }}"
          fi
          
          CHANGED_FILES=$(git diff --name-only $BASE $HEAD | grep '^apps/website/' || true)
          
          if [ -z "$CHANGED_FILES" ]; then
            echo "⏭️  No website files changed - skipping"
            echo "should_run=false" >> $GITHUB_OUTPUT
          else
            echo "✅ Website files changed"
            echo "should_run=true" >> $GITHUB_OUTPUT
          fi

      - name: Setup Node
        if: steps.check.outputs.should_run == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install & Test
        if: steps.check.outputs.should_run == 'true'
        working-directory: apps/website
        run: |
          npm ci
          npm test
          npm run build
      
      - name: Upload build artifact
        if: steps.check.outputs.should_run == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: website-build
          path: apps/website/dist

      - name: Add summary for skipped tests
        if: always() && steps.check.outputs.should_run == 'false'
        run: |
          echo "## 🌐 Website Tests" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "⏭️ **Skipped** - No website files changed" >> $GITHUB_STEP_SUMMARY
```

### Step 2: Add to Main Orchestrator

**File:** `.github/workflows/ci.yml`

Uncomment and update the website job:

```yaml
test-website:
  name: Test Website
  needs: [core-ci]
  if: |
    always() &&
    (needs.core-ci.result == 'success' || needs.core-ci.result == 'failure')
  uses: ./.github/workflows/test-website-reusable.yml
  with:
    commit_sha: ${{ needs.core-ci.outputs.final-commit-sha }}
  secrets: inherit
```

### Step 3: (Optional) Add Deployment

Uncomment deploy jobs in `ci.yml`:

```yaml
deploy-preview:
  name: Deploy to Preview
  needs: [test-website]
  if: |
    needs.test-website.result == 'success' &&
    github.event_name == 'pull_request' &&
    contains(github.event.pull_request.labels.*.name, 'deploy:preview')
  uses: ./.github/workflows/preview-deploy-reusable.yml
  # ... rest of config
```

**Done!** 🎉 Your website now:
- Tests only when `apps/website/` changes
- Skips gracefully when no changes
- Builds automatically
- Can deploy to preview (with label)
- Deploys to production (on main push)

## 🛠️ Troubleshooting

### "My workspace tests didn't run"

**Check:**
1. Did your changes affect the workspace path?
2. Look at the Actions summary - should say "Skipped" if no changes detected
3. Check the change detection script in the reusable workflow

**Debug:**
```bash
# Run change detection locally
git diff origin/main...HEAD --name-only | grep '^apps/website/'
```

### "Tests ran but I didn't change any files in that workspace"

**This happens when:**
- The base commit doesn't exist (first push to branch)
- Git fetch depth is too shallow

**Solution:**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # ← Make sure this is set
```

### "Deploy job didn't run"

**Check:**
1. Did tests pass? (Deploy requires success)
2. For preview: Does PR have `deploy:preview` label?
3. For production: Are you pushing to `main`?

## 📊 Best Practices

### 1. Keep Workflows Self-Contained

Each reusable workflow should:
- Detect its own relevant file changes
- Skip gracefully if no changes
- Not depend on centralized change detection

### 2. Use Consistent Change Detection Pattern

```yaml
# Step 1: Detect changes
- name: Check if X files changed
  id: check
  run: |
    CHANGED_FILES=$(git diff --name-only $BASE $HEAD | grep '^path/' || true)
    if [ -z "$CHANGED_FILES" ]; then
      echo "should_run=false" >> $GITHUB_OUTPUT
    else
      echo "should_run=true" >> $GITHUB_OUTPUT
    fi

# Step 2: Conditional steps
- name: Do work
  if: steps.check.outputs.should_run == 'true'
  run: ...

# Step 3: Skipped summary
- name: Add summary for skipped
  if: always() && steps.check.outputs.should_run == 'false'
  run: |
    echo "⏭️ **Skipped** - No relevant changes" >> $GITHUB_STEP_SUMMARY
```

### 3. Pass Commit SHA Forward

Always use the SHA from core-ci:

```yaml
with:
  commit_sha: ${{ needs.core-ci.outputs.final-commit-sha }}
```

This ensures all jobs test the same commit (even if auto-fixes were pushed).

### 4. Always Use `fetch-depth: 0`

Required for change detection:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # ← Essential for git diff to work
```

## 📚 Reference

### Job Naming Convention

```
<phase>-<purpose>

Examples:
core-ci
test-docs-links
test-crewai
test-website
deploy-preview
crewai-review
```

### Conditional Execution Patterns

**Run after core-ci (success or failure):**
```yaml
if: |
  always() &&
  (needs.core-ci.result == 'success' || needs.core-ci.result == 'failure')
```

**Run if tests passed:**
```yaml
if: needs.test-website.result == 'success'
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

## 🎯 Design Decisions

### Why Self-Contained Change Detection?

**Before:** Centralized `detect-changes` job → all workflows depend on it

**After:** Each workflow detects its own changes

**Benefits:**
1. **Simpler:** No complex workspace mapping JSON
2. **More maintainable:** Change detection logic lives with the workflow it controls
3. **Easier to debug:** Look at one file instead of multiple
4. **More flexible:** Each workflow can have custom detection rules
5. **Better UX:** Clear "Skipped" messages in Actions summary

### Why Not Use GitHub's `paths` Filter?

GitHub's built-in `paths` works at the workflow level, not job level:

```yaml
# This would create separate workflows
on:
  pull_request:
    paths:
      - 'apps/website/**'
```

We want:
- Single workflow entry point (`ci.yml`)
- Reusable workflow components
- Change detection at job execution time

---

**Last Updated:** 2026-01-22  
**Architecture:** Phase-based with self-contained change detection  
**Questions?** Open an issue or ask in #dev-ops
