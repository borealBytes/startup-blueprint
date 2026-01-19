# CrewAI Code Review System

> **Automated multi-agent code review for GitHub pull requests**
>
> Based on [official CrewAI patterns](https://github.com/crewAIInc/demo-pull-request-review) and best practices

---

## Overview

This directory contains a CrewAI-powered code review system that analyzes **commit changes** in pull requests using three specialized AI agents. The system provides comprehensive feedback on code quality, security, performance, and architecture - posted as **executive summaries** directly in PR comments.

**Key Features:**
- 🤖 Three specialized AI agents (60% cost reduction vs 5 agents)
- 🔍 Commit-based review: all changed files + related file impacts
- 📊 Executive summary format: quick scan + detailed findings
- ⚡ CI-only (no Python setup required for developers)
- 💰 Cost-effective: ~$0.21/review with OpenAI gpt-4o via OpenRouter
- ⏱️ Fast: 3-5 minutes per review

---

## Project Structure

```
.crewai/
├── README.md                    # This file
├── IMPLEMENTATION_PLAN.md       # Detailed implementation roadmap
├── crew.py                      # Main Crew definition
├── main.py                      # Entry point for GitHub Actions
├── pyproject.toml               # Python dependencies (isolated)
├── .env.example                 # Template for local testing
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
- ✅ OpenRouter integration - model flexibility + cost optimization

---

## The Three Agents

### 1. Code Quality Reviewer 📚
**Role**: Senior code reviewer + coordinator  
**Focus**: 
- Code style and readability
- Best practices and maintainability
- Test coverage and quality
- Documentation completeness
- Commit message quality
- **Generates executive summary**

**Tools**: CommitDiffTool, CommitInfoTool, PRCommentTool

### 2. Security & Performance Analyst 🔒⚡
**Role**: Security researcher + performance engineer  
**Focus**:
- Security vulnerabilities (SQL injection, XSS, auth issues)
- Credential leaks and hardcoded secrets
- Performance bottlenecks (N+1 queries, memory leaks)
- Resource usage and optimization opportunities

**Tools**: CommitDiffTool, FileContentTool

### 3. Architecture & Impact Analyst 🏛️
**Role**: Software architect + impact assessor  
**Focus**:
- Design patterns and architectural decisions
- **Related files analysis** (finds files NOT directly modified but affected)
- Coupling, cohesion, and modularity
- Scalability and long-term maintainability

**Tools**: CommitDiffTool, FileContentTool, RelatedFilesTool

---

## Task Workflow (6 Sequential Tasks)

```
1. Analyze Commit Changes (Code Quality Reviewer)
   Input: Commit diff, message, files changed
   Output: Code quality issues, commit message assessment
   ↓
2. Security & Performance Review (Security & Performance Analyst)
   Input: Task 1 output + diff
   Output: Vulnerabilities, bottlenecks, secrets
   ↓
3. Find Related Files (Architecture & Impact Analyst) ← NEW!
   Input: Changed files list
   Output: Related files with scores (0-100)
   ↓
4. Analyze Related Files (Architecture & Impact Analyst)
   Input: Task 3 output
   Output: Impact on related components
   ↓
5. Architecture Review (Architecture & Impact Analyst)
   Input: All previous outputs
   Output: Design patterns, maintainability
   ↓
6. Generate Executive Summary (Code Quality Reviewer)
   Input: All task outputs
   Output: Executive summary + detailed findings → Post to PR
```

**Total time**: 3-5 minutes per review

---

## Executive Summary Output Format

Each review is posted to the PR with this structure:

```markdown
## 📊 Executive Summary

- **Overall**: ✅ LGTM | ⚠️ Needs Changes | 🚨 Critical Issues
- **Files**: 5 modified, 2 new, 0 removed
- **Changes**: +245 lines, -87 lines
- **Issues**: 0 critical, 2 warnings, 5 suggestions
- **Top Actions**:
  1. Fix SQL injection in auth.py:45
  2. Add tests for new user validation
  3. Document breaking change in API

## 🔍 Detailed Findings

### 🚨 Critical Issues (Must Fix)
[Blocking issues with file:line references]

### ⚠️ Warnings (Should Fix)
[Important non-blocking concerns]

### 💡 Suggestions (Nice to Have)
[Improvements and optimizations]

### ✅ Positive Observations
[Good patterns found]
```

---

## Setup & Installation

### Prerequisites

- Python 3.10-3.13
- UV package manager
- GitHub repository with Actions enabled
- OpenRouter API key

### Local Development (Optional)

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to .crewai directory
cd .crewai

# 3. Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .

# 4. Create .env file
cp .env.example .env

# 5. Add your API keys to .env
OPENROUTER_API_KEY=sk-or-v1-...
GITHUB_TOKEN=ghp_...

# 6. Test locally (requires PR context)
GITHUB_PR_NUMBER=1 \
GITHUB_REPOSITORY=owner/repo \
GITHUB_SHA=abc123 \
python main.py
```

**Note**: Local setup is optional. CrewAI runs automatically in CI - no Python setup required for developers.

### GitHub Actions Setup (CI-Only)

1. **Add OpenRouter API Key** to GitHub Secrets:
   - Go to: Settings → Secrets and variables → Actions
   - Add secret: `OPENROUTER_API_KEY`
   - Value: Your OpenRouter API key from https://openrouter.ai/keys

2. **Workflow is automatically triggered** on:
   - Pull request opened
   - Pull request synchronized (new commits)
   - Pull request reopened

3. **Review appears**:
   - As PR comment (primary output)
   - In GitHub Actions job summary (for debugging)

---

## OpenRouter Configuration

### Getting Your API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Go to [Keys page](https://openrouter.ai/keys)
4. Create new key (optional: set spending limits)
5. Copy the key (starts with `sk-or-v1-...`)

### Model Selection

**Default Model**: `openai/gpt-4o`  
**Alternative**: `openai/gpt-4o-mini` (70% cheaper, good quality)

To change models, edit `.crewai/crew.py`:

```python
from langchain_openrouter import ChatOpenRouter

self.llm = ChatOpenRouter(
    model="openai/gpt-4o",        # or "openai/gpt-4o-mini"
    api_key=api_key,
    temperature=0.3,              # Lower = more consistent
)
```

**Available Models via OpenRouter**:
- `openai/gpt-4o` - Best quality (~$0.21/review)
- `openai/gpt-4o-mini` - Good quality, budget (~$0.06/review)
- `anthropic/claude-3.5-sonnet` - Excellent reasoning (~$0.24/review)
- `anthropic/claude-3-haiku` - Fast and cheap (~$0.08/review)

See [OpenRouter Models](https://openrouter.ai/models) for full list and pricing.

---

## Configuration

### Customizing Agents

Edit `.crewai/config/agents.yaml`:

```yaml
code_quality_reviewer:
  role: Senior Code Reviewer
  goal: Evaluate commit changes for quality, style, testing...
  backstory: You are a senior engineer with 15 years experience...
  verbose: true
  allow_delegation: false
```

### Customizing Tasks

Edit `.crewai/config/tasks.yaml`:

```yaml
analyze_commit_changes:
  description: Analyze all files changed in this commit...
  expected_output: A structured report with...
  agent: code_quality_reviewer
```

### Changing Review Scope

To review only specific file types, modify tools in `crew.py`:

```python
# Example: Only review Python and JavaScript
file_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
```

---

## Cost Estimates

### Per Review

| Model | Input Tokens | Output Tokens | Cost/Review |
|-------|-------------|--------------|-------------|
| **gpt-4o** | ~50K | ~2K | ~$0.21 |
| **gpt-4o-mini** | ~50K | ~2K | ~$0.06 |
| **claude-3.5-sonnet** | ~50K | ~2K | ~$0.24 |
| **claude-3-haiku** | ~50K | ~2K | ~$0.08 |

### Monthly (100 PRs)

| Model | Monthly Cost | Quality | Best For |
|-------|-------------|----------|----------|
| **gpt-4o** | ~$21 | High | Complex PRs |
| **gpt-4o-mini** | ~$6 | Good | Most PRs |
| **claude-3.5-sonnet** | ~$24 | Excellent | Architecture reviews |
| **claude-3-haiku** | ~$8 | Good | Fast feedback |
| **Hybrid** | ~$12 | Balanced | Cost optimization |

**Hybrid strategy**: Use `gpt-4o-mini` for small commits (<50 lines), `gpt-4o` for complex commits

**ROI**: Saves ~5 hours of human review time per month

**Comparison to 5-agent plan**: 58% cost reduction

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

### OpenRouter API Key (`OPENROUTER_API_KEY`)

- Stored in GitHub Secrets (encrypted at rest)
- Never logged or exposed in output
- Used only for LLM API calls via OpenRouter
- **Rotation recommended**: Every 90 days
- **Access control**: Only GitHub Actions workflows
- **Spending limits**: Set on OpenRouter dashboard

**Secret management documented in**: `.github/SECRETS.md`

---

## Testing

### Run Tests

```bash
cd .crewai
source .venv/bin/activate

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
   - Add hardcoded credentials (e.g., `API_KEY = "sk-1234"`)
   - Write inefficient loop (e.g., N+1 query)
   - Missing tests for new function
   - Undocumented public method

2. Trigger workflow manually:
   - Go to Actions tab
   - Select "CrewAI Code Review" workflow
   - Click "Run workflow"

3. Verify review catches all issues with proper severity

---

## Troubleshooting

### "OPENROUTER_API_KEY not found"

**Solution:**
- Ensure secret is added in GitHub Settings → Secrets
- Secret name must be exactly `OPENROUTER_API_KEY`
- Re-run workflow after adding secret

### "OpenRouter rate limit exceeded"

**Solution:**
- Check your OpenRouter account limits
- Set spending limits on OpenRouter dashboard
- Implement exponential backoff (future enhancement)
- Consider caching responses for identical commits

### "Review not posted to PR"

**Solution:**
- Check GitHub Actions logs for errors
- Verify `pull-requests: write` permission in workflow
- Ensure `GITHUB_TOKEN` has correct scopes

### "Timeout after 15 minutes"

**Solution:**
- Large PRs may hit timeout
- Reduce diff size (chunk files >500 lines)
- Use faster model (`gpt-4o-mini` or `claude-3-haiku`)
- Increase timeout in workflow YAML

### "High API costs"

**Solution:**
- Switch to `gpt-4o-mini` for most reviews
- Implement hybrid strategy (mini for small, full for large)
- Skip review for bot PRs (Dependabot, Renovate)
- Cache responses for identical commits
- Set spending limits on OpenRouter dashboard

### "Model unavailable"

**Solution:**
- Check [OpenRouter Status](https://status.openrouter.ai/)
- Try alternative model in `crew.py`
- Implement fallback model logic (future enhancement)

---

## Future Enhancements (Phase 2)

- [ ] **Historical Commit Analysis** - Learn from past reviews
- [ ] **Custom Rules Engine** - Project-specific checks
- [ ] **Auto-Fix Suggestions** - Generate code patches
- [ ] **Cost Dashboard** - Track API usage and costs
- [ ] **False Positive Feedback** - Learn from dismissals
- [ ] **Multi-Language Support** - Beyond Python/JS/TS
- [ ] **Hybrid Model Strategy** - Auto-select model based on commit size
- [ ] **Response Caching** - Reuse reviews for identical commits
- [ ] **Model Fallback** - Auto-retry with alternative model on failure

---

## References

- [Official CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review) - Architecture inspiration
- [CrewAI Documentation](https://docs.crewai.com/) - Official patterns and API
- [UV Package Manager](https://docs.astral.sh/uv/) - Modern Python tooling
- [OpenRouter](https://openrouter.ai/) - LLM gateway with unified API
- [OpenRouter Models](https://openrouter.ai/models) - Available models and pricing
- [GitHub Actions](https://docs.github.com/en/actions) - CI/CD platform

---

## Support

**For issues or questions:**
- Check `IMPLEMENTATION_PLAN.md` for detailed design decisions
- Review GitHub Actions logs for errors
- Verify secret configuration in repository settings
- Check OpenRouter dashboard for API usage/limits
- Open issue in repository with:
  - Error message
  - GitHub Actions log link
  - Commit SHA that failed
  - Model used

---

**Status**: 🏁 Design Finalized, Implementation Ready  
**Current Phase**: Phase 1 - Core Code Review Crew  
**Last Updated**: 2026-01-18  
**Cost**: ~$0.21/review (gpt-4o) | ~$21/month (100 PRs)  
**Speed**: 3-5 minutes average  
**Dev Impact**: None (CI-only Python environment)
