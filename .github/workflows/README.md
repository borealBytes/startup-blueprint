# CI/CD Orchestration Structure

Scalable, phase-based CI/CD orchestration for our monorepo.

## 📐 Architecture Overview

```
ci.yml (main orchestrator)
├─ Phase 1: core-ci.yml (Quality Gates)
│  ├─ jobs/format-lint.yml
│  └─ jobs/detect-changes.yml
│
├─ Phase 2: test-build.yml (Test & Build)
│  ├─ workspaces/crewai-test.yml
│  ├─ workspaces/docs-links-test.yml
│  └─ workspaces/website-test-build.yml (FUTURE)
│
├─ Phase 3: deploy.yml (Deploy)
│  ├─ environments/preview-deploy.yml (FUTURE)
│  └─ environments/production-deploy.yml (FUTURE)
│
└─ Phase 4: agents.yml (AI Analysis)
   └─ agents/crewai-review.yml
```

## 🔄 Execution Flow

### Pull Request Flow
```
PR Opened/Updated
  ↓
[Phase 1] Core CI
  ├─ Format & Lint → Auto-fix → Commit
  └─ Detect Changes → Output: ["crewai", "docs"]
  ↓
[Phase 2] Test & Build (parallel)
  ├─ CrewAI Test (if .crewai/ changed)
  ├─ Docs Links (if *.md changed)
  └─ Website Test+Build (if apps/website/ changed) [FUTURE]
  ↓
[Phase 3] Deploy (if label:deploy:preview)
  └─ Preview Environment [FUTURE]
  ↓
[Phase 4] AI Agents (parallel with Phase 3)
  └─ CrewAI Code Review → Post PR comment
```

### Main Branch Flow
```
Push to main
  ↓
[Phase 1] Core CI
  ├─ Format & Lint
  └─ Detect Changes
  ↓
[Phase 2] Test & Build
  ├─ All changed workspaces
  ↓
[Phase 3] Deploy to Production
  └─ Deploy changed workspaces [FUTURE]
  ↓
[Phase 4] AI Agents (skipped - not a PR)
```

## 📁 Directory Structure

```
.github/workflows/
├── ci.yml                    # Main orchestrator (entry point)
├── core-ci.yml               # Phase 1: Quality gates
├── test-build.yml            # Phase 2: Test & build orchestrator
├── deploy.yml                # Phase 3: Deploy orchestrator
├── agents.yml                # Phase 4: AI agents orchestrator
│
├── jobs/                     # Utility jobs
│   ├── format-lint.yml       # Code formatting & linting
│   └── detect-changes.yml    # Workspace change detection
│
├── workspaces/               # Per-workspace test+build
│   ├── crewai-test.yml       # CrewAI testing
│   ├── docs-links-test.yml   # Documentation validation
│   └── website-test-build.yml # Website test+build [FUTURE]
│
├── environments/             # Per-environment deployment
│   ├── preview-deploy.yml    # Preview environment [FUTURE]
│   └── production-deploy.yml # Production environment [FUTURE]
│
└── agents/                   # AI agents
    └── crewai-review.yml     # Code review agent
```

## ➕ Adding New Workspaces

### Example: Adding a Website Workspace

**1. Update change detection** (`jobs/detect-changes.yml`):
```yaml
# Add detection logic
if echo "$CHANGED_FILES" | grep -q "^apps/website/"; then
  WORKSPACES+=("website")
  echo "  ✓ Detected: website"
fi
```

**2. Create workspace workflow** (`workspaces/website-test-build.yml`):
```yaml
name: Website Test & Build

on:
  workflow_call:
    inputs:
      commit_sha:
        required: true
        type: string

jobs:
  test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test
        run: npm test
      - name: Build
        run: npm run build
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: website-build
          path: dist/
```

**3. Add to test-build orchestrator** (`test-build.yml`):
```yaml
website:
  name: Website
  if: contains(inputs.changed_workspaces, 'website')
  uses: ./.github/workflows/workspaces/website-test-build.yml
  with:
    commit_sha: ${{ inputs.commit_sha }}
  secrets: inherit
```

**4. Add deployment** (when ready):
```yaml
# In deploy.yml
website:
  name: Website → ${{ inputs.environment }}
  if: contains(inputs.changed_workspaces, 'website')
  uses: ./.github/workflows/environments/${{ inputs.environment }}-deploy.yml
  with:
    workspace: website
  secrets: inherit
```

## 🌍 Environment Management

### Preview Environment
- **Trigger**: PR with `deploy:preview` label
- **URL**: `https://preview.credibilitymarkets.com`
- **Purpose**: Test changes before production

### Production Environment
- **Trigger**: Push to `main` branch
- **URL**: `https://credibilitymarkets.com`
- **Purpose**: Live production site

### Environment-Specific Secrets
```yaml
# In deploy.yml
environment:
  name: ${{ inputs.environment }}
  url: ${{ inputs.environment == 'production' && 
          'https://credibilitymarkets.com' || 
          'https://preview.credibilitymarkets.com' }}
```

## 🎯 Conditional Execution

Workspaces only run when their files change:

```yaml
# test-build.yml
crewai:
  name: CrewAI
  if: contains(inputs.changed_workspaces, 'crewai')
  uses: ./.github/workflows/workspaces/crewai-test.yml
```

Change detection maps file paths to workspaces:
- `.crewai/**` → `crewai`
- `apps/website/**` → `website`
- `**/*.md` → `docs`
- `.github/workflows/**` → ALL workspaces

## 🔧 Troubleshooting

### Workflow not running?
1. Check if workspace was detected: View "Detect Changes" job output
2. Verify file paths match detection logic in `jobs/detect-changes.yml`
3. Check `if:` conditions in orchestrator workflows

### Format & lint failing?
1. Format should auto-fix and commit
2. If manual fixes needed, check commit history
3. Run locally: `black .` and `isort .`

### Deploy not triggering?
1. **PR**: Add `deploy:preview` label
2. **Main**: Verify push to `main` branch
3. Check if workspace changed (deploy.yml conditions)

### AI agent not running?
1. Check PR is not draft
2. Verify not a bot PR (dependabot, renovate)
3. Confirm core-ci completed

## 📊 Benefits

✅ **Scalable** - Easy to add workspaces  
✅ **Efficient** - Only test/build what changed  
✅ **Clear** - Obvious where things run  
✅ **Maintainable** - DRY with reusable workflows  
✅ **Environment-aware** - Preview vs production  
✅ **Monorepo-friendly** - Path-based detection  

## 🚀 Future Enhancements

- [ ] Website deployment to Cloudflare Pages
- [ ] API workspace with test+build+deploy
- [ ] E2E testing workflow
- [ ] Security scanning (SAST/DAST)
- [ ] Performance testing
- [ ] Release automation

---

**Last updated**: 2026-01-22  
**Status**: Production-ready orchestration framework
