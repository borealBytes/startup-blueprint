# PR #00011: feat(crewai): Optimize Crew

**Branch:** `feat/crewai-optimize-crew`
**Base:** `feat/clean-custom-preview`
**Status:** Draft
**Created:** 2026-01-28

---

## Summary

Comprehensive optimization of the CrewAI code review system to make it reliable, cost-effective, and smarter over time. This PR focuses on getting the review crew fully operational, expanding the "board of directors" with additional specialized reviewers, and enabling memory so the system learns from previous runs.

---

## Goals

### 1. Reliability: Get CrewAI Review Working Reliably

- [ ] Debug and fix current crew execution issues
- [ ] Ensure consistent output format across all agents
- [ ] Add proper error handling and fallback behavior
- [ ] Validate end-to-end workflow from PR trigger to comment posting

### 2. Cost Optimization: Switch to Cheaper Models

- [ ] Evaluate current model costs vs quality tradeoffs
- [ ] Current: `xiaomi/mimo-v2-flash` via OpenRouter
- [ ] Consider: `gemini-2.0-flash`, `claude-3-haiku`, `gpt-4o-mini`
- [ ] Implement tiered model selection based on PR complexity
- [ ] Add cost tracking/logging per review (partially done via LiteLLM callbacks)

### 3. Expand the Board of Directors

Add specialized reviewers to create a comprehensive "board" that covers all aspects of code review:

| Agent                          | Role                                          | Status              |
| ------------------------------ | --------------------------------------------- | ------------------- |
| Router                         | Decides which reviewers need to be involved   | Exists (needs work) |
| Quick Reviewer                 | Fast quality check for simple PRs             | Exists              |
| Code Quality Reviewer          | Deep code analysis                            | Exists              |
| Security & Performance Analyst | Vulnerabilities and bottlenecks               | Exists              |
| Architecture & Impact Analyst  | Design patterns, related files                | Exists              |
| Executive Summary Agent        | Final synthesis                               | Exists              |
| Legal Compliance Reviewer      | License, ToS, copyright                       | Stub exists         |
| **Security Reviewer**          | Dedicated deep security review                | **To enhance**      |
| **Marketing Reviewer**         | User-facing changes, messaging, branding      | **To add**          |
| **Board of Directors**         | High-level strategic review for major changes | **To add**          |

### 4. Smart Routing with PR Tags

- [ ] Implement PR label detection for forced review paths
  - `review:security` → Force security review
  - `review:legal` → Force legal review
  - `review:full` → Force full review (all agents)
  - `review:quick` → Force quick review only
  - `review:marketing` → Force marketing review
- [ ] Allow router to suggest additional labels when relevant files are detected
- [ ] Document label conventions

### 5. Memory System

Enable CrewAI to learn from previous runs and maintain context.

#### 5.1 Short-Term Memory (Within CI Run)

- [ ] Enable ChromaDB-based short-term memory
- [ ] Agents can recall context from earlier tasks in same run
- [ ] Ephemeral - cleared when CI run finishes
- [ ] Configuration: `memory=True` in Crew

#### 5.2 Long-Term Memory (Git-Based Persistence)

**Architecture:**

```
.crewai/
├── memory/
│   └── memory.jsonl          # Source of truth (git tracked)
└── state/
    └── long_term_memory_storage.db  # SQLite cache (gitignored)
```

**Behavior:**

| Phase          | Action                                 |
| -------------- | -------------------------------------- |
| **Startup**    | Rebuild SQLite from `memory.jsonl`     |
| **During Run** | Append events to `memory.jsonl`        |
| **After Run**  | Commit to same branch with `[skip ci]` |

**CI Loop Prevention:**

- Commit message includes `[skip ci]`
- Workflow guard: skip if `actor == github-actions[bot]`
- Result: Human commits trigger CI, memory commits do not

**What Gets Stored:**

- Executive summaries from each run
- Issues found and their categories
- Recurring patterns detected
- File paths and issue types for indexing

**Query Capabilities:**

- "What did we say about this file last time?"
- "Have we seen similar security issues before?"
- "Is this the same error pattern as PR #X?"
- Diff current summary vs previous run

#### 5.3 Embedder Configuration

- **Provider:** OpenAI `text-embedding-3-small`
- **Cost:** ~$0.00002 per 1K tokens (negligible)
- **Requirement:** Add `OPENAI_API_KEY` to GitHub secrets

```python
crew = Crew(
    memory=True,
    embedder={
        "provider": "openai",
        "config": {"model_name": "text-embedding-3-small"}
    }
)
```

---

## Technical Implementation

### Memory Storage Implementation

**Custom LTM Storage Class:**

```python
from crewai.memory.storage.interface import Storage
import json
from pathlib import Path

class GitJSONLStorage(Storage):
    """Long-term memory storage using git-tracked JSONL."""

    def __init__(self, jsonl_path: str = ".crewai/memory/memory.jsonl"):
        self.jsonl_path = Path(jsonl_path)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, value, metadata=None, agent=None):
        """Append memory event to JSONL file."""
        record = {
            "value": value,
            "metadata": metadata,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(self.jsonl_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def search(self, query, limit=10, score_threshold=0.5):
        """Search memories (rebuild SQLite index first)."""
        # Implementation: Load JSONL, use embeddings for similarity
        pass

    def reset(self):
        """Clear all memories."""
        self.jsonl_path.unlink(missing_ok=True)
```

### CI Commit Script

```bash
#!/bin/bash
# .crewai/scripts/commit-memory.sh

MEMORY_FILE=".crewai/memory/memory.jsonl"

if git diff --quiet "$MEMORY_FILE" 2>/dev/null; then
    echo "No memory changes to commit"
    exit 0
fi

git add "$MEMORY_FILE"
git commit -m "chore(memory): update long-term memory [skip ci]"
git push origin HEAD
```

### Gitignore Updates

```gitignore
# CrewAI state (ephemeral, rebuilt from memory.jsonl)
.crewai/state/
```

---

## Success Criteria

- [ ] Reviews complete successfully on 10 consecutive PRs
- [ ] Average review cost < $0.05 per PR
- [ ] Memory system captures and recalls previous findings
- [ ] Router correctly identifies when to invoke specialized reviewers
- [ ] PR labels correctly force specific review paths
- [ ] No CI loops from memory commits

---

## Related Files

- `.crewai/crew.py` - Main crew definition (add memory config)
- `.crewai/config/agents.yaml` - Agent definitions
- `.crewai/crews/` - Individual crew implementations
- `.crewai/tools/` - Tool implementations
- `.github/workflows/crewai-review.yml` - GitHub Actions trigger
- `.gitignore` - Add `.crewai/state/`

---

## References

- [CrewAI Memory Docs](https://docs.crewai.com/concepts/memory)
- [CrewAI Storage Interface](https://docs.crewai.com/concepts/memory#custom-storage-implementation)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

## Changelog

| Date       | Change                                                   |
| ---------- | -------------------------------------------------------- |
| 2026-01-28 | Initial PR document created                              |
| 2026-01-28 | Added memory implementation details (git-based JSONL)    |
| 2026-01-28 | Decided: Enable short-term memory with OpenAI embeddings |
