# Draft: CrewAI Final Summary Missing

## Requirements (confirmed)
- User reports final “⚠️ Review Summary” not appearing in output.
- Quick review reports: “completed but did not write structured output.”
- Provided workspace zip: `~/Downloads/crewai-agent-workspace-pr15-21530729348.zip`.
- Goal: debug why new crew outputs aren’t written and ensure final summary includes them.
- User approved inspecting the workspace zip.
- User wants to **update** the final summary format (not just keep current).
- Priority: fix quick review outputs first.

## Technical Decisions
- None yet.

## Research Findings
- Pending: inspect workspace zip contents for missing JSON outputs.
- Pending: confirm which branch/path to analyze (clean-custom-preview, feat/crewai-optimize-crew).

## Open Questions
- Can I unzip/extract the workspace zip to a temp directory for deeper inspection?
- Confirm target branch is `feat/crewai-optimize-crew` inside `clean-custom-preview`.
- What specific changes do you want in the updated final summary format?

## Scope Boundaries
- INCLUDE: diagnosing missing quick_review.json or diff_context.json, ensuring final summary consumes outputs.
- EXCLUDE: unrelated workflow changes unless required for output generation.
