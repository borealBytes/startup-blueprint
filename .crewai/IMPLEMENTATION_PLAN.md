# CrewAI Implementation Plan

## Overview

This document outlines the phased implementation plan for integrating CrewAI multi-agent code review into the startup-blueprint repository's CI/CD pipeline.

---

## Phase 1: Code Review Crew (Current)

**Timeline**: 2-3 weeks
**Status**: 🏗️ Planning

### Objectives
1. Set up CrewAI infrastructure
2. Implement 5-agent code review system
3. Integrate with GitHub Actions
4. Validate security and performance

### Tasks

#### Task 1.1: Environment Setup
**Estimated Time**: 2-3 hours

- [ ] Create `.crewai/` directory structure
- [ ] Add `requirements.txt` with dependencies:
  ```
  crewai>=0.28.0
  crewai-tools>=0.8.0
  langchain>=0.1.0
  openai>=1.10.0
  PyGithub>=2.1.1
  python-dotenv>=1.0.0
  pyyaml>=6.0.1
  ```
- [ ] Create `.env.example` for local development
- [ ] Update `.gitignore` to exclude `.env`, `__pycache__`, etc.

#### Task 1.2: GitHub Tools Development
**Estimated Time**: 4-6 hours

- [ ] Implement `tools/github_tools.py`:
  - [ ] `get_file_content(path: str) -> str`
  - [ ] `get_commit_diff(commit_sha: str) -> dict`
  - [ ] `get_pr_metadata() -> dict`
  - [ ] `list_changed_files() -> list[str]`
  - [ ] `search_for_patterns(pattern: str, files: list) -> list`
- [ ] Add error handling and retry logic
- [ ] Implement rate limit handling
- [ ] Add unit tests

#### Task 1.3: Agent Definitions
**Estimated Time**: 3-4 hours

- [ ] Create `config/agents.yaml`:
  - [ ] Senior Developer agent definition
  - [ ] Security Analyst agent definition
  - [ ] Performance Engineer agent definition
  - [ ] Documentation Specialist agent definition
  - [ ] Test Engineer agent definition
- [ ] Define agent roles, goals, backstories
- [ ] Configure LLM parameters per agent
- [ ] Set up agent memory and context

#### Task 1.4: Task Definitions
**Estimated Time**: 3-4 hours

- [ ] Create `config/tasks.yaml`:
  - [ ] Code quality analysis task
  - [ ] Security review task
  - [ ] Performance analysis task
  - [ ] Documentation review task
  - [ ] Test coverage analysis task
- [ ] Define task descriptions and expected outputs
- [ ] Set up task dependencies (if needed)
- [ ] Configure task execution order

#### Task 1.5: Crew Implementation
**Estimated Time**: 4-6 hours

- [ ] Create `crews/code-review/crew.py`:
  - [ ] Initialize CrewAI framework
  - [ ] Load agent and task configurations
  - [ ] Set up LLM provider (OpenRouter)
  - [ ] Configure crew execution strategy (parallel)
  - [ ] Implement error recovery
- [ ] Create `crews/code-review/agents.py`:
  - [ ] Instantiate all 5 agents
  - [ ] Assign tools to each agent
  - [ ] Configure agent collaboration
- [ ] Create `crews/code-review/tasks.py`:
  - [ ] Instantiate all tasks
  - [ ] Link tasks to agents
  - [ ] Set up task inputs from PR context

#### Task 1.6: Workflow Orchestration
**Estimated Time**: 3-4 hours

- [ ] Create `workflows/code_review_workflow.py`:
  - [ ] Parse GitHub Actions event data
  - [ ] Prepare crew inputs (PR metadata, files, diffs)
  - [ ] Execute crew
  - [ ] Collect agent outputs
  - [ ] Generate structured report
  - [ ] Handle errors and timeouts
- [ ] Add logging and debugging output
- [ ] Implement progress tracking

#### Task 1.7: Report Generation
**Estimated Time**: 3-4 hours

- [ ] Create report formatter:
  - [ ] Severity-based categorization (Critical, Warning, Suggestion)
  - [ ] File-by-file breakdown
  - [ ] Code snippets with line numbers
  - [ ] Actionable recommendations
  - [ ] Summary statistics
- [ ] Generate Markdown output for GitHub Actions summary
- [ ] (Optional) Generate JSON output for external tools
- [ ] Add emoji and formatting for readability

#### Task 1.8: GitHub Actions Integration
**Estimated Time**: 3-4 hours

- [ ] Create `.github/workflows/crewai-review.yml`:
  - [ ] Configure PR trigger (opened, synchronize, reopened)
  - [ ] Set permissions (contents: read, pull-requests: write)
  - [ ] Checkout code at PR head
  - [ ] Setup Python 3.13
  - [ ] Install dependencies
  - [ ] Set environment variables:
    - `GITHUB_TOKEN` (auto-provided)
    - `OPENROUTER_API_KEY` (from secrets)
    - `GITHUB_REPOSITORY`, `GITHUB_PR_NUMBER`, etc.
  - [ ] Run crew workflow
  - [ ] Capture output
  - [ ] Write to GitHub Actions summary
  - [ ] Handle failures gracefully
- [ ] Test workflow on sample PR

#### Task 1.9: Security Configuration
**Estimated Time**: 2-3 hours

- [ ] Add OpenRouter API key to GitHub Secrets:
  - [ ] Document in `.github/SECRETS.md`
  - [ ] Include rotation schedule (90 days)
  - [ ] Note minimal permissions required
- [ ] Configure token scoping:
  - [ ] Verify `GITHUB_TOKEN` has read-only access
  - [ ] Test permissions in isolated workflow
- [ ] Add security checks:
  - [ ] Prevent secrets from being logged
  - [ ] Mask sensitive data in output
  - [ ] Validate input from untrusted sources

#### Task 1.10: Testing & Validation
**Estimated Time**: 4-6 hours

- [ ] Unit tests:
  - [ ] Test GitHub tools with mocked API
  - [ ] Test agent initialization
  - [ ] Test task execution
  - [ ] Test report generation
- [ ] Integration tests:
  - [ ] Test crew workflow end-to-end (mocked LLM)
  - [ ] Test GitHub Actions workflow (dry-run)
- [ ] Manual testing:
  - [ ] Create test PR with known issues
  - [ ] Run crew locally
  - [ ] Verify output quality
  - [ ] Test edge cases (large PRs, no changes, etc.)
- [ ] Performance testing:
  - [ ] Measure execution time
  - [ ] Monitor API usage
  - [ ] Validate cost per review

#### Task 1.11: Documentation
**Estimated Time**: 2-3 hours

- [ ] Update `.crewai/README.md` with usage instructions
- [ ] Document agent behaviors and outputs
- [ ] Add troubleshooting guide
- [ ] Create runbook for common issues
- [ ] Document cost and performance characteristics

#### Task 1.12: Beta Rollout
**Estimated Time**: 1 week monitoring

- [ ] Enable workflow on selected PRs
- [ ] Monitor execution logs
- [ ] Track costs and performance
- [ ] Collect feedback from team
- [ ] Iterate on agent prompts based on feedback
- [ ] Fix bugs and edge cases

---

## Phase 2: Enhanced Features (Future)

**Timeline**: TBD
**Status**: 📋 Planned

### Potential Features

#### PR Comment Integration
- Post inline code suggestions
- Comment on specific lines
- Link to relevant documentation

#### Custom Rule Engine
- Project-specific checks
- Configurable severity levels
- Team-defined best practices

#### Historical Analysis
- Compare against past reviews
- Track improvement over time
- Identify recurring issues

#### Auto-Fix Suggestions
- Generate code patches
- Suggest specific refactorings
- Provide "Apply Suggestion" button

---

## Phase 3: Additional Crews (Future)

**Timeline**: TBD
**Status**: 🔮 Vision

### Architecture Review Crew
**Purpose**: Analyze system design, scalability, architectural patterns

**Agents**:
- System Architect
- Database Specialist
- Scalability Engineer
- Integration Expert

### Security Audit Crew
**Purpose**: Deep security analysis, dependency scanning, threat modeling

**Agents**:
- Penetration Tester
- Cryptography Expert
- Compliance Specialist
- Dependency Auditor

### Performance Analysis Crew
**Purpose**: Load testing, optimization strategies, resource management

**Agents**:
- Load Testing Engineer
- Database Performance Expert
- Frontend Optimization Specialist
- Infrastructure Architect

### Business Impact Crew
**Purpose**: Analyze decisions for business value, ROI, strategic alignment

**Agents**:
- Business Analyst
- Product Manager
- Financial Analyst
- Market Researcher

---

## Tracking Progress

### Current Phase: Phase 1 - Code Review Crew

**Overall Progress**: 0% (Specification Complete)

| Task | Status | Estimated | Actual | Notes |
|------|--------|-----------|--------|-------|
| 1.1 Environment Setup | ⏳ Pending | 2-3h | - | - |
| 1.2 GitHub Tools | ⏳ Pending | 4-6h | - | - |
| 1.3 Agent Definitions | ⏳ Pending | 3-4h | - | - |
| 1.4 Task Definitions | ⏳ Pending | 3-4h | - | - |
| 1.5 Crew Implementation | ⏳ Pending | 4-6h | - | - |
| 1.6 Workflow Orchestration | ⏳ Pending | 3-4h | - | - |
| 1.7 Report Generation | ⏳ Pending | 3-4h | - | - |
| 1.8 GitHub Actions | ⏳ Pending | 3-4h | - | - |
| 1.9 Security Config | ⏳ Pending | 2-3h | - | - |
| 1.10 Testing | ⏳ Pending | 4-6h | - | - |
| 1.11 Documentation | ⏳ Pending | 2-3h | - | - |
| 1.12 Beta Rollout | ⏳ Pending | 1 week | - | - |

**Total Estimated**: 35-48 hours + 1 week monitoring

---

## Risks & Mitigations

### Risk 1: Cost Overruns
**Impact**: High
**Probability**: Medium

**Mitigation**:
- Set strict rate limits on OpenRouter API
- Monitor costs daily during beta
- Implement cost-based circuit breaker
- Cache LLM responses where possible

### Risk 2: Performance Issues
**Impact**: Medium
**Probability**: Medium

**Mitigation**:
- Set 5-minute timeout on crew execution
- Implement parallel agent execution
- Use efficient LLM models (not o1/o3)
- Optimize tool calls (minimize API requests)

### Risk 3: False Positives
**Impact**: Medium
**Probability**: High

**Mitigation**:
- Refine agent prompts based on feedback
- Implement severity levels (don't block on suggestions)
- Allow developers to dismiss findings
- Track false positive rate

### Risk 4: Token Limit Exceeded
**Impact**: Medium
**Probability**: Low

**Mitigation**:
- Limit input size (max files, max lines per file)
- Use chunking for large diffs
- Summarize context when approaching limits
- Use models with large context windows

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All 12 tasks completed
- [ ] Code review crew runs successfully on test PRs
- [ ] Average execution time < 5 minutes
- [ ] Average cost per review < $0.50
- [ ] No security issues in security review
- [ ] 80%+ test coverage
- [ ] Team feedback is positive
- [ ] Documentation is complete

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Get approval** to proceed with implementation
3. **Create GitHub Issues** for each task (Tasks 1.1-1.12)
4. **Assign owners** to tasks
5. **Begin Task 1.1**: Environment Setup

---

**Plan Status**: ✅ Ready for Review
**Created**: 2026-01-18
**Owner**: @borealBytes
**Estimated Completion**: 3-4 weeks from start
