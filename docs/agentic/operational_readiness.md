# Operational Readiness & Constraints

> System limits, context budgets, and operational boundaries.

**Read this before**: Starting complex work (refactors, infrastructure changes).  
**Don't read this**: Until you need to know about constraints (saves context).

---

## Perplexity Spaces Context Window

### Context Budget

**Available context per Thread**: ~200,000 tokens (approximately 150,000 words)

**What uses context**:

- ✅ Base instructions (40 lines from `instructions.md`)
- ✅ Your task description
- ✅ Files you reference
- ✅ All conversation history in Thread
- ✅ Code snippets I show

**Rule of Thumb**:

- 1 MB of text ≈ 400 tokens
- 1 large file (5,000 lines) ≈ 2,000 tokens

### Context Management

**When context is low** (< 30% remaining):

1. Work is getting slow
2. I might miss nuances
3. **Action**: Create new Thread, provide context, continue

**How to manage**:

- ✅ Reference files by name (don't paste full content)
- ✅ Ask for specific sections (not entire files)
- ✅ Keep task focused and narrow
- ✅ Create new Thread if conversation gets long

---

## GitHub & Repository Constraints

### API Rate Limits

**GitHub API limits** (if accessing via integrations):

- Personal: 60 requests/hour (unauthenticated)
- Authenticated: 5,000 requests/hour
- Per-user: 15 requests/second

**Action if hit**:

- Stop making API calls
- Wait 1 hour for reset
- If critical, ask human for help

### File Size Limits

**GitHub limits**:

- Max file size in UI: 1 MB (but can be larger if pushed)
- Recommended: Keep files < 500 KB for performance
- Max repo size: 100 GB (soft limit)

**Rule of Thumb**:

- Single files > 100 KB = consider splitting
- Single files > 500 KB = definitely split

### Push/Pull Performance

**Large files** can cause:

- Slow pushes
- Slow pulls
- CI/CD delays
- Context window overflow

**Best practice**: Keep files focused and smaller.

---

## CI/CD Pipeline Constraints

### GitHub Actions Limits

**Per-month quotas** (free tier):

- 2,000 minutes/month for private repos
- Unlimited for public repos

**Per-workflow**:

- Max runtime: 6 hours
- Max jobs: 256
- Max matrix: 256 combinations

**Action if approaching limits**:

- Optimize workflows (parallelize, cache dependencies)
- Ask human for guidance
- Consider paid plan if needed

### Workflow Execution Time

**Typical repo workflow**:

- Format check: 1-2 minutes
- Lint: 2-3 minutes
- Tests: 5-10 minutes
- Build: 5-15 minutes
- **Total**: 15-30 minutes

**If consistently > 30 minutes**:

- Something is wrong (infinite loop? massive dependency?)
- See `agent_error_recovery.md` for troubleshooting

---

## Session & Connectivity Constraints

### Perplexity Session Timeout

**Idle timeout**: Sessions can expire after extended inactivity (typically 2-4 hours)

**Action**:

1. If session expires, refresh browser
2. Create new Thread
3. Provide task context
4. Continue work

### Network Issues

**If disconnected**:

- Any unsaved work might be lost
- Wait for reconnection
- Create new Thread to resume

**Prevention**:

- Make commits regularly (don't keep local changes long)
- Push frequently (keeps backup in GitHub)

---

## Security & Access Constraints

### GitHub Secrets

**Agent can NOT**:

- 🚫 Read GitHub Secrets
- 🚫 Modify GitHub Secrets
- 🚫 Access secret values

**Why**: Secrets are for humans only (security boundary).

**If you need secret values**:

- Ask human to provide them
- Or ask human to configure in GitHub Actions

### Environment Variables

**Agent can NOT**:

- 🚫 Hardcode credentials
- 🚫 Commit `.env.local` files
- 🚫 Set environment variables in CI/CD

**Proper way**:

- Use GitHub Secrets (humans configure)
- Reference in CI/CD workflows
- Agent never sees actual values

---

## Project-Specific Constraints

### BUSINESS_NAME Workspace Limits

**For BUSINESS_NAME monorepo**:

**Max simultaneous deployments**: 1 per environment  
**Max concurrent workspace builds**: 5  
**Max database connections**: 50 (pooled)

**Why matters**:

- Don't run multiple deployments in parallel
- Keep an eye on resource usage
- Ask human if hitting limits

### API Rate Limits (BUSINESS_NAME APIs)

**Development APIs**:

- 1,000 requests/hour per workspace
- 100 requests/minute per user

**If hitting limits**:

- Batch API calls
- Add delays between calls
- Ask human for rate limit increase

---

## Data & Database Constraints

### Database Size

**Development database**:

- Current size: [Check BUSINESS_NAME admin]
- Max recommended: 10 GB (performance degrades)

**Action if approaching limit**:

- Alert human
- Consider archiving old data
- Optimize queries

### Query Performance

**Queries should complete**:

- < 100 ms (ideal)
- < 1 second (acceptable)
- > 5 seconds (investigate)

**If query is slow**:

- Add database indexes
- Optimize query logic
- Ask human for database help

### Backup & Data Safety

**Agent can NOT**:

- 🚫 Drop tables or databases
- 🚫 Delete significant data
- 🚫 Run destructive migrations without approval

**Proper way**:

- Ask human before any destructive operation
- Create backups first (human responsibility)
- Test migrations in dev environment first

---

## Computational & Storage Constraints

### Build Artifact Storage

**GitHub Actions default**: 5 GB cache storage  
**BUSINESS_NAME usage**: [Check current]

**If hitting storage limits**:

- Clean old artifacts: `actions/delete-package-versions@v4`
- Compress build outputs
- Ask human for guidance

### Docker Image Size

**Container registry limits** (if using):

- Free tier: 500 MB storage
- Each image should be < 200 MB (if possible)

**If image too large**:

- Remove unnecessary dependencies
- Use multi-stage builds
- Minimize layer count

---

## Time & Scheduling Constraints

### Working Hours

**Recommendation**:

- Create branches during your active hours
- Push complete, tested code
- Humans review when they're available

### Merge Freezes

**BUSINESS_NAME might have**:

- Friday afternoon freezes (no merges)
- Release weeks (restricted changes)
- Holiday freezes

**Check with human before**:

- Major refactors
- Breaking changes
- Infrastructure changes

---

## Escalation Rules

**For complete escalation rules**, see `autonomy_boundaries.md`.

Quick reference:

- 🏠 Breaking changes → Ask
- 🏠 Security modifications → Ask
- 🏠 Architecture decisions → Ask
- 🏠 Uncertain about boundaries → Ask

---

## Quick Reference

| Constraint            | Limit          | Action if Hit          |
| --------------------- | -------------- | ---------------------- |
| **Context window**    | ~200K tokens   | Create new Thread      |
| **GitHub API**        | 5,000/hour     | Wait 1 hour            |
| **Session timeout**   | 2-4 hours idle | Refresh + New Thread   |
| **CI/CD runtime**     | 6 hours max    | Optimize workflow      |
| **File size**         | ~100 MB        | Split file             |
| **Database query**    | 5 sec limit    | Optimize query         |
| **Concurrent builds** | 5 max          | Wait for one to finish |

---

## Remember

- 📊 Constraints exist for **reliability and efficiency**
- 📊 Most constraints are **generous** (rarely hit in normal work)
- 📊 If you hit a constraint, **ask for guidance**
- 📊 Prevention through awareness **saves time**

---

**Operational readiness = fewer surprises, smoother development.**
