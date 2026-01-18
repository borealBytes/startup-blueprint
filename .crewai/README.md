# CrewAI Code Review System

> **Automated multi-agent code review for GitHub pull requests**
>
> Based on [official CrewAI patterns](https://github.com/crewAIInc/demo-pull-request-review) and best practices

---

## Overview

This directory contains a CrewAI-powered code review system that analyzes pull requests using three specialized AI agents. The system provides comprehensive feedback on code quality, security, performance, and architecture - directly posted as PR comments.

---

## Project Structure

```
.crewai/
├── README.md                    # This file
├── IMPLEMENTATION_PLAN.md       # Detailed implementation roadmap
├── crew.py                      # Main Crew definition
├── main.py                      # Entry point for GitHub Actions
├── __init__.py
├── config/
│   ├── agents.yaml              # 3 agent definitions
│   └── tasks.yaml               # 6 task definitions
├── tools/
│   ├── __init__.py
│   ├── github_tools.py          # GitHub API tools
│   └── related_files_tool.py    # Related files analysis
└── tests/
    ├── test_tools.py
    ├── test_agents.py
    └── test_integration.py
```

**Key Design Decisions:**

- ✅ Uses standard `Crew` class (not `Flow`) - simpler for sequential tasks
- ✅ Follows official CrewAI project structure conventions
- ✅ Uses UV package manager (modern Python tooling)
- ✅ 3 specialized agents (not 5) - better cost/performance balance

---

## The Three Agents

### 1. Code Quality Reviewer 📖

**Role**: Senior code reviewer  
**Focus**:

- Code style and readability
- Best practices and maintainability
- Test coverage and quality
- Documentation completeness

**Tools**: GitHubDiffTool, CommitInfoTool, PRCommentTool

### 2. Security & Performance Analyst 🔒⚡

**Role**: Security researcher + performance engineer  
**Focus**:

- Security vulnerabilities (SQL injection, XSS, auth issues)
- Credential leaks and sensitive data exposure
- Performance bottlenecks (N+1 queries, memory leaks)
- Resource usage and optimization opportunities

**Tools**: GitHubDiffTool, FileContentTool

### 3. Architecture & Impact Analyst 🏛️

**Role**: Software architect + impact assessor  
**Focus**:

- Design patterns and architectural decisions
- **Related files analysis** (finds files NOT directly modified but affected)
- Coupling, cohesion, and modularity
- Scalability and long-term maintainability

**Tools**: GitHubDiffTool, FileContentTool, RelatedFilesTool

---

## Task Workflow (6 Sequential Tasks)

```
1. Analyze Code Changes (Code Quality Reviewer)
   ↓
2. Security & Performance Review (Security & Performance Analyst)
   ↓
3. Find Related Files (Architecture & Impact Analyst) ← NEW! Inspired by official demo
   ↓
4. Analyze Related Files (Architecture & Impact Analyst)
   ↓
5. Architecture Review (Architecture & Impact Analyst)
   ↓
6. Generate Review Comment (Code Quality Reviewer) ← Posts to PR!
```

**Estimated time**: 3-5 minutes per review

---

## Key Features

✅ **Related Files Analysis** - Finds files affected by changes (even if not directly modified)  
✅ **PR Comment Posting** - Review appears directly in PR (not just Actions log)  
✅ **Multi-Perspective Review** - Security, performance, architecture, quality  
✅ **Cost Optimized** - 3 agents vs 5 = 60% cost reduction  
✅ **Fast Execution** - Sequential processing with context sharing  
✅ **OpenRouter Integration** - Model flexibility + cost optimization

---

## Setup & Installation

### Prerequisites

- Python 3.10-3.13
- UV package manager
- GitHub repository with Actions enabled
- OpenRouter API key

### Local Development

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to .crewai directory
cd .crewai

# 3. Install dependencies
crewai install

# 4. Create .env file
cp .env.example .env

# 5. Add your API keys to .env
OPENROUTER_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# 6. Test locally (requires PR context)
GITHUB_PR_NUMBER=1 GITHUB_REPOSITORY=owner/repo GITHUB_SHA=abc123 python main.py
```

### GitHub Actions Setup

1. **Add OpenRouter API Key** to GitHub Secrets:
   - Go to: Settings → Secrets and variables → Actions
   - Add secret: `OPENROUTER_API_KEY`
   - Value: Your OpenRouter API key from <https://openrouter.ai/keys>

2. **Workflow is automatically triggered** on:
   - Pull request opened
   - Pull request synchronized (new commits)
   - Pull request reopened

3. **Review appears**:
   - As PR comment (primary output)
   - In GitHub Actions job summary (for debugging)

---

## Configuration

### Customizing Agents

Edit `.crewai/config/agents.yaml`:

```yaml
code_quality_reviewer:
  role: Senior Code Reviewer
  goal: Evaluate code changes for quality, style, testing...
  backstory: You are a senior engineer with 15 years experience...
  verbose: true
  allow_delegation: false
```

### Customizing Tasks

Edit `.crewai/config/tasks.yaml`:

```yaml
analyze_code_changes:
  description: Analyze code changes focusing on...
  expected_output: A structured report with...
  agent: code_quality_reviewer
```

### Changing LLM Model

By default uses `anthropic/claude-3.5-sonnet` via OpenRouter.

To change, edit `crew.py` and modify the agent LLM configuration:

```python
Agent(
    config=self.agents_config['code_quality_reviewer'],
    llm="openai/gpt-4o",  # or any OpenRouter model
    tools=[...],
)
```

---

## Cost Estimates

### Per Review (with Claude 3.5 Sonnet)

- **3 agents** × ~$0.08 per agent = **~$0.24 per review**
- Input tokens: ~50K (diff + context)
- Output tokens: ~2K (review comments)

### Monthly (100 PRs)

- **$24/month** for code review automation
- Compare to: ~5 hours of human review time

**Cost optimization:**

- Use cheaper models for simple PRs (detect via file count/lines changed)
- Cache responses for identical commits
- Skip review for bot-generated PRs (Dependabot, etc.)

---

## Security Model

### GitHub Token (`GITHUB_TOKEN`)

- Automatically provided by GitHub Actions
- Read-only permissions:
  - ✅ Read repository content
  - ✅ Read PR metadata
  - ✅ Write PR comments
- ❌ Cannot modify code or settings
- ❌ Cannot access secrets

### OpenRouter API Key

- Stored in GitHub Secrets (encrypted)
- Never logged or exposed in output
- Used only for LLM API calls
- Rotation recommended every 90 days

**Secret management documented in**: `.github/SECRETS.md`

---

## Testing

### Run Tests

```bash
cd .crewai

# Unit tests
pytest tests/test_tools.py -v
pytest tests/test_agents.py -v

# Integration test (requires mocked PR data)
pytest tests/test_integration.py -v

# All tests with coverage
pytest --cov=. --cov-report=html
```

### Manual Testing

1. Create test PR with known issues:
   - Add hardcoded credentials
   - Write inefficient loop
   - Missing tests
   - Undocumented function

2. Trigger workflow manually:
   - Go to Actions tab
   - Select "CrewAI Code Review" workflow
   - Click "Run workflow"

3. Verify review catches all issues

---

## Troubleshooting

### "OPENROUTER_API_KEY not found"

- Ensure secret is added in GitHub Settings → Secrets
- Secret name must be exactly `OPENROUTER_API_KEY`
- Re-run workflow after adding secret

### "Rate limit exceeded"

- GitHub API: Max 5000 requests/hour (usually enough)
- OpenRouter: Check your plan limits
- Implement caching (future enhancement)

### "Review not posted to PR"

- Check GitHub Actions logs for errors
- Verify `pull-requests: write` permission in workflow
- Ensure `GITHUB_TOKEN` has correct scopes

### "Timeout after 15 minutes"

- Large PRs may hit timeout
- Reduce diff size (chunk files)
- Use faster LLM model
- Increase timeout in workflow YAML

---

## Future Enhancements (Phase 2)

- [ ] **Historical PR Analysis** - Learn from past reviews
- [ ] **Custom Rules Engine** - Project-specific checks
- [ ] **Auto-Fix Suggestions** - Generate code patches
- [ ] **Cost Dashboard** - Track API usage and costs
- [ ] **False Positive Feedback** - Learn from dismissals
- [ ] **Multi-Language Support** - Beyond Python/JS/TS

---

## References

- [Official CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review)
- [CrewAI Documentation](https://docs.crewai.com/)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [OpenRouter API](https://openrouter.ai/docs)
- [GitHub Actions](https://docs.github.com/en/actions)

---

## Support

**For issues or questions:**

- Check `IMPLEMENTATION_PLAN.md` for detailed design decisions
- Review GitHub Actions logs for errors
- Open issue in repository

---

**Status**: 🏗️ Implementation Ready  
**Current Phase**: Phase 1 - Core Code Review Crew  
**Last Updated**: 2026-01-18  
**Cost**: ~$0.24/review | ~$24/month (100 PRs)  
**Speed**: 3-5 minutes average
