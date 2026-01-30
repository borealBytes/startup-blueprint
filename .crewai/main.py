#!/usr/bin/env python3
"""Main orchestrator for CrewAI router-based review system."""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# CRITICAL: Register models BEFORE importing any CrewAI components
# This must happen before CrewAI checks model capabilities during class decoration
from utils.model_config import get_rate_limit_delay, register_models

register_models()

# Configure LiteLLM for rate limit handling
import litellm

# Enable retries for rate limit errors (429)
# OpenRouter free tier: 20 RPM limit
litellm.num_retries = 3  # Retry up to 3 times
litellm.request_timeout = 120  # 2 minute timeout per request

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


def get_workspace_diagnostics():
    """Get current workspace state for debugging.

    Returns:
        dict: Workspace state including files present and their sizes
    """
    try:
        workspace_dir = Path(__file__).parent / "workspace"

        files_info = {}
        if workspace_dir.exists():
            for file_path in workspace_dir.iterdir():
                if file_path.is_file():
                    files_info[file_path.name] = {"size": file_path.stat().st_size, "exists": True}

        return {
            "workspace_path": str(workspace_dir),
            "files": files_info,
            "file_count": len(files_info),
        }
    except Exception as e:
        return {"error": str(e)}


def run_router(env_vars):
    """Run router crew to decide workflows.

    Returns:
        dict: Router decision with workflows, suggestions, and metadata.
              Returns default workflows on failure.
    """
    logger.info("=" * 60)
    logger.info("🔀 STEP 1: Router - Analyzing PR and deciding workflows")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("analyze_pr_and_route")

    try:
        router = RouterCrew()
        result = router.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )

        # Debug: Log raw result
        logger.debug(f"Router result type: {type(result)}")
        logger.debug(f"Router result: {str(result)[:2000]}")

        # Read router decision from workspace
        workspace = WorkspaceTool()
        if workspace.exists("router_decision.json"):
            decision = workspace.read_json("router_decision.json")
            logger.info(f"✅ Router decision: {decision.get('workflows', [])}")
            if decision.get("suggestions"):
                logger.info("💡 Router suggestions:")
                for suggestion in decision["suggestions"]:
                    logger.info(f"  - {suggestion}")

            # Debug: Log decision content
            logger.debug(f"Router decision content: {json.dumps(decision, indent=2)[:1000]}")
            return decision
        else:
            # Enhanced error logging with workspace diagnostics
            workspace_state = get_workspace_diagnostics()
            logger.warning(
                f"⚠️ Router did NOT write router_decision.json\n"
                f"  Agent: RouterCrew router_agent\n"
                f"  Workflow: analyze_pr_and_route\n"
                f"  Expected file: router_decision.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            logger.info("⚠️ Using default workflows due to missing router output")
            return {
                "workflows": ["ci-log-analysis", "quick-review"],
                "suggestions": [],
                "metadata": {},
            }

    except Exception as e:
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Router failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        # Return default workflows on failure
        return {
            "workflows": ["ci-log-analysis", "quick-review"],
            "suggestions": [f"⚠️ Router error: {str(e)}"],
            "metadata": {},
        }


def run_ci_analysis(env_vars):
    """Run CI log analysis crew.

    Returns:
        bool: True if analysis succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("📊 STEP 2: CI Log Analysis - Parsing core-ci results")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("parse_ci_output")

    try:
        ci_crew = CILogAnalysisCrew()
        result = ci_crew.crew().kickoff(inputs={"core_ci_result": env_vars["core_ci_result"]})

        # Debug: Log raw result
        logger.debug(f"CI analysis result type: {type(result)}")
        logger.debug(f"CI analysis result: {str(result)[:2000]}")

        logger.info("✅ CI analysis complete")

        # Validate output file was created
        workspace = WorkspaceTool()
        if not workspace.exists("ci_summary.json"):
            workspace_state = get_workspace_diagnostics()
            logger.warning(
                f"⚠️ CI analysis did NOT write ci_summary.json\n"
                f"  Agent: CILogAnalysisCrew ci_analyst\n"
                f"  Workflow: parse_ci_output\n"
                f"  Expected file: ci_summary.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            workspace.write_json(
                "ci_summary.json",
                {
                    "status": env_vars["core_ci_result"],
                    "passed": env_vars["core_ci_result"] == "success",
                    "summary": f"Core CI: {env_vars['core_ci_result']}",
                    "critical_errors": [],
                    "warnings": [],
                },
            )
            return False
        else:
            # Debug: Log summary content
            summary = workspace.read_json("ci_summary.json")
            logger.debug(f"CI summary content: {json.dumps(summary, indent=2)[:1000]}")
            logger.info("✅ Verified ci_summary.json exists in workspace")
            return True

    except Exception as e:
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ CI analysis failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
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
        return False


def run_quick_review():
    """Run quick review crew.

    Returns:
        bool: True if review succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("⚡ STEP 3: Quick Review - Fast code quality check")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("quick_code_review")

    try:
        quick_crew = QuickReviewCrew()
        result = quick_crew.crew().kickoff()

        # Debug: Log raw result
        logger.debug(f"Quick review result type: {type(result)}")
        logger.debug(f"Quick review result: {str(result)[:2000]}")

        logger.info("✅ Quick review task complete")

        # CRITICAL: Validate output file was created
        workspace = WorkspaceTool()
        if not workspace.exists("quick_review.json"):
            workspace_state = get_workspace_diagnostics()
            logger.error(
                f"❌ CRITICAL: Quick review did NOT write quick_review.json!\n"
                f"  Agent: QuickReviewCrew code_reviewer\n"
                f"  Workflow: quick_code_review\n"
                f"  Expected file: quick_review.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            logger.warning("⚠️ Creating fallback quick_review.json with empty arrays")

            workspace.write_json(
                "quick_review.json",
                {
                    "status": "completed",
                    "summary": "Quick review completed but did not write structured output.",
                    "critical": [],
                    "warnings": [],
                    "info": [],
                },
            )
            return False
        else:
            # Validate the JSON has expected structure and log findings
            review_data = workspace.read_json("quick_review.json")
            total_findings = (
                len(review_data.get("critical", []))
                + len(review_data.get("warnings", []))
                + len(review_data.get("info", []))
            )
            logger.info(
                f"✅ Verified quick_review.json exists with {total_findings} total findings"
            )
            logger.info(f"   - Critical: {len(review_data.get('critical', []))}")
            logger.info(f"   - Warnings: {len(review_data.get('warnings', []))}")
            logger.info(f"   - Info: {len(review_data.get('info', []))}")

            # Debug: Log first few findings
            if review_data.get("critical"):
                logger.debug(
                    f"First critical issue: {json.dumps(review_data['critical'][0], indent=2)}"
                )

            return True

    except Exception as e:
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Quick review failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        workspace = WorkspaceTool()
        workspace.write_json(
            "quick_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Quick review failed",
            },
        )
        return False


def run_full_review(env_vars):
    """Run full technical review crew.

    Returns:
        bool: True if review succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("🔍 STEP 4: Full Technical Review - Deep analysis")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("full_technical_review")

    try:
        full_crew = FullReviewCrew()
        result = full_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )

        # Debug: Log raw result
        logger.debug(f"Full review result type: {type(result)}")
        logger.debug(f"Full review result: {str(result)[:2000]}")

        logger.info("✅ Full review complete")

        # Validate output exists
        workspace = WorkspaceTool()
        if workspace.exists("full_review.json"):
            review_data = workspace.read_json("full_review.json")
            logger.debug(f"Full review data keys: {list(review_data.keys())}")
            return True
        else:
            logger.warning("⚠️ Full review did not write full_review.json")
            return False

    except Exception as e:
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Full review failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        workspace = WorkspaceTool()
        workspace.write_json(
            "full_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Full review failed",
            },
        )
        return False


def run_legal_review():
    """Run legal review crew (stub).

    Returns:
        bool: Always returns True as this is a stub implementation.
    """
    logger.info("=" * 60)
    logger.info("⚖️ STEP 5: Legal Review - Compliance check (STUB)")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("legal_compliance_check")

    try:
        legal_crew = LegalReviewCrew()
        result = legal_crew.kickoff()  # Uses stub implementation

        # Debug: Log raw result
        logger.debug(f"Legal review result type: {type(result)}")
        logger.debug(f"Legal review result: {str(result)[:2000]}")

        logger.info("✅ Legal review complete (stub)")
        return True
    except Exception as e:
        logger.error(f"❌ Legal review failed: {e}", exc_info=True)
        return False


def run_final_summary(env_vars, workflows_executed):
    """Run final summary crew.

    Args:
        env_vars: Environment variables dictionary
        workflows_executed: List of workflows that were executed

    Returns:
        bool: True if summary was created successfully, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("📋 STEP 6: Final Summary - Synthesizing all reviews")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("synthesize_final_summary")

    try:
        # Count the number of reviews/workflows that were executed
        workflow_count = len(workflows_executed)

        summary_crew = FinalSummaryCrew()
        result = summary_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
                "time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                ),  # Changed from timestamp to time
                "count": workflow_count,
                "list": ", ".join(workflows_executed),  # Changed from workflows to list
            }
        )

        # Debug: Log raw result
        logger.debug(f"Final summary result type: {type(result)}")
        logger.debug(f"Final summary result: {str(result)[:2000]}")

        logger.info("✅ Final summary complete")

        # Validate output exists
        workspace = WorkspaceTool()
        if workspace.exists("final_summary.md"):
            summary_content = workspace.read("final_summary.md")
            logger.debug(f"Final summary length: {len(summary_content)} chars")
            return True
        else:
            logger.warning("⚠️ Final summary did not write final_summary.md")
            return False

    except Exception as e:
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Final summary failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        return False


def format_finding_item(finding, severity_emoji):
    """Format a single finding item with proper structure.

    Args:
        finding: Finding dictionary
        severity_emoji: Emoji to use for severity

    Returns:
        str: Formatted markdown for the finding
    """
    if not isinstance(finding, dict):
        return f"- {severity_emoji} {str(finding)}"

    lines = []
    title = finding.get("title", "Unknown issue")
    file_path = finding.get("file", "")
    line_num = finding.get("line", "")
    description = finding.get("description", "")
    fix_suggestion = finding.get("fix_suggestion", "")

    # Title with file location
    if file_path:
        if line_num:
            lines.append(f"- {severity_emoji} **{title}** `{file_path}:{line_num}`")
        else:
            lines.append(f"- {severity_emoji} **{title}** `{file_path}`")
    else:
        lines.append(f"- {severity_emoji} **{title}**")

    # Description (indented)
    if description:
        lines.append(f"  - {description}")

    # Fix suggestion (indented with special icon)
    if fix_suggestion:
        lines.append(f"  - 💡 **Fix**: {fix_suggestion}")

    return "\n".join(lines)


def create_fallback_summary(workspace_dir, env_vars, workflows_executed):
    """Create executive summary from crew JSON outputs.

    Args:
        workspace_dir: Path to workspace directory
        env_vars: Environment variables
        workflows_executed: List of executed workflows
    """
    logger.info("🔧 Creating executive summary from crew outputs...")

    workspace = WorkspaceTool()

    # Collect findings from all crews
    ci_data = workspace.read_json("ci_summary.json") if workspace.exists("ci_summary.json") else {}
    quick_data = (
        workspace.read_json("quick_review.json") if workspace.exists("quick_review.json") else {}
    )
    router_data = (
        workspace.read_json("router_decision.json")
        if workspace.exists("router_decision.json")
        else {}
    )
    full_data = (
        workspace.read_json("full_review.json") if workspace.exists("full_review.json") else {}
    )

    # Count findings
    ci_critical = len(ci_data.get("critical_errors", []))
    ci_warnings = len(ci_data.get("warnings", []))
    quick_critical = len(quick_data.get("critical", []))
    quick_warnings = len(quick_data.get("warnings", []))
    quick_info = len(quick_data.get("info", []))

    total_critical = ci_critical + quick_critical
    total_warnings = ci_warnings + quick_warnings

    # Start building summary
    summary_parts = []
    summary_parts.append("## ⚠️ Review Summary")
    summary_parts.append("")

    # Executive Summary
    summary_parts.append("### 📋 Executive Summary")
    summary_parts.append("")
    if total_critical > 0:
        summary_parts.append(
            f"**Status**: 🔴 **Action Required** - {total_critical} critical issue(s) must be addressed"
        )
    elif total_warnings > 0:
        summary_parts.append(
            f"**Status**: 🟡 **Review Recommended** - {total_warnings} warning(s) found"
        )
    else:
        summary_parts.append("**Status**: ✅ **Looks Good** - No critical issues detected")

    summary_parts.append("")
    summary_parts.append(
        f"**PR**: #{env_vars['pr_number']} | **Commit**: `{env_vars['commit_sha'][:7]}` | **Repository**: {env_vars['repository']}"
    )

    # Build summary line
    summary_line_parts = []
    if ci_data.get("status") == "success":
        summary_line_parts.append("✅ CI passed")
    elif ci_data.get("status"):
        summary_line_parts.append(f"❌ CI {ci_data.get('status')}")

    if total_critical > 0:
        summary_line_parts.append(f"🔴 {total_critical} critical")
    if total_warnings > 0:
        summary_line_parts.append(f"🟡 {total_warnings} warnings")
    if quick_info > 0:
        summary_line_parts.append(f"ℹ️ {quick_info} suggestions")

    if summary_line_parts:
        summary_parts.append(f"**Summary**: {' • '.join(summary_line_parts)}")

    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")

    # CI Analysis - Extract detailed findings
    if workspace.exists("ci_summary.json"):
        try:
            ci_data = workspace.read_json("ci_summary.json")
            summary_parts.append("### ✅ CI Analysis")
            status = ci_data.get("status", "unknown")
            passed = ci_data.get("passed", False)
            status_emoji = "✅" if passed else "❌"
            summary_parts.append(f"**Status**: {status_emoji} {status}")

            # Get what was checked
            checks_performed = ci_data.get("checks_performed", [])
            if checks_performed:
                summary_parts.append(f"**Checks Performed**: {', '.join(checks_performed)}")

            summary_parts.append(f"**Summary**: {ci_data.get('summary', 'No summary available')}")

            # Extract issue analysis if available
            if "issue_analysis" in ci_data:
                analysis = ci_data["issue_analysis"]
                summary_parts.append("")
                summary_parts.append("**Issue Analysis**:")
                if analysis.get("root_cause"):
                    summary_parts.append(f"- **Root Cause**: {analysis['root_cause']}")
                if analysis.get("fix_applied"):
                    summary_parts.append(f"- **Fix Applied**: {analysis['fix_applied']}")
                if analysis.get("recommendation"):
                    summary_parts.append(f"- **Recommendation**: {analysis['recommendation']}")

            # Add critical errors if present
            critical_errors = ci_data.get("critical_errors", [])
            warnings = ci_data.get("warnings", [])

            if critical_errors or warnings:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append("<summary><b>🔍 View CI Issues</b></summary>")
                summary_parts.append("")

                if critical_errors:
                    summary_parts.append("**Critical Errors**:")
                    for idx, error in enumerate(critical_errors, 1):
                        error_type = (
                            error.get("type", "Error") if isinstance(error, dict) else "Error"
                        )
                        error_msg = (
                            error.get("message", str(error))
                            if isinstance(error, dict)
                            else str(error)
                        )
                        summary_parts.append(f"{idx}. **{error_type}**: {error_msg}")
                        if isinstance(error, dict) and error.get("fix_suggestion"):
                            summary_parts.append(f"   - 💡 **Fix**: {error['fix_suggestion']}")
                    summary_parts.append("")

                if warnings:
                    summary_parts.append("**Warnings**:")
                    for idx, warning in enumerate(warnings, 1):
                        warning_msg = (
                            warning.get("message", str(warning))
                            if isinstance(warning, dict)
                            else str(warning)
                        )
                        summary_parts.append(f"{idx}. {warning_msg}")
                    summary_parts.append("")

                summary_parts.append("</details>")

            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse ci_summary.json: {e}")
            summary_parts.append("### ✅ CI Analysis")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        logger.warning("⚠️ ci_summary.json not found in workspace")
        summary_parts.append("### ✅ CI Analysis")
        summary_parts.append("Status: Not available")
        summary_parts.append("")

    # Quick Review - SHOW ALL FINDINGS with collapsible sections
    if workspace.exists("quick_review.json"):
        try:
            quick_data = workspace.read_json("quick_review.json")
            summary_parts.append("### ⚡ Quick Review")
            summary_parts.append(f"**Status**: {quick_data.get('status', 'completed')}")
            summary_parts.append(
                f"**Summary**: {quick_data.get('summary', 'No summary available')}"
            )

            # Get all findings
            critical_issues = quick_data.get("critical", [])
            warnings = quick_data.get("warnings", [])
            suggestions = quick_data.get("info", [])

            # High-level counts
            critical_count = len(critical_issues)
            warning_count = len(warnings)
            info_count = len(suggestions)

            if critical_count > 0 or warning_count > 0 or info_count > 0:
                summary_parts.append("")
                summary_parts.append("**Findings**:")
                if critical_count > 0:
                    summary_parts.append(f"- 🔴 {critical_count} critical issue(s)")
                if warning_count > 0:
                    summary_parts.append(f"- 🟡 {warning_count} warning(s)")
                if info_count > 0:
                    summary_parts.append(f"- 🔵 {info_count} suggestion(s)")

            # CRITICAL ISSUES - always show if present
            if critical_issues:
                summary_parts.append("")
                summary_parts.append("<details open>")
                summary_parts.append(
                    f"<summary><b>🔴 Critical Issues ({critical_count})</b></summary>"
                )
                summary_parts.append("")
                for issue in critical_issues:
                    summary_parts.append(format_finding_item(issue, "🔴"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            # WARNINGS - collapsible
            if warnings:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(f"<summary><b>🟡 Warnings ({warning_count})</b></summary>")
                summary_parts.append("")
                for warning in warnings:
                    summary_parts.append(format_finding_item(warning, "🟡"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            # SUGGESTIONS - collapsible
            if suggestions:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(f"<summary><b>🔵 Suggestions ({info_count})</b></summary>")
                summary_parts.append("")
                for suggestion in suggestions:
                    summary_parts.append(format_finding_item(suggestion, "🔵"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse quick_review.json: {e}")
            summary_parts.append("### ⚡ Quick Review")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        logger.warning("⚠️ quick_review.json not found in workspace")
        summary_parts.append("### ⚡ Quick Review")
        summary_parts.append("Status: Not available")
        summary_parts.append("")

    # Full Review - Extract architectural and security findings
    if workspace.exists("full_review.json"):
        try:
            full_data = workspace.read_json("full_review.json")
            summary_parts.append("### 🔍 Full Technical Review")
            summary_parts.append("")

            # Architecture issues
            arch_issues = full_data.get("architecture", [])
            critical_arch = [i for i in arch_issues if i.get("severity") == "critical"]
            if critical_arch:
                summary_parts.append("**Critical Architecture Issues**:")
                for idx, issue in enumerate(critical_arch[:2], 1):  # Top 2
                    summary_parts.append(f"{idx}. **{issue.get('title', 'Unknown')}**")
                    summary_parts.append(f"   - {issue.get('description', 'No description')}")
                summary_parts.append("")

            # Security vulnerabilities
            security_issues = full_data.get("security", [])
            critical_security = [
                i for i in security_issues if i.get("severity") in ["critical", "high"]
            ]
            if critical_security:
                summary_parts.append("**Security Vulnerabilities**:")
                for idx, issue in enumerate(critical_security[:2], 1):  # Top 2
                    severity_emoji = "🔴" if issue.get("severity") == "critical" else "🟡"
                    summary_parts.append(
                        f"{idx}. {severity_emoji} **{issue.get('title', 'Unknown')}**"
                    )
                    summary_parts.append(f"   - {issue.get('description', 'No description')}")
                summary_parts.append("")

        except Exception as e:
            logger.warning(f"Could not parse full_review.json: {e}")
            summary_parts.append("### 🔍 Full Technical Review")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        if "full-review" in workflows_executed:
            logger.warning("⚠️ full_review.json not found but full-review was executed")
        summary_parts.append("### 🔍 Full Technical Review")
        summary_parts.append("Status: Did not run")
        summary_parts.append("")

    positive_notes = []
    if total_critical == 0:
        positive_notes.append("No critical issues detected")
    if ci_data.get("status") == "success":
        positive_notes.append("All CI checks passed")
    if quick_data.get("merge_status") == "APPROVE":
        positive_notes.append("Code quality review recommends approval")

    if positive_notes:
        summary_parts.append("<details>")
        summary_parts.append(f"<summary><b>✨ What's Good ({len(positive_notes)})</b></summary>")
        summary_parts.append("")
        for note in positive_notes:
            summary_parts.append(f"- ✅ {note}")
        summary_parts.append("")
        summary_parts.append("</details>")
        summary_parts.append("")

    if workspace.exists("router_decision.json"):
        try:
            router_data = workspace.read_json("router_decision.json")
            suggestions = router_data.get("suggestions", [])
            if suggestions:
                summary_parts.append("### 💡 Router Suggestions")
                summary_parts.append("")
                for suggestion in suggestions:
                    summary_parts.append(f"- {suggestion}")
                summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse router_decision.json: {e}")

    summary_parts.append("---")
    summary_parts.append("")
    summary_parts.append(
        f"*🤖 Generated by CrewAI Router System | "
        f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
    )

    fallback_md = "\n".join(summary_parts)
    workspace.write("final_summary.md", fallback_md)
    logger.info(f"✅ Comprehensive fallback summary created ({len(fallback_md)} chars)")
    return fallback_md


def generate_cost_breakdown():
    """Generate markdown table with cost breakdown grouped by crew.

    Returns:
        str: Markdown formatted cost breakdown table with crew subtotals
    """
    try:
        tracker = get_tracker()
        summary = tracker.get_summary()

        if summary["total_calls"] == 0:
            return "\n---\n\n## 💰 Cost Tracking\n\nNo API calls recorded.\n"

        # Use tracker's built-in markdown table formatter
        # It includes crew column, crew subtotals, and grand total
        table = tracker.format_as_markdown_table()

        lines = []
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 💰 Cost Breakdown by Crew")
        lines.append("")
        lines.append(table)
        lines.append("")
        lines.append(
            f"**Summary**: {summary['total_calls']} calls across "
            f"{len(summary['crew_breakdown'])} crews | "
            f"Total: {summary['total_tokens']:,} tokens in {summary['total_duration']:.1f}s | "
            f"Avg: {summary['total_tokens'] / summary['total_duration']:.1f} tok/s"
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
            logger.info("📊 View results in Actions tab for this workflow run")
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
            logger.info("✅ Saved final_summary.md to trace")
            files_copied += 1
        except Exception as e:
            logger.warning(f"⚠️ Could not copy final_summary.md: {e}")
    else:
        logger.warning(f"⚠️ final_summary.md not found at {summary_file}")

    # Copy diff.txt to trace if it exists
    diff_file = workspace_dir / "diff.txt"
    if diff_file.exists():
        try:
            shutil.copy(diff_file, trace_dir / "diff.txt")
            logger.info("✅ Saved diff.txt to trace")
            files_copied += 1
        except Exception as e:
            logger.warning(f"⚠️ Could not copy diff.txt: {e}")

    # Create a trace index file with metadata
    try:
        trace_index = {
            "timestamp": datetime.now().isoformat(),
            "files_copied": files_copied,
            "workspace_files": [f.name for f in workspace_dir.iterdir() if f.is_file()],
        }
        with open(trace_dir / "trace_index.json", "w") as f:
            json.dump(trace_index, f, indent=2)
        logger.info("✅ Created trace index")
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

        # Print per-crew breakdown
        if summary["crew_breakdown"]:
            logger.info("")
            logger.info("By Crew:")
            for crew_name in sorted(summary["crew_breakdown"].keys()):
                stats = summary["crew_breakdown"][crew_name]
                logger.info(
                    f"  • {crew_name}: {stats['calls']} calls, "
                    f"${stats['cost']:.4f} ({stats['total_tokens']:,} tokens)"
                )

    except Exception as e:
        logger.warning(f"⚠️ Could not generate cost summary: {e}")


def main():
    """Main orchestration function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("🚀 CrewAI Router-Based Review System Starting")
    logger.info("=" * 60)

    try:
        # Setup
        workspace_dir = setup_workspace()
        env_vars = get_env_vars()

        # Track which workflows were executed and their success status
        workflows_executed = []
        workflow_success = {}  # Track which workflows succeeded

        # STEP 1: Router decides workflows
        decision = run_router(env_vars)
        workflows = decision.get("workflows", ["ci-log-analysis", "quick-review"])

        # Rate limit delay: centralized in MODEL_REGISTRY (0s for paid, 10s for free)
        rate_limit_delay = get_rate_limit_delay()

        # STEP 2: Always run CI analysis (default)
        if "ci-log-analysis" in workflows:
            success = run_ci_analysis(env_vars)
            workflows_executed.append("ci-log-analysis")
            workflow_success["ci-log-analysis"] = success
            if not success:
                logger.warning("⚠️ CI analysis had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)

        # STEP 3: Always run quick review (default)
        if "quick-review" in workflows:
            success = run_quick_review()
            workflows_executed.append("quick-review")
            workflow_success["quick-review"] = success
            if not success:
                logger.warning("⚠️ Quick review had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)

        # STEP 4: Conditional - Full review
        if "full-review" in workflows:
            success = run_full_review(env_vars)
            workflows_executed.append("full-review")
            workflow_success["full-review"] = success
            if not success:
                logger.warning("⚠️ Full review had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)
        else:
            logger.info("⏩ Skipping full review (no crewai:full-review label)")

        # STEP 5: Conditional - Legal review (stub)
        if "legal-review" in workflows:
            success = run_legal_review()
            workflows_executed.append("legal-review")
            workflow_success["legal-review"] = success
            if not success:
                logger.warning("⚠️ Legal review had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)
        else:
            logger.info("⏩ Skipping legal review (no crewai:legal label)")

        # STEP 6: Final summary (always run) - pass workflow count
        summary_success = run_final_summary(env_vars, workflows_executed)
        if not summary_success:
            logger.warning("⚠️ Final summary had issues, will use fallback...")

        # Read final markdown from workspace with validation
        workspace = WorkspaceTool()

        # Debug: List all files in workspace
        logger.info("📂 Workspace files:")
        for f in workspace_dir.iterdir():
            if f.is_file():
                logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

        # Try to read final_summary.md
        if workspace.exists("final_summary.md"):
            final_markdown = workspace.read("final_summary.md")
            logger.info(f"✅ Read final_summary.md ({len(final_markdown)} chars)")

            # CRITICAL VALIDATION: If summary is too short, it's likely just skeleton
            # A proper summary with actual content should be at least 1000 chars
            if len(final_markdown) < 1000:
                logger.warning(
                    f"⚠️ Final summary is too short ({len(final_markdown)} chars) - "
                    "likely incomplete"
                )
                logger.info("🔄 Replacing with comprehensive fallback summary")
                final_markdown = create_fallback_summary(
                    workspace_dir, env_vars, workflows_executed
                )
            else:
                logger.info("✅ Final summary has sufficient content")
        else:
            logger.warning("⚠️ final_summary.md not found - creating comprehensive fallback")
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

        # Log workflow success summary
        logger.info("=" * 60)
        logger.info("📊 Workflow Execution Summary")
        logger.info("=" * 60)
        for workflow, success in workflow_success.items():
            status = "✅ SUCCESS" if success else "⚠️ HAD ISSUES"
            logger.info(f"{workflow}: {status}")

        logger.info("=" * 60)
        logger.info("✅ CrewAI Review Complete!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Review failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
