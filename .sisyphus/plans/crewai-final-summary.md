# Plan: Fix quick review output + final summary executive format

## Context
User sees fallback summary (short) because quick_review.json is empty; missing structured output. Need quick review to write code_issues.json and quick_review.json with findings. Final summary should be updated to include a short executive summary and collapsible sections for criticals, watch-outs, and positives, based only on JSON outputs from ran crews (router, CI, quick, full/legal if present).

## Tasks
- [ ] 1. Diagnose why quick review is not writing structured output (code_issues.json missing) and fix quick_review_crew/task configs to ensure code_issues.json + quick_review.json are always written.
- [ ] 2. Update final summary format to include a concise executive summary and collapsible sections for critical issues, watch-outs, and positive notes; source only from existing crew JSON outputs.
- [ ] 3. Add safeguards so final summary handles missing optional crew outputs cleanly without losing the required executive summary.
- [ ] 4. Verify with sample workspace inputs (from PR15 zip) that new outputs are produced and summary format matches expectations.
