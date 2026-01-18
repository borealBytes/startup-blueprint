# CrewAI Infrastructure

## Overview

This directory contains the CrewAI multi-agent system for automated code review, business analysis, and decision-making support. CrewAI enables multiple AI agents to collaborate on complex tasks, each with specialized roles and expertise.

## Directory Structure

```
.crewai/
├── README.md                          # This file
├── IMPLEMENTATION_PLAN.md             # Phased implementation roadmap
├── config/
│   ├── agents.yaml                    # Agent definitions (roles, goals, backstories)
│   ├── tasks.yaml                     # Task definitions
│   └── llm.yaml                       # LLM provider configuration (OpenRouter)
├── crews/
│   ├── code-review/                   # Code review crew (Phase 1)
│   │   ├── spec.md                    # Detailed specification
│   │   ├── crew.py                    # Crew definition
│   │   ├── agents.py                  # Agent implementations
│   │   ├── tasks.py                   # Task implementations
│   │   └── tools.py                   # Custom tools for GitHub access
│   ├── architecture-review/           # Future: Architecture analysis
│   ├── security-audit/                # Future: Security scanning
│   ├── performance-analysis/          # Future: Performance recommendations
│   └── business-impact/               # Future: Business decision analysis
├── tools/
│   ├── github_tools.py                # GitHub API integration tools
│   └── security_tools.py              # Security-scoped access helpers
├── workflows/
│   └── code_review_workflow.py        # Orchestration logic
└── tests/
    ├── test_crews.py                  # Unit tests for crews
    └── test_tools.py                  # Unit tests for tools
```

## Phase 1: Code Review Crew (Current)

The first crew implements automated multi-perspective code review:

### Agents

1. **Senior Developer** - Code quality, best practices, maintainability
2. **Security Analyst** - Security vulnerabilities, sensitive data exposure
3. **Performance Engineer** - Performance implications, optimization opportunities
4. **Documentation Specialist** - Code clarity, documentation completeness
5. **Test Engineer** - Test coverage, edge cases, testing strategy

### Integration

- **Trigger**: GitHub Actions on pull request
- **Input**: Changed files, commit messages, PR description
- **Output**: Comprehensive review report in GitHub Actions summary
- **LLM**: OpenRouter API (supports multiple models)

## Security Model

### GitHub Token Scoping

The crew requires read-only access to:

- Repository contents
- Pull request metadata
- Commit history
- File diffs

**Token**: Uses GitHub Actions `GITHUB_TOKEN` with automatic read permissions

- ✅ Read repository content
- ✅ Read pull request data
- ❌ No write access (cannot modify code)
- ❌ No secrets access (scoped to public repo data)

### OpenRouter API Key

**Secret**: `OPENROUTER_API_KEY`

- Stored in GitHub Secrets
- Never logged or exposed
- Used only for LLM API calls
- Rate-limited and monitored

## Best Practices

### Agent Design

- **Single Responsibility**: Each agent has one clear role
- **Collaborative**: Agents can share insights and build on each other's work
- **Contextual**: Agents consider project-specific standards
- **Actionable**: Recommendations are specific and implementable

### Tool Development

- **Read-Only**: Tools cannot modify code or settings
- **Error Handling**: Graceful degradation on API failures
- **Rate Limiting**: Respect GitHub API limits
- **Caching**: Minimize redundant API calls

### Workflow Design

- **Fast**: Complete reviews in under 5 minutes
- **Informative**: Clear, structured output
- **Non-Blocking**: Warnings/suggestions, not hard failures
- **Expandable**: Easy to add new agents or tasks

## Future Crews (Planned)

### Architecture Review Crew

Analyzes system design, scalability, and architectural patterns

### Security Audit Crew

Deep security scanning, dependency analysis, threat modeling

### Performance Analysis Crew

Load testing recommendations, optimization strategies, resource usage

### Business Impact Crew

Analyzes decisions for business impact, ROI, strategic alignment

## Getting Started

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for the phased rollout strategy.

For the code review crew specification, see [`crews/code-review/spec.md`](./crews/code-review/spec.md).

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [OpenRouter API](https://openrouter.ai/docs)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub REST API](https://docs.github.com/en/rest)

---

**Status**: 🏗️ In Development
**Current Phase**: Phase 1 - Code Review Crew
**Last Updated**: 2026-01-18
