# GitHub Actions CI/CD Structure

## Overview

This repository uses a **single orchestrator** pattern with phase-based execution:

```
ci.yml (Main Orchestrator)
├─ Phase 1: Core CI (Quality gates)
├─ Phase 2: Test & Build (Changed workspaces only)
├─ Phase 3: Deploy (Environment-aware) [FUTURE]
└─ Phase 4: AI Agents (Code review)
```

## File Structure

```
.github/workflows/
├── ci.yml                          # Main orchestrator (THIS IS THE ONE)
├── README.md                       # This file
│
├── format-lint-reusable.yml        # Formatting & linting
├── test-orchestration-reusable.yml # Change detection
├── link-check-reusable.yml         # Documentation tests
├── test-crewai-reusable.yml        # CrewAI workspace tests
└── crewai-review-reusable.yml      # AI code review
```

## Why This Structure?

### ✅ GitHub Actions Requirements
- **Reusable workflows MUST be at top level** of `.github/workflows/`
- Subdirectories are not allowed for workflow files
- Single orchestrator (`ci.yml`) coordinates everything

### ✅ Benefits
- **Clear execution flow** - 4 distinct phases
- **Efficient** - Only test/build what changed
- **Scalable** - Easy to add new workspaces
- **DRY** - Reusable workflows for common patterns
- **Easy to debug** - Clear job naming shows exactly what failed

## Execution Flow

### Phase 1: Core CI (Always Runs)
```
format-lint → detect-changes
```
- Format/lint all code
- Detect which workspaces changed
- Outputs: `test-matrix` (JSON), `final-commit-sha`

### Phase 2: Test & Build (Conditional)
```
test-docs ─┐
           ├─→ (Phase 3)
test-crewai ┘
```
- Runs **only if** Core CI completes (success or failure)
- Each test job checks if its workspace changed
- Parallel execution where possible

### Phase 3: Deploy (Future)
```
deploy-preview      # PR with 'deploy:preview' label
deploy-production   # Push to 'main' branch
```
- Runs **only if** Phase 2 succeeds
- Environment-aware (preview vs production)
- Currently commented out (not implemented yet)

### Phase 4: AI Agents (Parallel with Phase 3)
```
review-crewai  # PR code review
```
- Runs **after** Phase 2 completes
- Skips drafts, bots (dependabot, renovate)
- Uses `always()` so it runs even if tests fail

## Adding a New Workspace

Example: Add a `website` workspace

### 1. Create Reusable Workflow

Create `.github/workflows/test-website-reusable.yml`:

```yaml
name: Test Website (Reusable)

on:
  workflow_call:
    inputs:
      commit_sha:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.commit_sha }}
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        working-directory: ./apps/website
        run: npm ci
      
      - name: Run tests
        working-directory: ./apps/website
        run: npm test
```

### 2. Add Detection Logic

Edit `test-orchestration-reusable.yml` to detect `apps/website/**` changes:

```yaml
- name: Check Website Changes
  id: website
  run: |
    if git diff --name-only ${{ env.BASE_SHA }} ${{ env.HEAD_SHA }} | grep -q '^apps/website/'; then
      echo "changed=true" >> $GITHUB_OUTPUT
    fi
```

### 3. Add Job to ci.yml

Add to Phase 2 in `ci.yml`:

```yaml
test-website:
  name: "Phase 2 » Website"
  needs: [format-lint, detect-changes]
  if: |
    always() &&
    (needs.format-lint.result == 'success' || needs.format-lint.result == 'failure') &&
    contains(needs.detect-changes.outputs.test-matrix, 'test-website-reusable.yml')
  uses: ./.github/workflows/test-website-reusable.yml
  with:
    commit_sha: ${{ needs.format-lint.outputs.final-commit-sha }}
  secrets: inherit
```

### 4. Update Deploy Dependencies

When enabling Phase 3, add `test-website` to deploy `needs`:

```yaml
deploy-preview:
  needs: [format-lint, detect-changes, test-docs, test-crewai, test-website]
  # ...
```

## Conditional Execution Logic

### `if: always()`
Runs even if previous jobs failed. Used when:
- Tests should run regardless of lint failures
- AI review should run regardless of test results

### `needs.X.result == 'success' || needs.X.result == 'failure'`
Runs if job **completed** (not skipped/cancelled). Used when:
- We need the job's outputs (like `final-commit-sha`)
- We want to proceed even if job found issues

### `contains(needs.detect-changes.outputs.test-matrix, 'X')`
Runs **only if** workspace changed. Used for:
- Efficient testing (don't test unchanged workspaces)
- Workspace-specific jobs

## Common Patterns

### Reusable Workflow Template

```yaml
name: My Reusable Workflow

on:
  workflow_call:
    inputs:
      commit_sha:
        required: true
        type: string
      some_option:
        required: false
        type: string
        default: 'default-value'
    secrets:
      MY_SECRET:
        required: false

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.commit_sha }}
      
      - name: Do work
        run: echo "Working with ${{ inputs.some_option }}"
```

### Calling Reusable Workflow

```yaml
my-job:
  name: "My Job"
  needs: [previous-job]
  uses: ./.github/workflows/my-reusable.yml
  with:
    commit_sha: ${{ needs.previous-job.outputs.commit_sha }}
    some_option: 'custom-value'
  secrets:
    MY_SECRET: ${{ secrets.MY_SECRET }}
```

## Troubleshooting

### "Invalid workflow reference" Error

**Error:**
```
error parsing called workflow: workflows must be defined at the top level of the .github/workflows/ directory
```

**Solution:** Move workflow to `.github/workflows/` (no subdirectories allowed).

### Job Not Running

Check the `if:` condition:
1. Does it use `always()` if it should run regardless of failures?
2. Does it check for correct result values (`success`, `failure`, `skipped`, `cancelled`)?
3. Does it check for the right trigger (`github.event_name`)?

### Change Detection Not Working

Verify:
1. `test-orchestration-reusable.yml` has detection logic for your paths
2. Job's `if:` condition includes `contains(needs.detect-changes.outputs.test-matrix, 'your-workflow.yml')`
3. Git diff base/head refs are correct for PR vs push events

### Outputs Not Available

Ensure:
1. Job producing output is in the `needs:` array of consuming job
2. Output is defined in reusable workflow's `outputs:` section
3. Output is set correctly using `echo "name=value" >> $GITHUB_OUTPUT`

## Examples

### Run Job Only on Main Branch

```yaml
my-job:
  if: github.ref == 'refs/heads/main'
```

### Run Job Only on PRs with Label

```yaml
my-job:
  if: |
    github.event_name == 'pull_request' &&
    contains(github.event.pull_request.labels.*.name, 'my-label')
```

### Run Job After Multiple Dependencies

```yaml
my-job:
  needs: [job1, job2, job3]
  if: |
    needs.job1.result == 'success' &&
    needs.job2.result == 'success' &&
    needs.job3.result == 'success'
```

## References

- [GitHub Actions: Reusing workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [GitHub Actions: Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub Actions: Contexts](https://docs.github.com/en/actions/learn-github-actions/contexts)
