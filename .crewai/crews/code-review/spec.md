# Code Review Crew Specification

## Overview

The Code Review Crew is an autonomous multi-agent system that performs comprehensive code review from multiple expert perspectives. It runs in GitHub Actions CI/CD pipeline and provides structured feedback on pull requests.

## Objectives

1. **Comprehensive Analysis**: Review code from 5 different expert perspectives
2. **Actionable Feedback**: Provide specific, implementable recommendations
3. **Fast Execution**: Complete review in under 5 minutes
4. **Non-Blocking**: Generate insights without blocking PR merge
5. **Security-First**: Operate with minimal, read-only permissions

## Agents

### 1. Senior Developer Agent

**Role**: Code Quality Lead

**Goal**: Ensure code quality, maintainability, and adherence to best practices

**Backstory**:  
A seasoned software engineer with 15+ years of experience across multiple languages and paradigms. Passionate about clean code, SOLID principles, and long-term maintainability. Known for catching subtle bugs and suggesting elegant refactorings.

**Responsibilities**:

- Code structure and organization
- Design patterns and anti-patterns
- DRY principle violations
- Code complexity (cognitive and cyclomatic)
- Naming conventions
- Error handling patterns
- Code duplication detection

**Tools**:

- `get_file_content`: Read changed files
- `get_commit_diff`: Analyze specific changes
- `get_pr_metadata`: Understand context

---

### 2. Security Analyst Agent

**Role**: Security Expert

**Goal**: Identify security vulnerabilities and sensitive data exposure risks

**Backstory**:  
A security-focused engineer who has seen the consequences of vulnerabilities in production. Expert in OWASP Top 10, secure coding practices, and threat modeling. Always thinking like an attacker.

**Responsibilities**:

- SQL injection vulnerabilities
- Cross-site scripting (XSS) risks
- Authentication/authorization issues
- Secrets in code (API keys, passwords)
- Input validation
- Dependency vulnerabilities
- Data exposure risks
- Insecure configurations

**Tools**:

- `get_file_content`: Scan for security issues
- `get_commit_diff`: Focus on security-sensitive changes
- `search_for_patterns`: Find potential secrets/vulnerabilities

---

### 3. Performance Engineer Agent

**Role**: Performance Optimization Specialist

**Goal**: Identify performance bottlenecks and optimization opportunities

**Backstory**:  
A performance-obsessed engineer who has optimized systems from milliseconds to microseconds. Deep understanding of algorithms, data structures, and system-level performance. Believes every cycle counts.

**Responsibilities**:

- Algorithm complexity (Big O)
- Database query optimization
- N+1 query detection
- Memory leaks and resource management
- Caching opportunities
- Async/parallel execution opportunities
- Hot path optimizations
- Load testing implications

**Tools**:

- `get_file_content`: Analyze code for performance issues
- `get_commit_diff`: Focus on performance-critical changes
- `analyze_complexity`: Estimate algorithmic complexity

---

### 4. Documentation Specialist Agent

**Role**: Documentation & Clarity Expert

**Goal**: Ensure code is understandable, well-documented, and maintainable by others

**Backstory**:  
A technical writer turned engineer who values clarity above all. Has onboarded countless developers and knows the pain of poor documentation. Believes code should tell a story.

**Responsibilities**:

- Code comments quality and necessity
- Function/class documentation (docstrings)
- README and documentation updates
- API documentation
- Complex logic explanations
- Examples and usage patterns
- Deprecation notices
- Migration guides

**Tools**:

- `get_file_content`: Review documentation
- `get_pr_description`: Check PR documentation
- `check_documentation_coverage`: Ensure completeness

---

### 5. Test Engineer Agent

**Role**: Quality Assurance Specialist

**Goal**: Ensure robust test coverage and identify edge cases

**Backstory**:  
A QA engineer who has found thousands of bugs before they reached production. Expert in test-driven development, edge case analysis, and breaking things gracefully. Trust is earned through tests.

**Responsibilities**:

- Test coverage analysis
- Edge case identification
- Error condition testing
- Integration test recommendations
- Test data quality
- Mocking strategy
- Flaky test detection
- Test maintainability

**Tools**:

- `get_file_content`: Review test files
- `get_test_coverage`: Analyze coverage metrics
- `identify_test_gaps`: Find untested code paths

---

## Workflow

### Phase 1: Context Gathering (30 seconds)

1. **PR Metadata Collection**:
   - PR title and description
   - Changed files list
   - Number of commits
   - Author information
   - Branch names

2. **Code Change Analysis**:
   - Fetch full diffs for all changed files
   - Identify file types and languages
   - Extract commit messages
   - Determine scope of changes

3. **Repository Context**:
   - Project structure
   - Configuration files
   - Testing framework
   - CI/CD setup

### Phase 2: Parallel Agent Analysis (3 minutes)

All 5 agents work **concurrently** on their specialized analyses:

- **Senior Developer**: Reviews code structure and quality
- **Security Analyst**: Scans for vulnerabilities
- **Performance Engineer**: Identifies bottlenecks
- **Documentation Specialist**: Checks clarity and docs
- **Test Engineer**: Analyzes test coverage

Each agent:

1. Uses specialized tools to gather relevant data
2. Applies domain expertise to analyze changes
3. Generates findings with severity levels
4. Provides specific, actionable recommendations

### Phase 3: Report Synthesis (1 minute)

1. **Aggregation**:
   - Combine all agent findings
   - Remove duplicate observations
   - Prioritize by severity and impact

2. **Cross-Agent Insights**:
   - Identify common themes across agents
   - Highlight conflicting recommendations
   - Generate holistic assessment

3. **Report Generation**:
   - Structured Markdown output
   - Severity-based categorization
   - File-by-file breakdown
   - Summary with key takeaways

### Phase 4: Output (30 seconds)

Write comprehensive report to GitHub Actions summary:

````markdown
## 🤖 CrewAI Code Review Report

### 📊 Summary

- **PR**: #123 - Add user authentication
- **Files Changed**: 8
- **Lines Added**: +245, **Lines Removed**: -12
- **Review Completed**: 2026-01-18 14:32 UTC

### 🎯 Key Findings

#### 🔴 Critical Issues (2)

1. **Security**: Hardcoded API key in `auth.py:42` (@SecurityAnalyst)
2. **Performance**: N+1 query in `users.py:156` (@PerformanceEngineer)

#### 🟡 Warnings (5)

1. **Code Quality**: Complex function with cyclomatic complexity 15 (@SeniorDeveloper)
2. **Testing**: Missing test coverage for error paths (@TestEngineer)
   ...

#### 🟢 Suggestions (3)

1. **Documentation**: Add docstring to public API (@DocsSpecialist)
   ...

### 📁 File-by-File Analysis

#### `src/auth.py` (+87, -3)

**🔴 Critical - Security Analyst**

> Line 42: Hardcoded API key detected

```python
API_KEY = "sk_live_1234567890abcdef"  # ❌ Remove this
```
````

**Recommendation**: Use environment variables

```python
API_KEY = os.getenv("API_KEY")  # ✅ Better
```

**🟡 Warning - Senior Developer**

> Lines 67-89: Function `authenticate_user` has complexity 12
> **Recommendation**: Extract validation logic into separate function

...

### ✅ Positive Observations

- **Security**: Proper input validation on user endpoints
- **Testing**: Good integration test coverage for happy path
- **Documentation**: Clear README updates

### 🎓 Recommendations

1. **Immediate**: Fix critical security issue in `auth.py`
2. **Before Merge**: Address N+1 query performance issue
3. **Future**: Consider reducing complexity of authentication flow
4. **Consider**: Add integration tests for error conditions

````

---

## Technical Implementation

### Tools Required

#### `get_file_content(path: str) -> str`
Fetches the full content of a file from the PR branch.

**Parameters**:
- `path`: File path relative to repo root

**Returns**: File content as string

**Security**: Read-only access via `GITHUB_TOKEN`

---

#### `get_commit_diff(commit_sha: str, file_path: str) -> dict`
Retrieves the diff for a specific file in a commit.

**Parameters**:
- `commit_sha`: Commit SHA to analyze
- `file_path`: Optional file path to filter

**Returns**: Dict with additions, deletions, and changes

**Security**: Read-only access via `GITHUB_TOKEN`

---

#### `get_pr_metadata() -> dict`
Fetches PR metadata from GitHub Actions context.

**Returns**: Dict with PR number, title, description, files, etc.

**Security**: Uses `GITHUB_EVENT_PATH` environment variable

---

#### `search_for_patterns(pattern: str, files: list[str]) -> list[dict]`
Searches for regex patterns across specified files.

**Parameters**:
- `pattern`: Regex pattern to search
- `files`: List of file paths to search

**Returns**: List of matches with line numbers and context

**Use Cases**: Secret detection, vulnerability scanning, code patterns

---

### LLM Configuration

**Provider**: OpenRouter

**Primary Model**: `anthropic/claude-3.5-sonnet`
- **Why**: Excellent code understanding, strong reasoning
- **Fallback**: `openai/gpt-4-turbo`

**API Key**: `OPENROUTER_API_KEY` from GitHub Secrets

**Rate Limiting**:
- Max 10 requests/second
- Exponential backoff on rate limit errors
- Circuit breaker after 5 consecutive failures

---

### GitHub Actions Integration

**Workflow File**: `.github/workflows/crewai-review.yml`

**Trigger**:
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
````

**Secrets Required**:

- `OPENROUTER_API_KEY`: For LLM access
- `GITHUB_TOKEN`: Auto-provided by GitHub Actions

**Permissions**:

```yaml
permissions:
  contents: read # Read code
  pull-requests: write # Comment on PRs
  checks: write # Update status checks
```

**Job Steps**:

1. Checkout code at PR head
2. Setup Python 3.13
3. Install CrewAI and dependencies
4. Set environment variables
5. Run code review crew
6. Parse output
7. Write to GitHub Actions summary
8. Optionally post PR comment

---

## Security Considerations

### Permissions Model

**What the crew CAN do**:

- ✅ Read repository contents (public & PR code)
- ✅ Read PR metadata (title, description, files)
- ✅ Read commit history and diffs
- ✅ Write to GitHub Actions summary
- ✅ Post comments on PRs (optional)

**What the crew CANNOT do**:

- ❌ Modify code or files
- ❌ Merge or close PRs
- ❌ Access repository secrets
- ❌ Change repository settings
- ❌ Delete branches or commits
- ❌ Approve PRs (no review permissions)

### Token Security

**GitHub Token**:

- Uses built-in `GITHUB_TOKEN` (automatically provided)
- Scoped to PR's repository only
- Expires after job completion
- Never logged or exposed

**OpenRouter API Key**:

- Stored in GitHub Secrets (encrypted)
- Never printed in logs
- Masked in workflow output
- Rotated every 90 days
- Rate-limited to prevent abuse

### Data Privacy

- **Code**: Sent to OpenRouter for analysis (review privacy policy)
- **Secrets**: Never sent to LLM (pre-filtered)
- **PII**: Stripped from output reports
- **Logs**: No sensitive data in GitHub Actions logs

---

## Performance Targets

- **Total Runtime**: < 5 minutes
- **Context Gathering**: < 30 seconds
- **Agent Analysis**: < 3 minutes (parallel)
- **Report Generation**: < 1 minute
- **Output Writing**: < 30 seconds

**Cost Target**: < $0.50 per PR review (OpenRouter API)

---

## Testing Strategy

### Unit Tests

- Individual agent logic
- Tool functionality
- Error handling

### Integration Tests

- Full crew workflow
- GitHub API interactions
- OpenRouter LLM calls (mocked)

### End-to-End Tests

- Test PR with known issues
- Verify report generation
- Check GitHub Actions output

### Test Coverage Target

- Minimum 80% code coverage
- 100% coverage for security-critical paths

---

## Rollout Plan

### Phase 1: Development & Testing (Week 1)

- [ ] Set up CrewAI infrastructure
- [ ] Implement GitHub tools
- [ ] Create 5 agent definitions
- [ ] Build workflow orchestration
- [ ] Write unit tests

### Phase 2: Integration (Week 1-2)

- [ ] Create GitHub Actions workflow
- [ ] Configure OpenRouter integration
- [ ] Set up secrets management
- [ ] Implement error handling
- [ ] Add integration tests

### Phase 3: Testing (Week 2)

- [ ] Test on sample PRs
- [ ] Validate agent outputs
- [ ] Optimize performance
- [ ] Refine prompts
- [ ] Security review

### Phase 4: Beta Rollout (Week 3)

- [ ] Enable on non-critical PRs
- [ ] Monitor performance and costs
- [ ] Gather feedback
- [ ] Iterate on agent prompts

### Phase 5: Production (Week 4)

- [ ] Enable for all PRs
- [ ] Document usage
- [ ] Train team on output
- [ ] Monitor and optimize

---

## Metrics & Monitoring

### Success Metrics

- **Adoption**: % of PRs reviewed by crew
- **Usefulness**: % of findings addressed by developers
- **Performance**: Average review time
- **Cost**: Average cost per review
- **Quality**: Reduction in bugs reaching production

### Monitoring

- GitHub Actions logs
- OpenRouter API usage dashboard
- Cost tracking
- Error rate tracking
- Response time percentiles

---

## Future Enhancements

### Short-term (Next Quarter)

- **PR Comments**: Inline code suggestions
- **Severity Levels**: Configurable thresholds
- **Custom Rules**: Project-specific checks
- **Historical Analysis**: Compare against past reviews

### Long-term (6-12 Months)

- **Auto-Fix**: Suggest code patches
- **Learning**: Improve from accepted/rejected suggestions
- **Multi-Repo**: Share insights across projects
- **Integration**: Connect with Jira, Slack, etc.

---

**Status**: 📋 Specification Complete
**Next Step**: Implementation
**Owner**: @borealBytes
**Last Updated**: 2026-01-18
