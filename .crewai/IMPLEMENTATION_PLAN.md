# CrewAI Code Review Implementation Plan (FINAL)

> **Based on official [CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review) + project requirements**
>
> **Architecture**: 3-agent Crew, commit-based review, OpenAI API, CI-only Python environment

---

## Configuration Decisions ✅

### API Provider: OpenAI (Direct)
**API Key**: `CREWAI_OPENAI_KEY`  
**Provider**: OpenAI API directly (not OpenRouter)  
**Model**: `gpt-4o` (balanced performance/cost)  
**Fallback**: `gpt-4o-mini` (if budget constraints)

**Why OpenAI direct?**
- Simpler integration (one provider)
- Predictable pricing
- Official CrewAI support
- Better rate limits for single provider

### Review Scope: Commit-Based
**Focus**: All files updated in the commit  
**Priority Analysis**:
1. **Diff content** (lines added/removed) - highest priority
2. **New files** - full review
3. **Removed files** - impact assessment
4. **Commit message** - context and intent validation

**Why commit-based?**
- Matches developer workflow (commit → review)
- Clear scope per review
- Commit message provides context
- Easier to track review history

### Output Format: Executive Summary + Details
**Structure**:
```markdown
## 📊 Executive Summary
- Overall assessment (✅ LGTM | ⚠️ Needs Changes | 🚨 Critical Issues)
- Key metrics (files changed, lines added/removed, issues found)
- Top 3 action items

## 🔍 Detailed Findings

### 🚨 Critical Issues (Must Fix)
[High-priority blocking issues]

### ⚠️ Warnings (Should Fix)
[Important but non-blocking concerns]

### 💡 Suggestions (Nice to Have)
[Improvements and optimizations]

### ✅ Positive Observations
[Good patterns and practices found]
```

**Why this format?**
- Busy developers see summary first
- Detailed findings for deep dive
- Prioritized by severity
- Acknowledges good work (positive feedback)

### Python Environment: CI-Only, Isolated
**Setup**: Separate Python environment in GitHub Actions  
**Scope**: CrewAI dependencies only (not dev environment)  
**Management**: UV package manager with isolated venv  
**Location**: `.crewai/` directory with own `pyproject.toml`

**Why CI-only?**
- No Python requirement for Node.js developers
- Keeps dev setup simple
- CrewAI runs automatically in CI
- Best practice: separate CI tools from dev tools

---

## Overview

This document outlines the implementation plan for integrating CrewAI multi-agent code review into the startup-blueprint repository's CI/CD pipeline, following CrewAI best practices and project-specific requirements.

---

## Architecture Decision: Crew vs Flow

**Decision**: Use standard `Crew` class (not `Flow`)

**Rationale**:
- Official CrewAI PR review demo uses `Crew` with sequential processing
- `Flow` is overkill for linear task dependencies
- `Crew` is simpler, more maintainable, better documented
- Sequential execution ensures proper context passing between agents

---

## Project Structure (Official CrewAI Convention)

```
startup-blueprint/
├── .crewai/
│   ├── config/
│   │   ├── agents.yaml              # 3 agent definitions
│   │   └── tasks.yaml               # 6 task definitions
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── github_tools.py          # GitHub API integration
│   │   └── related_files_tool.py    # Find related files
│   ├── crew.py                      # Main Crew definition
│   ├── main.py                      # Entry point for GitHub Actions
│   ├── pyproject.toml               # Isolated Python dependencies
│   ├── uv.lock                      # Locked dependency versions
│   ├── .env.example                 # Template for local testing
│   ├── __init__.py
│   └── README.md                    # Usage documentation
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                   # Existing (unchanged)
│   │   └── crewai-review.yml        # NEW: CrewAI workflow
│   └── SECRETS.md                   # Updated: Document CREWAI_OPENAI_KEY
└── README.md                        # Updated with CrewAI section
```

**Key Structure Decisions**:
- ✅ `.crewai/` has own `pyproject.toml` (isolated Python environment)
- ✅ Use `crew.py` (matches official pattern)
- ✅ Use `main.py` (standard entry point)
- ✅ No `flows/` directory (using `Crew`, not `Flow`)
- ✅ Tools in separate files by category

---

## Phase 1: Core Code Review Crew

**Timeline**: 2-3 weeks  
**Status**: 🏗️ Implementation Ready

### Agent Architecture (3 Specialized Agents)

#### 1. Code Quality Reviewer
**Role**: Senior code reviewer  
**Focus**: 
- Code style, readability, maintainability
- Test coverage and quality
- Documentation completeness
- Commit message quality

**Tools**: GitHubDiffTool, CommitInfoTool, PRCommentTool  
**Consolidates**: Code Quality + Test Engineer from original plan

#### 2. Security & Performance Analyst
**Role**: Security researcher + performance engineer  
**Focus**: 
- Security vulnerabilities (SQL injection, XSS, auth issues)
- Credential leaks, hardcoded secrets
- Performance bottlenecks (N+1 queries, memory leaks)
- Resource usage optimization

**Tools**: GitHubDiffTool, FileContentTool  
**Consolidates**: Security + Performance agents from original plan

#### 3. Architecture & Impact Analyst
**Role**: Software architect + impact assessor  
**Focus**: 
- Design patterns and architectural decisions
- Related file impact analysis
- Coupling, cohesion, modularity
- Scalability and long-term maintainability

**Tools**: GitHubDiffTool, FileContentTool, RelatedFilesTool  
**New capability**: Analyzes files NOT directly modified but affected

**Why 3 agents?**
- Lower API costs (~60% reduction vs 5 agents)
- Faster execution (fewer sequential handoffs)
- Simpler to maintain and debug
- Matches official CrewAI demo pattern (2 agents) but adds architecture focus

---

## Task Workflow (6 Sequential Tasks)

### Task 1: Analyze Commit Changes
**Agent**: Code Quality Reviewer  
**Input**: 
- Commit SHA, diff, message
- Files modified (new, changed, removed)
- Lines added/removed per file

**Output**: Code quality issues report with:
- Commit message assessment
- Style and readability issues
- Testing gaps
- Documentation needs

**Duration**: ~30-60 seconds

### Task 2: Security & Performance Review
**Agent**: Security & Performance Analyst  
**Input**: Task 1 output + commit diff  
**Output**: 
- Security vulnerabilities (CRITICAL/HIGH/MEDIUM)
- Performance bottlenecks
- Resource usage concerns

**Duration**: ~45-90 seconds  
**Runs**: Sequentially after Task 1 (needs quality context)

### Task 3: Find Related Files
**Agent**: Architecture & Impact Analyst  
**Input**: Changed files list from commit  
**Output**: 
- Related files (imports, dependencies, patterns)
- Relatedness scores (0-100)
- Why each file is related

**Tool**: RelatedFilesTool  
**Duration**: ~20-30 seconds  
**Why critical**: Catches issues in files NOT in commit

### Task 4: Analyze Related Files
**Agent**: Architecture & Impact Analyst  
**Input**: Task 3 output (related files)  
**Output**: 
- Impact assessment on related components
- Potential breaking changes
- Integration risks
- Testing recommendations

**Duration**: ~30-60 seconds

### Task 5: Architecture Review
**Agent**: Architecture & Impact Analyst  
**Input**: All previous task outputs + commit intent  
**Output**: 
- Design pattern evaluation
- Coupling and cohesion analysis
- Alignment with project architecture
- Long-term maintainability impact

**Duration**: ~30-60 seconds

### Task 6: Generate Executive Summary & Post
**Agent**: Code Quality Reviewer (coordinator)  
**Input**: All task outputs  
**Output Format**:
```markdown
## 📊 Executive Summary
- Overall: ✅ LGTM | ⚠️ Needs Changes | 🚨 Critical Issues
- Files: 5 modified, 2 new, 0 removed
- Changes: +245 lines, -87 lines
- Issues: 0 critical, 2 warnings, 5 suggestions
- Top Actions:
  1. Fix SQL injection in auth.py:45
  2. Add tests for new user validation
  3. Document breaking change in API

## 🔍 Detailed Findings
[Detailed sections from all agents]
```

**Action**: Posts to PR as comment  
**Duration**: ~15-30 seconds

**Total estimated time**: 3-5 minutes

---

## Implementation Tasks

### Task 1.1: Environment Setup with UV (CI-Only)
**Estimated**: 2-3 hours

- [ ] Create `.crewai/pyproject.toml` (isolated from root):
  ```toml
  [project]
  name = "startup-blueprint-crewai"
  version = "0.1.0"
  requires-python = ">=3.10 <=3.13"
  dependencies = [
      "crewai>=0.86.0",
      "crewai-tools>=0.12.0",
      "PyGithub>=2.1.1",
      "python-dotenv>=1.0.0",
      "openai>=1.10.0",  # Direct OpenAI API
  ]
  
  [project.optional-dependencies]
  dev = [
      "pytest>=8.0.0",
      "pytest-asyncio>=0.23.0",
      "ruff>=0.6.0",
  ]
  ```

- [ ] Create `.crewai/.env.example`:
  ```bash
  # OpenAI API Key for CrewAI agents
  CREWAI_OPENAI_KEY=sk-...
  
  # GitHub API (auto-provided in Actions)
  GITHUB_TOKEN=ghp_...
  GITHUB_REPOSITORY=owner/repo
  GITHUB_PR_NUMBER=1
  GITHUB_SHA=abc123
  ```

- [ ] Update root `.gitignore`:
  ```
  # CrewAI environment
  .crewai/.env
  .crewai/__pycache__/
  .crewai/.pytest_cache/
  .crewai/uv.lock
  .crewai/logs/
  ```

- [ ] Document in README: "CrewAI runs in CI only, no local Python setup required"

### Task 1.2: GitHub Tools Development (Commit-Focused)
**Estimated**: 5-7 hours

- [ ] `tools/github_tools.py`:
  - [ ] `CommitDiffTool` - Get commit diff with added/removed line numbers
  - [ ] `CommitInfoTool` - Get commit message, author, timestamp, file stats
  - [ ] `FileContentTool` - Read full file content for context
  - [ ] `PRCommentTool` - Post review with executive summary format
  
- [ ] `tools/related_files_tool.py`:
  - [ ] Parse imports from changed files
  - [ ] Find files importing changed files
  - [ ] Detect shared dependencies
  - [ ] Score relatedness (0-100)
  
- [ ] Add comprehensive error handling
- [ ] Implement GitHub API rate limiting
- [ ] Unit tests with mocked GitHub API

### Task 1.3: Agent Definitions (agents.yaml)
**Estimated**: 2-3 hours

```yaml
code_quality_reviewer:
  role: Senior Code Reviewer
  goal: >
    Evaluate commit changes for code quality, testing, and documentation.
    Assess commit message clarity and intent.
    Coordinate final executive summary with prioritized action items.
  backstory: >
    You are a senior software engineer with 15 years of experience.
    You've reviewed thousands of commits and understand the importance
    of clear commit messages and well-tested code. You synthesize
    findings from multiple perspectives into actionable feedback.
  verbose: true
  allow_delegation: false

security_performance_analyst:
  role: Security and Performance Specialist
  goal: >
    Identify security vulnerabilities and performance issues in commit changes.
    Flag critical issues immediately with severity levels.
    Focus on diff content: what was added, what was removed, and why it matters.
  backstory: >
    You are a security researcher and performance engineer.
    You've prevented breaches by catching issues in commit reviews.
    You think like an attacker and optimizer simultaneously,
    always considering the worst-case scenario.
  verbose: true
  allow_delegation: false

architecture_impact_analyst:
  role: Software Architect and Impact Assessor
  goal: >
    Assess architectural implications of commit changes.
    Identify files affected beyond the commit itself.
    Evaluate long-term maintainability and scalability impact.
  backstory: >
    You are a principal architect who has designed large-scale systems.
    You see the ripple effects of changes others miss.
    You anticipate how today's commit affects tomorrow's architecture.
    You value modularity, loose coupling, and clear boundaries.
  verbose: true
  allow_delegation: false
```

### Task 1.4: Task Definitions (tasks.yaml) - Executive Summary Format
**Estimated**: 3-4 hours

```yaml
analyze_commit_changes:
  description: >
    Analyze all files changed in this commit.
    Focus on: diff content (lines added/removed), new files, removed files.
    Evaluate: code style, readability, test coverage, documentation.
    Assess commit message: does it clearly explain what and why?
    
    Provide specific line references from the diff.
  expected_output: >
    A structured report with:
    - Commit message assessment (clear/unclear, follows conventions)
    - Files changed breakdown (new, modified, removed)
    - Code quality issues by file (severity: high/medium/low)
    - Missing tests for new functionality
    - Documentation gaps
    - Specific recommendations with line numbers
  agent: code_quality_reviewer

security_performance_review:
  description: >
    Review commit diff for security and performance issues.
    Focus on lines added (new attack surface) and removed (breaking changes).
    Check for: SQL injection, XSS, auth bypasses, hardcoded secrets,
    N+1 queries, memory leaks, inefficient algorithms.
    
    Flag CRITICAL issues that block merge.
  expected_output: >
    A report with:
    - Security vulnerabilities (CRITICAL/HIGH/MEDIUM) with CVE references
    - Performance bottlenecks with estimated impact
    - Hardcoded secrets or credentials (immediate block)
    - Remediation steps for each issue
  agent: security_performance_analyst

find_related_files:
  description: >
    Identify files functionally or logically related to changed files,
    even if NOT modified in this commit.
    
    Analyze: imports, dependencies, shared patterns, architectural layers.
    This finds hidden impacts not visible in the commit diff.
  expected_output: >
    A list of related files with:
    - File path
    - Relationship type (imports, imported by, shared dependency, pattern)
    - Relatedness score (0-100)
    - Why it's related and potential impact
  agent: architecture_impact_analyst

analyze_related_files:
  description: >
    Analyze the related files identified in the previous task.
    Assess potential impacts of this commit's changes on those files.
    
    Consider: breaking changes, interface modifications, shared contracts.
  expected_output: >
    An impact assessment with:
    - Affected components and their criticality
    - Potential breaking changes (with migration steps)
    - Integration risks (API changes, data format changes)
    - Recommendations for additional testing
  agent: architecture_impact_analyst

architecture_review:
  description: >
    Evaluate architectural implications of this commit.
    Consider: design patterns, SOLID principles, coupling, cohesion,
    scalability, and alignment with existing architecture.
    
    Reference insights from all previous tasks to provide holistic view.
  expected_output: >
    An architectural assessment with:
    - Design pattern evaluation (appropriate/inappropriate)
    - Coupling and cohesion analysis
    - Scalability considerations (will this scale?)
    - Alignment with project architecture (consistent/divergent)
    - Long-term maintainability impact (tech debt introduced/reduced)
  agent: architecture_impact_analyst

generate_executive_summary:
  description: >
    Synthesize all agent findings into executive summary + detailed review.
    
    Format as markdown:
    1. Executive Summary (4-5 sentences, overall assessment, top 3 actions)
    2. Detailed Findings:
       - 🚨 Critical Issues (must fix before merge)
       - ⚠️ Warnings (should fix soon)
       - 💡 Suggestions (nice to have)
       - ✅ Positive Observations (good patterns found)
    
    Use emojis, code snippets with line numbers, and clear action items.
    Post the complete review to PR using PRCommentTool.
  expected_output: >
    Posted PR comment with:
    - Executive summary (overall assessment, metrics, top actions)
    - Detailed findings (critical/warning/suggestion/positive)
    - Code snippets with file:line references
    - Clear next steps for developer
    
    Also return markdown for GitHub Actions summary.
  agent: code_quality_reviewer
```

### Task 1.5: Crew Implementation (crew.py) - OpenAI Configuration
**Estimated**: 4-6 hours

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI
from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool, PRCommentTool
from tools.related_files_tool import RelatedFilesTool
import yaml
import os
from pathlib import Path

@CrewBase
class CodeReviewCrew:
    """Code review crew for GitHub commit analysis"""
    
    def __init__(self):
        config_dir = Path(__file__).parent / "config"
        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)
        
        # Configure OpenAI LLM
        api_key = os.getenv('CREWAI_OPENAI_KEY')
        if not api_key:
            raise ValueError("CREWAI_OPENAI_KEY environment variable required")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # or "gpt-4o-mini" for cost savings
            api_key=api_key,
            temperature=0.3,  # Lower temp for consistent reviews
        )
    
    # Agents
    @agent
    def code_quality_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_quality_reviewer'],
            tools=[CommitDiffTool(), CommitInfoTool(), PRCommentTool()],
            llm=self.llm,
            verbose=True
        )
    
    @agent
    def security_performance_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['security_performance_analyst'],
            tools=[CommitDiffTool(), FileContentTool()],
            llm=self.llm,
            verbose=True
        )
    
    @agent
    def architecture_impact_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['architecture_impact_analyst'],
            tools=[CommitDiffTool(), FileContentTool(), RelatedFilesTool()],
            llm=self.llm,
            verbose=True
        )
    
    # Tasks
    @task
    def analyze_commit_changes(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_commit_changes'],
            agent=self.code_quality_reviewer()
        )
    
    @task
    def security_performance_review(self) -> Task:
        return Task(
            config=self.tasks_config['security_performance_review'],
            agent=self.security_performance_analyst()
        )
    
    @task
    def find_related_files(self) -> Task:
        return Task(
            config=self.tasks_config['find_related_files'],
            agent=self.architecture_impact_analyst()
        )
    
    @task
    def analyze_related_files(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_related_files'],
            agent=self.architecture_impact_analyst()
        )
    
    @task
    def architecture_review(self) -> Task:
        return Task(
            config=self.tasks_config['architecture_review'],
            agent=self.architecture_impact_analyst()
        )
    
    @task
    def generate_executive_summary(self) -> Task:
        return Task(
            config=self.tasks_config['generate_executive_summary'],
            agent=self.code_quality_reviewer()
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.code_quality_reviewer(),
                self.security_performance_analyst(),
                self.architecture_impact_analyst()
            ],
            tasks=[
                self.analyze_commit_changes(),
                self.security_performance_review(),
                self.find_related_files(),
                self.analyze_related_files(),
                self.architecture_review(),
                self.generate_executive_summary()
            ],
            process=Process.sequential,
            verbose=2
        )
```

### Task 1.6: Entry Point (main.py) - Commit Context
**Estimated**: 3-4 hours

```python
import os
import sys
from crew import CodeReviewCrew
from dotenv import load_dotenv

def main():
    """Entry point for GitHub Actions - commit-based review"""
    load_dotenv()
    
    # Get GitHub context from environment
    pr_number = os.getenv('GITHUB_PR_NUMBER')
    repo = os.getenv('GITHUB_REPOSITORY')
    sha = os.getenv('GITHUB_SHA')
    api_key = os.getenv('CREWAI_OPENAI_KEY')
    
    if not all([pr_number, repo, sha, api_key]):
        print("❌ Missing required environment variables")
        print(f"   PR: {pr_number}, Repo: {repo}, SHA: {sha[:8] if sha else 'None'}")
        print(f"   API Key: {'Set' if api_key else 'Missing'}")
        sys.exit(1)
    
    print(f"🚀 Starting code review for commit in PR #{pr_number}")
    print(f"📦 Repository: {repo}")
    print(f"📝 Commit SHA: {sha[:8]}")
    print()
    
    try:
        crew = CodeReviewCrew()
        inputs = {
            'pr_number': pr_number,
            'repository': repo,
            'commit_sha': sha,
            'review_scope': 'commit',  # Focus on commit changes
        }
        
        print("🤖 Crew agents activated:")
        print("  1️⃣ Code Quality Reviewer (coordinator)")
        print("  2️⃣ Security & Performance Analyst")
        print("  3️⃣ Architecture & Impact Analyst")
        print()
        print("📋 Review scope: All files in commit + related file impacts")
        print("📊 Output format: Executive summary + detailed findings")
        print()
        
        result = crew.crew().kickoff(inputs=inputs)
        
        print("\n✅ Code review complete!")
        print(f"📊 Review posted to PR #{pr_number}")
        
        # Write to GitHub Actions summary
        summary_file = os.getenv('GITHUB_STEP_SUMMARY')
        if summary_file:
            with open(summary_file, 'a') as f:
                f.write("\n## 🤖 CrewAI Code Review\n\n")
                f.write(result)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during code review: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
```

### Task 1.7: GitHub Actions Workflow (CI-Only Python)
**Estimated**: 3-4 hours

```yaml
name: CrewAI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
  # Optional: Also review direct pushes to feature branches
  push:
    branches-ignore:
      - main
      - master

permissions:
  contents: read
  pull-requests: write

jobs:
  crewai-review:
    name: AI Code Review
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    # Only run on actual code changes, skip bot PRs
    if: |
      github.actor != 'dependabot[bot]' &&
      github.actor != 'renovate[bot]'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for related file analysis
      
      - name: Setup Python (CI-only)
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install UV package manager
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install CrewAI dependencies (isolated)
        run: |
          cd .crewai
          uv venv
          source .venv/bin/activate
          uv pip install -e .
      
      - name: Run CrewAI code review
        env:
          CREWAI_OPENAI_KEY: ${{ secrets.CREWAI_OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number || github.event.number }}
          GITHUB_SHA: ${{ github.event.pull_request.head.sha || github.sha }}
        run: |
          cd .crewai
          source .venv/bin/activate
          python main.py
      
      - name: Upload review logs (debugging)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: crewai-review-logs-${{ github.run_number }}
          path: .crewai/logs/
          retention-days: 7
```

### Task 1.8: Testing
**Estimated**: 5-7 hours

- [ ] Unit tests for each tool (mocked GitHub API)
- [ ] Test commit diff parsing (added/removed lines)
- [ ] Test related files analysis (imports detection)
- [ ] Test executive summary formatting
- [ ] Integration test: full crew on sample commit
- [ ] Test error handling (missing API key, rate limits)
- [ ] Validate PR comment markdown rendering

### Task 1.9: Documentation
**Estimated**: 2-3 hours

- [ ] Update `.crewai/README.md`:
  - CI-only setup (no local Python required)
  - OpenAI API key setup (`CREWAI_OPENAI_KEY`)
  - Commit-based review scope
  - Executive summary output format
- [ ] Update `.github/SECRETS.md`:
  - Document `CREWAI_OPENAI_KEY` (rotation: 90 days)
  - Permissions required
- [ ] Update root `README.md`:
  - "Automated AI code review in CI" section
  - Note: "No Python setup required for developers"

---
## Success Criteria

### Phase 1 Complete When:
- [ ] All 3 agents implemented with OpenAI LLM
- [ ] Commit-based review working (all changed files analyzed)
- [ ] Executive summary + detailed findings format
- [ ] Related files analysis catching hidden impacts
- [ ] CI-only Python environment (no dev setup required)
- [ ] Reviews post to PR comments
- [ ] Average execution time < 5 minutes
- [ ] Average cost per review < $0.25 (OpenAI gpt-4o)
- [ ] 80%+ test coverage
- [ ] Zero API key leaks in logs

---

## Cost Estimates (OpenAI Direct)

### Per Review (gpt-4o)
- **3 agents** × ~$0.07 per agent = **~$0.21 per review**
- Input tokens: ~50K (commit diff + context)
- Output tokens: ~2K (executive summary + details)

### Per Review (gpt-4o-mini) - Budget Option
- **3 agents** × ~$0.02 per agent = **~$0.06 per review**
- Same quality for most reviews

### Monthly (100 PRs)
- **gpt-4o**: ~$21/month
- **gpt-4o-mini**: ~$6/month
- **Hybrid** (mini for small PRs, full for large): ~$12/month

**ROI**: ~5 hours of human review time saved/month

---

## References

- [Official CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review)
- [CrewAI Documentation](https://docs.crewai.com/)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [GitHub Actions: Isolated Environments](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

---

**Plan Status**: ✅ Ready for Implementation  
**Last Updated**: 2026-01-18  
**API Provider**: OpenAI (CREWAI_OPENAI_KEY)  
**Review Scope**: Commit-based (all changed files)  
**Output Format**: Executive summary + detailed findings  
**Python Setup**: CI-only, isolated environment