# CrewAI Code Review Implementation Plan (REVISED)

> **Based on official [CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review) analysis**
>
> **Key Changes**: UV package manager, simplified agent structure (3 agents), added Related Files Analysis, PR comment posting in Phase 1

---

## Overview

This document outlines the implementation plan for integrating CrewAI multi-agent code review into the startup-blueprint repository's CI/CD pipeline, following CrewAI best practices and official demo patterns.

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
│   │   └── related_files_tool.py    # NEW: Find related files
│   ├── crew.py                      # Main Crew definition
│   ├── main.py                      # Entry point for GitHub Actions
│   ├── __init__.py
│   └── README.md                    # Usage documentation
├── .github/
│   └── workflows/
│       ├── ci.yml                   # Existing (unchanged)
│       └── crewai-review.yml        # NEW: CrewAI workflow
├── pyproject.toml                   # NEW: UV-managed dependencies
├── uv.lock                          # NEW: Locked dependencies
└── README.md                        # Updated with CrewAI setup
```

**Key Structure Decisions**:
- ✅ Use `crew.py` (not `crews/code_review_crew.py`) - matches official pattern
- ✅ Use `main.py` (not `workflows/orchestrator.py`) - standard entry point
- ✅ No `flows/` directory - we're using `Crew`, not `Flow`
- ✅ Tools in separate files by category

---

## Phase 1: Core Code Review Crew

**Timeline**: 2-3 weeks  
**Status**: 🏗️ Implementation Ready

### Agent Architecture (SIMPLIFIED)

**3 agents** (reduced from 5 for efficiency):

#### 1. Code Quality Reviewer
**Role**: Senior code reviewer  
**Focus**: Code style, maintainability, testing, best practices  
**Tools**: GitHubDiffTool, CommitInfoTool  
**Consolidates**: Code Quality + Test Engineer from original plan

#### 2. Security & Performance Analyst
**Role**: Security and performance specialist  
**Focus**: Vulnerabilities, performance bottlenecks, resource usage  
**Tools**: GitHubDiffTool, FileContentTool  
**Consolidates**: Security + Performance agents from original plan

#### 3. Architecture & Impact Analyst
**Role**: Software architect and impact assessor  
**Focus**: Design patterns, related file impacts, architectural decisions  
**Tools**: GitHubDiffTool, RelatedFilesTool (NEW)  
**New capability**: Analyzes files NOT directly modified but affected

**Why 3 agents?**
- Lower API costs (~60% reduction vs 5 agents)
- Faster execution (fewer sequential handoffs)
- Simpler to maintain and debug
- Matches official CrewAI demo pattern (2 agents) but adds architecture focus

---

## Task Workflow (6 Sequential Tasks)

### Task 1: Analyze Code Changes
**Agent**: Code Quality Reviewer  
**Input**: PR diff, commit messages  
**Output**: Code quality issues report (style, testing, maintainability)  
**Duration**: ~30-60 seconds

### Task 2: Security & Performance Review
**Agent**: Security & Performance Analyst  
**Input**: Task 1 output + diff  
**Output**: Security vulnerabilities + performance bottlenecks report  
**Duration**: ~45-90 seconds  
**Runs**: Sequentially after Task 1 (needs context)

### Task 3: Find Related Files (NEW - Inspired by Official Demo)
**Agent**: Architecture & Impact Analyst  
**Input**: Changed files list  
**Output**: List of functionally/logically related files  
**Tool**: RelatedFilesTool (analyzes imports, dependencies, shared patterns)  
**Duration**: ~20-30 seconds  
**Why critical**: Catches issues in files NOT directly modified

### Task 4: Analyze Related Files
**Agent**: Architecture & Impact Analyst  
**Input**: Task 3 output (related files)  
**Output**: Impact assessment on related components  
**Duration**: ~30-60 seconds

### Task 5: Architecture Review
**Agent**: Architecture & Impact Analyst  
**Input**: All previous task outputs  
**Output**: Architectural assessment + design recommendations  
**Duration**: ~30-60 seconds

### Task 6: Generate Review Comment (NEW - Phase 1)
**Agent**: Code Quality Reviewer (coordinator)  
**Input**: All task outputs  
**Output**: Comprehensive markdown review comment  
**Action**: Posts to PR via GitHub API  
**Duration**: ~15-30 seconds

**Total estimated time**: 3-5 minutes

---

## Implementation Tasks

### Task 1.1: Environment Setup with UV
**Estimated**: 2-3 hours

- [ ] Create `pyproject.toml` with project metadata:
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
  ]
  
  [project.optional-dependencies]
  dev = [
      "pytest>=8.0.0",
      "pytest-asyncio>=0.23.0",
      "ruff>=0.6.0",
  ]
  ```
- [ ] Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Run `crewai install` to generate `uv.lock`
- [ ] Create `.env.example` template
- [ ] Update `.gitignore`: add `uv.lock`, `.env`, `__pycache__`, `.pytest_cache`

### Task 1.2: GitHub Tools Development
**Estimated**: 5-7 hours

- [ ] `tools/github_tools.py`:
  - [ ] `GitHubDiffTool` - Get PR diff with file context
  - [ ] `CommitInfoTool` - Get commit metadata
  - [ ] `FileContentTool` - Read file contents from PR
  - [ ] `PRCommentTool` - Post review comment to PR (NEW)
- [ ] `tools/related_files_tool.py` (NEW):
  - [ ] Analyze import statements
  - [ ] Detect shared dependencies
  - [ ] Find files with similar patterns
  - [ ] Score relatedness (0-100)
- [ ] Add comprehensive error handling
- [ ] Implement GitHub API rate limiting
- [ ] Unit tests for all tools

### Task 1.3: Agent Definitions (agents.yaml)
**Estimated**: 2-3 hours

```yaml
code_quality_reviewer:
  role: Senior Code Reviewer
  goal: >
    Evaluate code changes for quality, style, testing, and maintainability.
    Provide actionable feedback with specific examples.
  backstory: >
    You are a senior software engineer with 15 years of experience.
    You've reviewed thousands of PRs and have a keen eye for code smells,
    testing gaps, and maintainability issues. You value clarity over cleverness.
  verbose: true
  allow_delegation: false

security_performance_analyst:
  role: Security and Performance Specialist
  goal: >
    Identify security vulnerabilities and performance bottlenecks.
    Flag critical issues that could impact production systems.
  backstory: >
    You are a security researcher and performance engineer.
    You've prevented numerous security breaches and optimized
    systems handling millions of requests. You think like an attacker
    and a performance engineer simultaneously.
  verbose: true
  allow_delegation: false

architecture_impact_analyst:
  role: Software Architect and Impact Assessor
  goal: >
    Assess architectural implications and identify files affected by changes.
    Evaluate design patterns and anticipate ripple effects.
  backstory: >
    You are a principal architect who has designed large-scale systems.
    You see connections others miss and anticipate how changes
    propagate through codebases. You value modularity and loose coupling.
  verbose: true
  allow_delegation: false
```

### Task 1.4: Task Definitions (tasks.yaml)
**Estimated**: 3-4 hours

```yaml
analyze_code_changes:
  description: >
    Analyze the code changes in this pull request.
    Focus on: code style, readability, test coverage, error handling,
    documentation, and adherence to best practices.
    
    Provide specific line references and actionable suggestions.
  expected_output: >
    A structured report with:
    - Summary of changes
    - Code quality issues (categorized by severity)
    - Missing tests
    - Documentation gaps
    - Specific recommendations with line numbers
  agent: code_quality_reviewer

security_performance_review:
  description: >
    Review code changes for security vulnerabilities and performance issues.
    Check for: SQL injection, XSS, auth bypasses, credential leaks,
    N+1 queries, memory leaks, inefficient algorithms, resource exhaustion.
    
    Flag critical security issues immediately.
  expected_output: >
    A report with:
    - Security vulnerabilities (CRITICAL/HIGH/MEDIUM)
    - Performance bottlenecks with impact estimates
    - Remediation steps for each issue
  agent: security_performance_analyst

find_related_files:
  description: >
    Identify files that are functionally or logically related to the changed files,
    even if they weren't directly modified in this PR.
    
    Analyze: imports, shared dependencies, similar patterns, architectural layers.
  expected_output: >
    A list of related files with:
    - File path
    - Relationship type (import, dependency, pattern)
    - Relatedness score (0-100)
    - Why it's related
  agent: architecture_impact_analyst

analyze_related_files:
  description: >
    Analyze the related files identified in the previous task.
    Assess potential impacts of the PR changes on these files.
    
    Consider: breaking changes, integration points, shared contracts.
  expected_output: >
    An impact assessment with:
    - Affected components
    - Potential breaking changes
    - Integration risks
    - Recommendations for additional testing
  agent: architecture_impact_analyst

architecture_review:
  description: >
    Evaluate architectural decisions in this PR.
    Consider: design patterns, SOLID principles, coupling, cohesion,
    scalability, and alignment with existing architecture.
    
    Reference insights from all previous tasks.
  expected_output: >
    An architectural assessment with:
    - Design pattern evaluation
    - Coupling and cohesion analysis
    - Scalability considerations
    - Alignment with project architecture
    - Long-term maintainability impact
  agent: architecture_impact_analyst

generate_review_comment:
  description: >
    Synthesize all agent findings into a comprehensive, actionable PR review comment.
    
    Format as markdown with:
    - Executive summary
    - Critical issues (must fix)
    - Warnings (should fix)
    - Suggestions (nice to have)
    - Code snippets with line numbers
    - Emoji for readability (🚨 critical, ⚠️ warning, 💡 suggestion)
    
    Post the comment to the PR using PRCommentTool.
  expected_output: >
    Posted PR comment with comprehensive review.
    Also return the markdown content for GitHub Actions summary.
  agent: code_quality_reviewer
```

### Task 1.5: Crew Implementation (crew.py)
**Estimated**: 4-6 hours

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import GitHubDiffTool, CommitInfoTool, FileContentTool, PRCommentTool
from tools.related_files_tool import RelatedFilesTool
import yaml
from pathlib import Path

@CrewBase
class CodeReviewCrew:
    """Code review crew for GitHub pull requests"""
    
    def __init__(self):
        config_dir = Path(__file__).parent / "config"
        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)
    
    # Agents
    @agent
    def code_quality_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_quality_reviewer'],
            tools=[GitHubDiffTool(), CommitInfoTool(), PRCommentTool()],
            verbose=True
        )
    
    @agent
    def security_performance_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['security_performance_analyst'],
            tools=[GitHubDiffTool(), FileContentTool()],
            verbose=True
        )
    
    @agent
    def architecture_impact_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['architecture_impact_analyst'],
            tools=[GitHubDiffTool(), FileContentTool(), RelatedFilesTool()],
            verbose=True
        )
    
    # Tasks
    @task
    def analyze_code_changes(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_code_changes'],
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
    def generate_review_comment(self) -> Task:
        return Task(
            config=self.tasks_config['generate_review_comment'],
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
                self.analyze_code_changes(),
                self.security_performance_review(),
                self.find_related_files(),
                self.analyze_related_files(),
                self.architecture_review(),
                self.generate_review_comment()
            ],
            process=Process.sequential,
            verbose=2
        )
```

### Task 1.6: Entry Point (main.py)
**Estimated**: 3-4 hours

```python
import os
import sys
from crew import CodeReviewCrew
from dotenv import load_dotenv

def main():
    """Entry point for GitHub Actions"""
    load_dotenv()
    
    # Get GitHub context from environment
    pr_number = os.getenv('GITHUB_PR_NUMBER')
    repo = os.getenv('GITHUB_REPOSITORY')
    sha = os.getenv('GITHUB_SHA')
    
    if not all([pr_number, repo, sha]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    print(f"🚀 Starting code review for PR #{pr_number}")
    print(f"📦 Repository: {repo}")
    print(f"📝 Commit: {sha[:8]}")
    
    try:
        crew = CodeReviewCrew()
        inputs = {
            'pr_number': pr_number,
            'repository': repo,
            'commit_sha': sha
        }
        
        print("\n🤖 Crew agents activated:")
        print("  1️⃣ Code Quality Reviewer")
        print("  2️⃣ Security & Performance Analyst")
        print("  3️⃣ Architecture & Impact Analyst")
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
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
```

### Task 1.7: GitHub Actions Workflow
**Estimated**: 3-4 hours

```yaml
name: CrewAI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  code-review:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for better context
      
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: |
          cd .crewai
          crewai install
      
      - name: Run CrewAI code review
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          cd .crewai
          python main.py
      
      - name: Upload review artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: crewai-review-logs
          path: .crewai/logs/
          retention-days: 7
```

### Task 1.8: Testing
**Estimated**: 5-7 hours

- [ ] Unit tests for each tool
- [ ] Mock GitHub API responses
- [ ] Test agent initialization
- [ ] Test task execution in isolation
- [ ] Integration test: full crew on sample PR
- [ ] Test error handling and timeouts
- [ ] Validate PR comment formatting

### Task 1.9: Documentation
**Estimated**: 2-3 hours

- [ ] Update `.crewai/README.md` with setup instructions
- [ ] Document agent behaviors
- [ ] Add troubleshooting guide
- [ ] Update root `README.md` with CrewAI section
- [ ] Document `OPENROUTER_API_KEY` in `.github/SECRETS.md`

---

## Phase 2: Enhanced Features (Future)

- [ ] Historical PR analysis (inspired by official demo)
- [ ] Custom rule engine per file type
- [ ] Auto-fix suggestions with code patches
- [ ] Cost tracking dashboard
- [ ] False positive feedback loop

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All agents and tasks implemented
- [ ] Review posts to PR comments (not just Actions summary)
- [ ] Related files analysis working
- [ ] Average execution time < 5 minutes
- [ ] Average cost per review < $0.30 (with 3 agents vs 5)
- [ ] 80%+ test coverage
- [ ] Zero API key leaks in logs

---

## Cost Comparison

### Original Plan (5 Agents)
- Estimated cost: ~$0.50/review
- Execution time: ~7-10 minutes

### Revised Plan (3 Agents)
- Estimated cost: ~$0.20-0.30/review (40-60% reduction)
- Execution time: ~3-5 minutes (50% faster)

**Savings over 100 PRs**: ~$25-40

---

## References

- [Official CrewAI PR Review Demo](https://github.com/crewAIInc/demo-pull-request-review)
- [CrewAI Documentation](https://docs.crewai.com/)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [CrewAI Installation Guide](https://docs.crewai.com/en/installation)

---

**Plan Status**: ✅ Ready for Implementation  
**Last Updated**: 2026-01-18  
**Based On**: Official CrewAI patterns + demo analysis