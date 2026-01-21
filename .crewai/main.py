#!/usr/bin/env python3
"""Main orchestrator for CrewAI router-based review system."""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from crews.ci_log_analysis_crew import CILogAnalysisCrew
from crews.final_summary_crew import FinalSummaryCrew
from crews.full_review_crew import FullReviewCrew
from crews.legal_review_crew import LegalReviewCrew
from crews.quick_review_crew import QuickReviewCrew
from crews.router_crew import RouterCrew
from tools.cost_tracker import get_tracker
from tools.workspace_tool import WorkspaceTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Disable CrewAI tracing to prevent interactive prompts in CI
os.environ["CREWAI_TRACING_ENABLED"] = "false"


def setup_workspace():
    """Setup workspace directories.

    Uses absolute path based on this file's location to avoid CWD issues
    when workflow sets working-directory.
    """
    # Use absolute path: this file is in .crewai/, so workspace is .crewai/workspace
    workspace_dir = (Path(__file__).parent / "workspace").resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "trace").mkdir(exist_ok=True)
    logger.info(f"📁 Workspace initialized: {workspace_dir}")
    return workspace_dir


def get_env_vars():
    """Get required environment variables."""
    env_vars = {
        "pr_number": os.getenv("PR_NUMBER"),
        "commit_sha": os.getenv("COMMIT_SHA"),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "core_ci_result": os.getenv("CORE_CI_RESULT", "success"),
    }

    # Validate required vars
    if not env_vars["pr_number"]:
        logger.warning("PR_NUMBER not set - using mock mode")
        env_vars["pr_number"] = "999"

    if not env_vars["commit_sha"]:
        logger.warning("COMMIT_SHA not set - using mock mode")
        env_vars["commit_sha"] = "mock-sha"

    if not env_vars["repository"]:
        logger.warning("GITHUB_REPOSITORY not set - using mock mode")
        env_vars["repository"] = "owner/repo"

    logger.info(f"🎯 Environment: PR #{env_vars['pr_number']}, SHA {env_vars['commit_sha'][:7]}")
    logger.info(f"🎯 Repository: {env_vars['repository']}")
    logger.info(f"🎯 Core CI Result: {env_vars['core_ci_result']}")

    return env_vars


def run_router(env_vars):
    """Run router crew to decide workflows."""
    logger.info("=" * 60)
    logger.info("🔀 STEP 1: Router - Analyzing PR and deciding workflows")
    logger.info("=" * 60)

    try:
        router = RouterCrew()
        result = router.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )

        # Read router decision from workspace
        workspace = WorkspaceTool()
        if workspace.exists("router_decision.json"):
            decision = workspace.read_json("router_decision.json")
            logger.info(f"✅ Router decision: {decision.get('workflows', [])}")
            if decision.get("suggestions"):
                logger.info("💡 Router suggestions:")
                for suggestion in decision["suggestions"]:
                    logger.info(f"  - {suggestion}")
            return decision
        else:
            logger.warning("⚠️ Router decision not found in workspace - using defaults")
            return {
                "workflows": ["ci-log-analysis", "quick-review"],
                "suggestions": [],
                "metadata": {},
            }

    except Exception as e:
        logger.error(f"❌ Router failed: {e}", exc_info=True)
        # Return default workflows on failure
        return {
            "workflows": ["ci-log-analysis", "quick-review"],
            "suggestions": [f"⚠️ Router error: {str(e)}"],
            "metadata": {},
        }


def run_ci_analysis(env_vars):
    """Run CI log analysis crew."""
    logger.info("=" * 60)
    logger.info("📊 STEP 2: CI Log Analysis - Parsing core-ci results")
    logger.info("=" * 60)

    try:
        ci_crew = CILogAnalysisCrew()
        result = ci_crew.crew().kickoff(inputs={"core_ci_result": env_vars["core_ci_result"]})
        logger.info("✅ CI analysis complete")
        return result
    except Exception as e:
        logger.error(f"❌ CI analysis failed: {e}", exc_info=True)
        # Write error to workspace
        workspace = WorkspaceTool()
        workspace.write_json(
            "ci_summary.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "CI analysis failed",
            },
        )


def run_quick_review():
    """Run quick review crew."""
    logger.info("=" * 60)
    logger.info("⚡ STEP 3: Quick Review - Fast code quality check")
    logger.info("=" * 60)

    try:
        quick_crew = QuickReviewCrew()
        result = quick_crew.crew().kickoff()
        logger.info("✅ Quick review complete")
        return result
    except Exception as e:
        logger.error(f"❌ Quick review failed: {e}", exc_info=True)
        workspace = WorkspaceTool()
        workspace.write_json(
            "quick_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Quick review failed",
            },
        )


def run_full_review(env_vars):
    """Run full technical review crew."""
    logger.info("=" * 60)
    logger.info("🔍 STEP 4: Full Technical Review - Deep analysis")
    logger.info("=" * 60)

    try:
        full_crew = FullReviewCrew()
        result = full_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )
        logger.info("✅ Full review complete")
        return result
    except Exception as e:
        logger.error(f"❌ Full review failed: {e}", exc_info=True)
        workspace = WorkspaceTool()
        workspace.write_json(
            "full_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Full review failed",
            },
        )


def run_legal_review():
    """Run legal review crew (stub)."""
    logger.info("=" * 60)
    logger.info("⚖️ STEP 5: Legal Review - Compliance check (STUB)")
    logger.info("=" * 60)

    try:
        legal_crew = LegalReviewCrew()
        result = legal_crew.kickoff()  # Uses stub implementation
        logger.info("✅ Legal review complete (stub)")
        return result
    except Exception as e:
        logger.error(f"❌ Legal review failed: {e}", exc_info=True)


def run_final_summary(env_vars, workflows_executed):
    """Run final summary crew.

    Args:
        env_vars: Environment variables dictionary
        workflows_executed: List of workflows that were executed
    """
    logger.info("=" * 60)
    logger.info("📝 STEP 6: Final Summary - Synthesizing all reviews")
    logger.info("=" * 60)

    try:
        # Count the number of reviews/workflows that were executed
        workflow_count = len(workflows_executed)

        summary_crew = FinalSummaryCrew()
        result = summary_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "count": workflow_count,  # Add count parameter to fix template variable error
            }
        )
        logger.info("✅ Final summary complete")
        return result
    except Exception as e:
        logger.error(f"❌ Final summary failed: {e}", exc_info=True)
        return None


def create_fallback_summary(workspace_dir, env_vars, workflows_executed):
    """Create a fallback summary if the agent didn't create one.

    Args:
        workspace_dir: Path to workspace directory
        env_vars: Environment variables
        workflows_executed: List of executed workflows
    """
    logger.info("🔧 Creating fallback summary...")

    workspace = WorkspaceTool()

    # Collect what we can from workspace
    summary_parts = []
    summary_parts.append(f"## ⚠️ Review Summary")
    summary_parts.append("")
    summary_parts.append(
        f"Review completed with warnings. Some workflows may have encountered issues."
    )
    summary_parts.append("")
    summary_parts.append(f"**PR**: #{env_vars['pr_number']}")
    summary_parts.append(f"**Commit**: `{env_vars['commit_sha'][:7]}`")
    summary_parts.append(f"**Repository**: {env_vars['repository']}")
    summary_parts.append(f"**Workflows Executed**: {', '.join(workflows_executed)}")
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")

    # CI Analysis - Extract detailed findings
    if workspace.exists("ci_summary.json"):
        try:
            ci_data = workspace.read_json("ci_summary.json")
            summary_parts.append("### ✅ CI Analysis")
            summary_parts.append(f"**Status**: {ci_data.get('status', 'unknown')}")
            
            # Add critical errors if present
            critical_errors = ci_data.get('critical_errors', [])
            if critical_errors:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append("<summary>🔴 Critical Errors</summary>")
                summary_parts.append("")
                for error in critical_errors[:3]:  # Top 3 errors
                    summary_parts.append(f"**{error.get('type', 'Error')}**: {error.get('message', 'No details')}")
                    if error.get('fix_suggestion'):
                        summary_parts.append(f"  - 💡 **Fix**: {error['fix_suggestion']}")
                    summary_parts.append("")
                summary_parts.append("</details>")
            
            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse ci_summary.json: {e}")
            summary_parts.append("### ✅ CI Analysis")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")

    # Quick Review
    if workspace.exists("quick_review.json"):
        try:
            quick_data = workspace.read_json("quick_review.json")
            summary_parts.append("### ⚡ Quick Review")
            summary_parts.append(f"**Status**: {quick_data.get('status', 'unknown')}")
            
            # Add key findings if present
            if quick_data.get('issues'):
                issues = quick_data['issues']
                critical_count = len([i for i in issues if i.get('severity') == 'critical'])
                if critical_count > 0:
                    summary_parts.append(f"  - 🔴 {critical_count} critical issues found")
            
            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse quick_review.json: {e}")
            summary_parts.append("### ⚡ Quick Review")
            summary_parts.append("Status: Did not run")
            summary_parts.append("")

    # Full Review - Extract architectural and security findings
    if workspace.exists("full_review.json"):
        try:
            full_data = workspace.read_json("full_review.json")
            summary_parts.append("### 🔍 Full Technical Review")
            summary_parts.append("")
            
            # Architecture issues
            arch_issues = full_data.get('architecture', [])
            critical_arch = [i for i in arch_issues if i.get('severity') == 'critical']
            if critical_arch:
                summary_parts.append("<details>")
                summary_parts.append("<summary>🏗️ Critical Architecture Issues</summary>")
                summary_parts.append("")
                for issue in critical_arch[:3]:  # Top 3
                    summary_parts.append(f"**{issue.get('title', 'Unknown')}**")
                    summary_parts.append(f"  - {issue.get('description', 'No description')}")
                    if issue.get('suggestion'):
                        summary_parts.append(f"  - 💡 **Suggestion**: {issue['suggestion']}")
                    summary_parts.append("")
                summary_parts.append("</details>")
                summary_parts.append("")
            
            # Security vulnerabilities
            security_issues = full_data.get('security', [])
            critical_security = [i for i in security_issues if i.get('severity') in ['critical', 'high']]
            if critical_security:
                summary_parts.append("<details>")
                summary_parts.append("<summary>🔒 Security Vulnerabilities</summary>")
                summary_parts.append("")
                for issue in critical_security[:3]:  # Top 3
                    severity_emoji = "🔴" if issue.get('severity') == 'critical' else "🟡"
                    summary_parts.append(f"{severity_emoji} **{issue.get('title', 'Unknown')}**")
                    summary_parts.append(f"  - {issue.get('description', 'No description')}")
                    summary_parts.append("")
                summary_parts.append("</details>")
                summary_parts.append("")
            
            # Testing issues
            testing_issues = full_data.get('testing', [])
            critical_testing = [i for i in testing_issues if i.get('severity') == 'critical']
            if critical_testing:
                summary_parts.append("<details>")
                summary_parts.append("<summary>🧪 Testing Issues</summary>")
                summary_parts.append("")
                for issue in critical_testing[:2]:  # Top 2
                    summary_parts.append(f"**{issue.get('title', 'Unknown')}**")
                    summary_parts.append(f"  - {issue.get('description', 'No description')}")
                    summary_parts.append("")
                summary_parts.append("</details>")
                summary_parts.append("")
            
        except Exception as e:
            logger.warning(f"Could not parse full_review.json: {e}")
            summary_parts.append("### 🔍 Full Technical Review")
            summary_parts.append("Status: Did not run")
            summary_parts.append("")

    # Security Review (if available)
    if workspace.exists("security_review.json"):
        try:
            security_data = workspace.read_json("security_review.json")
            critical_vulns = security_data.get('critical_vulnerabilities', [])
            if critical_vulns:
                summary_parts.append("### 🔒 Security Scan")
                summary_parts.append(f"**Critical Vulnerabilities**: {len(critical_vulns)}")
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append("<summary>View Details</summary>")
                summary_parts.append("")
                for vuln in critical_vulns[:3]:  # Top 3
                    summary_parts.append(f"**{vuln.get('title', 'Unknown')}**")
                    summary_parts.append(f"  - **Category**: {vuln.get('category', 'N/A')}")
                    summary_parts.append(f"  - {vuln.get('description', 'No description')}")
                    if vuln.get('remediation'):
                        summary_parts.append(f"  - 💡 **Fix**: {vuln['remediation']}")
                    summary_parts.append("")
                summary_parts.append("</details>")
                summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse security_review.json: {e}")

    summary_parts.append("---")
    summary_parts.append("")
    summary_parts.append(
        f"*🤖 Generated by CrewAI Router System | ⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
    )

    fallback_md = "\n".join(summary_parts)
    workspace.write("final_summary.md", fallback_md)
    logger.info(f"✅ Fallback summary created ({len(fallback_md)} chars)")
    return fallback_md


def generate_cost_breakdown():
    """Generate markdown table with cost breakdown.

    Returns:
        str: Markdown formatted cost breakdown table
    """
    try:
        tracker = get_tracker()
        summary = tracker.get_summary()
        calls = tracker.calls

        if summary["total_calls"] == 0:
            return "\n---\n\n## 💰 Cost Tracking\n\nNo API calls recorded.\n"

        # Build markdown table
        lines = []
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 💰 Cost Breakdown")
        lines.append("")
        lines.append("| Call | Model | Input | Output | Cost | Speed |")
        lines.append("|------|-------|-------|--------|------|-------|")

        # CRITICAL: Access dataclass attributes with dot notation, not subscripts
        for i, call in enumerate(calls, 1):
            model_short = call.model.split("/")[-1]  # Last part of model name
            input_tokens = f"{call.tokens_in:,}"
            output_tokens = f"{call.tokens_out:,}"
            cost = f"${call.cost:.6f}"

            # Calculate speed (tokens/sec)
            if call.duration_seconds > 0:
                speed = (call.tokens_in + call.tokens_out) / call.duration_seconds
                speed_str = f"{speed:.1f} tok/s"
            else:
                speed_str = "N/A"

            lines.append(
                f"| #{i} | {model_short} | {input_tokens} | {output_tokens} | {cost} | {speed_str} |"
            )

        # Add totals row
        lines.append(
            f"| **TOTAL** | **{summary['total_calls']} calls** | **{summary['total_tokens_in']:,}** | **{summary['total_tokens_out']:,}** | **${summary['total_cost']:.6f}** | **{summary['total_duration']:.1f}s** |"
        )

        lines.append("")
        lines.append(
            f"**Total Tokens**: {summary['total_tokens']:,} | **Avg Speed**: {summary['total_tokens']/summary['total_duration']:.1f} tok/s"
        )
        lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"⚠️ Could not generate cost breakdown: {e}")
        return "\n---\n\n## 💰 Cost Breakdown\n\nCost tracking unavailable.\n"


def post_results(env_vars, final_markdown):
    """Post results to GitHub Actions summary."""
    logger.info("=" * 60)
    logger.info("📤 STEP 7: Posting Results to GitHub Actions")
    logger.info("=" * 60)

    # Post to GitHub Actions summary (ONLY output location)
    step_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        try:
            with open(step_summary_file, "a") as f:
                f.write(final_markdown)
                f.write("\n")
            logger.info("✅ Posted to GitHub Actions summary")
            logger.info(f"📊 View results in Actions tab for this workflow run")
        except Exception as e:
            logger.error(f"❌ Failed to write to step summary: {e}")
    else:
        logger.warning("⚠️ GITHUB_STEP_SUMMARY not set - skipping Actions summary")
        logger.info("ℹ️ In local testing mode, review saved to workspace/final_summary.md")


def save_trace(workspace_dir):
    """Save execution trace for artifacts."""
    logger.info("=" * 60)
    logger.info("💾 STEP 8: Saving Execution Trace")
    logger.info("=" * 60)

    trace_dir = workspace_dir / "trace"
    import shutil

    files_copied = 0

    # Copy all workspace JSON files to trace
    for json_file in workspace_dir.glob("*.json"):
        try:
            shutil.copy(json_file, trace_dir / json_file.name)
            logger.info(f"✅ Saved {json_file.name} to trace")
            files_copied += 1
        except Exception as e:
            logger.warning(f"⚠️ Could not copy {json_file.name}: {e}")

    # Copy final_summary.md to trace (this is the key file)
    summary_file = workspace_dir / "final_summary.md"
    if summary_file.exists():
        try:
            shutil.copy(summary_file, trace_dir / "final_summary.md")
            logger.info(f"✅ Saved final_summary.md to trace")
            files_copied += 1
        except Exception as e:
            logger.warning(f"⚠️ Could not copy final_summary.md: {e}")
    else:
        logger.warning(f"⚠️ final_summary.md not found at {summary_file}")

    # Create a trace index file with metadata
    try:
        trace_index = {
            "timestamp": datetime.now().isoformat(),
            "files_copied": files_copied,
            "workspace_files": [f.name for f in workspace_dir.iterdir() if f.is_file()],
        }
        with open(trace_dir / "trace_index.json", "w") as f:
            json.dump(trace_index, f, indent=2)
        logger.info(f"✅ Created trace index")
        files_copied += 1
    except Exception as e:
        logger.warning(f"⚠️ Could not create trace index: {e}")

    logger.info(f"📊 Trace saved to {trace_dir} ({files_copied} files)")


def print_cost_summary():
    """Print cost tracking summary to console."""
    logger.info("=" * 60)
    logger.info("💰 Cost Summary")
    logger.info("=" * 60)

    try:
        tracker = get_tracker()
        summary = tracker.get_summary()

        logger.info(f"Total API Calls: {summary['total_calls']}")
        logger.info(f"Total Tokens: {summary['total_tokens']:,}")
        logger.info(f"  - Input: {summary['total_tokens_in']:,}")
        logger.info(f"  - Output: {summary['total_tokens_out']:,}")
        logger.info(f"Total Cost: ${summary['total_cost']:.4f}")
        logger.info(f"Total Duration: {summary['total_duration']:.2f}s")

    except Exception as e:
        logger.warning(f"⚠️ Could not generate cost summary: {e}")


def main():
    """Main orchestration function."""
    logger.info("🚀 CrewAI Router-Based Review System Starting")
    logger.info("=" * 60)

    try:
        # Setup
        workspace_dir = setup_workspace()
        env_vars = get_env_vars()

        # Track which workflows were executed
        workflows_executed = []

        # STEP 1: Router decides workflows
        decision = run_router(env_vars)
        workflows = decision.get("workflows", ["ci-log-analysis", "quick-review"])

        # STEP 2: Always run CI analysis (default)
        if "ci-log-analysis" in workflows:
            run_ci_analysis(env_vars)
            workflows_executed.append("ci-log-analysis")

        # STEP 3: Always run quick review (default)
        if "quick-review" in workflows:
            run_quick_review()
            workflows_executed.append("quick-review")

        # STEP 4: Conditional - Full review
        if "full-review" in workflows:
            run_full_review(env_vars)
            workflows_executed.append("full-review")
        else:
            logger.info("⏩ Skipping full review (no crewai:full-review label)")

        # STEP 5: Conditional - Legal review (stub)
        if "legal-review" in workflows:
            run_legal_review()
            workflows_executed.append("legal-review")
        else:
            logger.info("⏩ Skipping legal review (no crewai:legal label)")

        # STEP 6: Final summary (always run) - pass workflow count
        final_result = run_final_summary(env_vars, workflows_executed)

        # Read final markdown from workspace with fallback
        workspace = WorkspaceTool()

        # Debug: List all files in workspace
        logger.info("📂 Workspace files:")
        for f in workspace_dir.iterdir():
            if f.is_file():
                logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

        # Try to read final_summary.md, create fallback if missing
        if workspace.exists("final_summary.md"):
            final_markdown = workspace.read("final_summary.md")
            logger.info(f"✅ Read final_summary.md ({len(final_markdown)} chars)")
        else:
            logger.warning("⚠️ final_summary.md not found - creating fallback")
            final_markdown = create_fallback_summary(workspace_dir, env_vars, workflows_executed)

        # CRITICAL: Wait for async cost tracking callbacks to fire
        logger.info("⏳ Waiting for cost tracking callbacks to complete...")
        time.sleep(2)  # Give async callbacks time to register

        # Generate cost breakdown and append to summary
        cost_breakdown = generate_cost_breakdown()
        final_markdown_with_cost = final_markdown + cost_breakdown

        # STEP 7: Post results to GitHub Actions summary (with cost table)
        post_results(env_vars, final_markdown_with_cost)

        # STEP 8: Save trace
        save_trace(workspace_dir)

        # Print cost summary to console
        print_cost_summary()

        logger.info("=" * 60)
        logger.info("✅ CrewAI Review Complete!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Review failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
