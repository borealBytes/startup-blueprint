# Development Backlog

> **Format:** `- [ ] [P#] [domain] Description... Est: Nd. BRANCH: \`branch-name\` PR: #NNN`
>
> **Priority:** P0 (highest) → P3 (lowest)  
> **Status:** To Triage → High Priority → In Progress → Done

---

## 📋 To Triage (New Items)

<!-- Add new work here first -->

---

## ⚡ High Priority (Next Up)

<!-- Move triaged P0/P1 items here -->

- [ ] [P1] [ci] Update core-ci job with complete log capture. Est: 1h.
- [ ] [P1] [ci] Update test-crewai job with complete log capture. Est: 1h.
- [ ] [P1] [ci] Update test-build-website job with complete log capture. Est: 1h.
- [ ] [P1] [crewai] Update CI analysis crew to use new CI tools with smart workflow. Est: 2h.
- [ ] [P2] [ci] Add validation tests for log capture in CI workflow. Est: 1h.
- [ ] [P2] [docs] Add examples to CI log capture implementation doc. Est: 30m.

---

## 🚧 In Progress

<!-- Active work with assigned branches/PRs -->

- [x] [P0] [ci] Create composite action for job output capture. Est: 1h. BRANCH: `feat/crewai-optimize-crew` PR: TBD
  - ✅ Two modes: start/finish
  - ✅ Captures logs, summary, metadata
  - ✅ Uploads as artifact

- [x] [P0] [ci] Update credential-validation job with complete log capture. Est: 1h. BRANCH: `feat/crewai-optimize-crew` PR: TBD
  - ✅ Initialize capture at start
  - ✅ Log all setup steps
  - ✅ Capture validation output
  - ✅ Finalize capture at end

- [x] [P0] [crewai] Create intelligent CI log analysis tools. Est: 2h. BRANCH: `feat/crewai-optimize-crew` PR: TBD
  - ✅ read_job_index
  - ✅ check_log_size
  - ✅ read_job_summary
  - ✅ search_log
  - ✅ read_full_log
  - ✅ get_log_stats

- [x] [P0] [ci] Update CrewAI workflow to download artifacts and organize workspace. Est: 2h. BRANCH: `feat/crewai-optimize-crew` PR: TBD
  - ✅ Download ci-job-output-\* artifacts
  - ✅ Organize into workspace/ci_results/
  - ✅ Build job index
  - ✅ Capture CrewAI's own execution

- [x] [P0] [docs] Document CI log capture implementation. Est: 2h. BRANCH: `feat/crewai-optimize-crew` PR: TBD
  - ✅ Architecture overview
  - ✅ Component descriptions
  - ✅ Workflow guide
  - ✅ Tool usage patterns

---

## ✅ Done

<!-- Completed items for historical reference -->

---

## 🔮 Future Enhancements

<!-- Nice-to-have features for later -->

- [ ] [P3] [ci] Add log compression for jobs with > 10MB output. Est: 2h.
- [ ] [P3] [crewai] Create streaming log analysis for extremely large logs. Est: 3h.
- [ ] [P3] [web] Build visual log viewer UI with syntax highlighting. Est: 1d.
- [ ] [P3] [ci] Add historical comparison (compare current run to previous runs). Est: 1d.
- [ ] [P3] [monitoring] Add metrics dashboard for CI job trends and costs. Est: 2d.

---

## 📝 Notes

### CI Log Capture System

**Status:** Core components complete, job updates in progress

**Completed:**

- ✅ Composite action (`.github/actions/capture-job-output/action.yml`)
- ✅ CI tools (`.crewai/tools/ci_tools.py`)
- ✅ CrewAI workflow updates (`.github/workflows/crewai-review-reusable.yml`)
- ✅ Credential validation job (`.github/workflows/validate-environment-reusable.yml`)
- ✅ Documentation (`docs/ci-log-capture-implementation.md`)

**Remaining Work:**

1. Update core-ci job pattern
2. Update test-crewai job pattern
3. Update test-build-website job pattern
4. Update CI analysis crew to use new tools
5. Add integration tests

**Architecture:**

- Jobs capture their own logs → upload as artifacts
- CrewAI downloads artifacts → organizes into workspace
- Smart tools check size before reading
- No API scraping needed = no rate limits

**Benefits:**

- Complete visibility into all CI jobs
- Intelligent size-aware log handling
- Efficient token usage (grep vs full read)
- Artifact-based (no API limits)
- Complete audit trail (including CrewAI execution)

---

**Last Updated:** 2026-01-30  
**Current Sprint:** CI Log Capture Implementation
