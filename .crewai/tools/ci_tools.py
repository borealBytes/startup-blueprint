"""Tools for analyzing CI/CD job results with intelligent log handling."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Get workspace directory relative to this file
WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"
CI_RESULTS_DIR = WORKSPACE_DIR / "ci_results"

# Log size thresholds (in KB)
SMALL_LOG_THRESHOLD = 50  # < 50KB = small, read fully
MEDIUM_LOG_THRESHOLD = 200  # < 200KB = medium, use caution
# > 200KB = large, must grep/search


class ReadJobIndexInput(BaseModel):
    """Input schema for ReadJobIndexTool."""

    dummy: str = Field(
        default="",
        description="No input required. Just call this tool to read the job index.",
    )


class ReadJobIndexTool(BaseTool):
    """Read the index of all CI jobs that ran before CrewAI review."""

    name: str = "Read CI Job Index"
    description: str = (
        "Read the index of all CI jobs that ran before CrewAI review. "
        "Returns a summary with job names, statuses, and log sizes. "
        "Use this FIRST to understand which jobs ran and their outcomes. "
        "No input required."
    )
    args_schema: type[BaseModel] = ReadJobIndexInput

    def _run(self, dummy: str = "") -> str:
        """Read the job index."""
        index_file = CI_RESULTS_DIR / "_job_index.json"
        if not index_file.exists():
            return "No CI job index found. CI data may not have been collected."

        with open(index_file) as f:
            data = json.load(f)

        result = "# CI Job Index\n\n"
        result += f"**Workflow Run:** {data.get('run_id', 'N/A')} "
        result += f"(#{data.get('run_number', 'N/A')})\n\n"
        result += f"## Jobs ({len(data['jobs'])} completed)\n\n"

        for job in data["jobs"]:
            conclusion = job.get("conclusion", "unknown")
            if conclusion == "success":
                status_emoji = "SUCCESS"
            elif conclusion == "failure":
                status_emoji = "FAILED"
            else:
                status_emoji = "WARNING"

            log_size_kb = job.get("log_size_bytes", 0) / 1024
            if log_size_kb < SMALL_LOG_THRESHOLD:
                size_note = f"{log_size_kb:.1f}KB (small - safe to read)"
            elif log_size_kb < MEDIUM_LOG_THRESHOLD:
                size_note = f"{log_size_kb:.1f}KB (medium - read with caution)"
            else:
                size_note = f"{log_size_kb:.1f}KB (LARGE - use grep/search)"

            result += f"[{status_emoji}] **{job['job_name']}** ({conclusion})\n"
            result += f"   - Folder: `{job['job_folder']}`\n"
            result += f"   - Log size: {size_note}\n"
            result += f"   - Timestamp: {job.get('timestamp', 'N/A')}\n\n"

        return result


class FolderNameInput(BaseModel):
    """Input schema for tools that take a folder name."""

    folder_name: str = Field(
        description="The folder name from the job index (e.g., 'core-ci', 'test-crewai')"
    )


class CheckLogSizeTool(BaseTool):
    """Check the size of a job's log before reading it."""

    name: str = "Check Log Size"
    description: str = (
        "Check the size of a job's log before reading it. "
        "Returns log size and recommendation on how to read it. "
        "Use this before reading large logs to decide if you need to grep/search instead."
    )
    args_schema: type[BaseModel] = FolderNameInput

    def _run(self, folder_name: str) -> str:
        """Check log size."""
        log_file = CI_RESULTS_DIR / folder_name / "log.txt"

        if not log_file.exists():
            return f"No log found for job '{folder_name}'"

        size_bytes = log_file.stat().st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024

        lines = sum(1 for _ in open(log_file))

        result = f"# Log Size for {folder_name}\n\n"
        result += f"**Size:** {size_bytes:,} bytes ({size_kb:.1f}KB / {size_mb:.2f}MB)\n"
        result += f"**Lines:** {lines:,}\n\n"

        if size_kb < SMALL_LOG_THRESHOLD:
            result += "**Recommendation:** SAFE TO READ FULLY\n"
            result += "This log is small enough to read completely using Read Full Log tool."
        elif size_kb < MEDIUM_LOG_THRESHOLD:
            result += "**Recommendation:** READ WITH CAUTION\n"
            result += (
                "Consider reading the summary first, then use Search Log to find specific errors."
            )
        else:
            result += "**Recommendation:** DO NOT READ FULLY\n"
            result += f"This log is too large ({size_mb:.2f}MB). "
            result += "Use Search Log tool to find specific patterns.\n"
            result += "Common searches: 'error', 'failed', 'FAILED', 'exception', 'traceback'"

        return result


class ReadJobSummaryTool(BaseTool):
    """Read the GitHub Actions summary for a specific job."""

    name: str = "Read Job Summary"
    description: str = (
        "Read the GitHub Actions summary for a specific job. "
        "Returns the job's summary showing step-by-step results. "
        "ALWAYS read summaries before logs. Summaries tell you WHAT failed."
    )
    args_schema: type[BaseModel] = FolderNameInput

    def _run(self, folder_name: str) -> str:
        """Read job summary."""
        summary_file = CI_RESULTS_DIR / folder_name / "summary.md"

        if not summary_file.exists():
            return f"No summary found for job '{folder_name}'"

        with open(summary_file) as f:
            return f.read()


class SearchLogInput(BaseModel):
    """Input schema for SearchLogTool."""

    folder_name: str = Field(description="The folder name from the job index (e.g., 'core-ci')")
    pattern: str = Field(
        description=(
            "Search pattern (regex supported). "
            "Good patterns: 'error', 'failed', 'exception'"
        )
    )
    context_lines: int = Field(
        default=3,
        description="Number of lines before/after match to include (default: 3)",
    )
    max_matches: int = Field(
        default=50, description="Maximum number of matches to return (default: 50)"
    )


class SearchLogTool(BaseTool):
    """Search a job's log for a specific pattern."""

    name: str = "Search Log for Pattern"
    description: str = (
        "Search a job's log for a specific pattern (case-insensitive grep). "
        "Returns matching lines with context. "
        "Use this for LARGE logs instead of reading the entire file. "
        "Good patterns: 'error', 'failed', 'exception', 'FAIL', specific test names"
    )
    args_schema: type[BaseModel] = SearchLogInput

    def _run(
        self,
        folder_name: str,
        pattern: str,
        context_lines: int = 3,
        max_matches: int = 50,
    ) -> str:
        """Search log for pattern."""
        log_file = CI_RESULTS_DIR / folder_name / "log.txt"

        if not log_file.exists():
            return f"No log found for job '{folder_name}'"

        try:
            pattern_re = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"Invalid regex pattern: {e}"

        matches = []
        with open(log_file) as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if pattern_re.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)

                context = {
                    "line_number": i + 1,
                    "match": line.strip(),
                    "context": "".join(lines[start:end]),
                }
                matches.append(context)

                if len(matches) >= max_matches:
                    break

        if not matches:
            return f"No matches found for pattern '{pattern}' in {folder_name} log"

        result = f"# Search Results for '{pattern}' in {folder_name}\n\n"
        result += f"**Found {len(matches)} matches** (showing up to {max_matches})\n\n"

        for i, match in enumerate(matches, 1):
            result += f"## Match {i} (Line {match['line_number']})\n"
            result += f"```\n{match['context']}```\n\n"

        if len(matches) == max_matches:
            result += f"\nReached maximum of {max_matches} matches. "
            result += "Pattern may occur more times.\n"

        return result


class ReadFullLogInput(BaseModel):
    """Input schema for ReadFullLogTool."""

    folder_name: str = Field(description="The folder name from the job index (e.g., 'core-ci')")
    max_lines: Optional[int] = Field(
        default=None,
        description="Optional limit on number of lines to return (for safety)",
    )


class ReadFullLogTool(BaseTool):
    """Read the complete log output for a specific job."""

    name: str = "Read Full Log"
    description: str = (
        "Read the complete log output for a specific job. "
        "WARNING: Check log size first! Use Check Log Size tool before calling this. "
        "For large logs, use Search Log tool instead."
    )
    args_schema: type[BaseModel] = ReadFullLogInput

    def _run(self, folder_name: str, max_lines: Optional[int] = None) -> str:
        """Read full log."""
        log_file = CI_RESULTS_DIR / folder_name / "log.txt"

        if not log_file.exists():
            return f"No log found for job '{folder_name}'"

        size_kb = log_file.stat().st_size / 1024

        # Safety check
        if size_kb > MEDIUM_LOG_THRESHOLD and max_lines is None:
            return (
                f"ERROR: Log is {size_kb:.1f}KB - too large to read without limit!\n\n"
                f"Use Check Log Size tool first, then either:\n"
                f"1. Use Search Log tool to find specific errors\n"
                f"2. Call this again with max_lines parameter (e.g., 500)"
            )

        with open(log_file) as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                content = "".join(lines)
                truncated = True
            else:
                content = f.read()
                truncated = False

        result = f"# Full Log: {folder_name}\n\n"

        if truncated:
            result += f"**Truncated to {max_lines} lines** (log is {size_kb:.1f}KB)\n\n"
        else:
            result += f"**Size:** {size_kb:.1f}KB\n\n"

        result += "```\n" + content + "\n```"

        if truncated:
            result += "\n\nLog truncated. Use Search Log tool to find specific patterns."

        return result


class GetLogStatsTool(BaseTool):
    """Get statistics about a job log."""

    name: str = "Get Log Statistics"
    description: str = (
        "Get statistics about a job log (error counts, warnings, etc.). "
        "Use this to quickly assess log content without reading the whole file."
    )
    args_schema: type[BaseModel] = FolderNameInput

    def _run(self, folder_name: str) -> str:
        """Get log statistics."""
        log_file = CI_RESULTS_DIR / folder_name / "log.txt"

        if not log_file.exists():
            return f"No log found for job '{folder_name}'"

        error_count = 0
        warning_count = 0
        failed_count = 0
        exception_count = 0
        total_lines = 0

        patterns = {
            "error": re.compile(r"\berror\b", re.IGNORECASE),
            "warning": re.compile(r"\bwarning\b", re.IGNORECASE),
            "failed": re.compile(r"\bfailed\b", re.IGNORECASE),
            "exception": re.compile(r"\bexception\b", re.IGNORECASE),
        }

        with open(log_file) as f:
            for line in f:
                total_lines += 1

                if patterns["error"].search(line):
                    error_count += 1
                if patterns["warning"].search(line):
                    warning_count += 1
                if patterns["failed"].search(line):
                    failed_count += 1
                if patterns["exception"].search(line):
                    exception_count += 1

        size_kb = log_file.stat().st_size / 1024

        result = f"# Log Statistics: {folder_name}\n\n"
        result += f"**Total lines:** {total_lines:,}\n"
        result += f"**File size:** {size_kb:.1f}KB\n\n"
        result += "## Pattern Counts\n\n"
        result += f"- **Errors:** {error_count}\n"
        result += f"- **Warnings:** {warning_count}\n"
        result += f"- **Failed:** {failed_count}\n"
        result += f"- **Exceptions:** {exception_count}\n\n"

        if error_count > 0 or failed_count > 0 or exception_count > 0:
            result += "**Recommendation:** This log contains errors/failures. "
            result += "Use Search Log tool with pattern 'error' to investigate.\n"
        elif warning_count > 0:
            result += "**Recommendation:** Log has warnings but may have passed. "
            result += "Check summary first.\n"
        else:
            result += "**Recommendation:** Log appears clean. Review summary for details.\n"

        return result


class ListCIJobsInput(BaseModel):
    """Input schema for ListCIJobsTool."""

    dummy: str = Field(
        default="",
        description="No input required. Just call this tool to list CI jobs.",
    )


class ListCIJobsTool(BaseTool):
    """List all available CI job folders."""

    name: str = "List CI Jobs"
    description: str = (
        "List all available CI job folders in the workspace. "
        "Use this to see what jobs are available for analysis. "
        "No input required."
    )
    args_schema: type[BaseModel] = ListCIJobsInput

    def _run(self, dummy: str = "") -> str:
        """List CI jobs."""
        if not CI_RESULTS_DIR.exists():
            return "No CI results directory found. CI data may not have been collected."

        jobs = []
        for item in CI_RESULTS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        meta = json.load(f)
                    jobs.append(
                        {
                            "folder": item.name,
                            "name": meta.get("job_name", item.name),
                            "conclusion": meta.get("conclusion", "unknown"),
                        }
                    )
                else:
                    jobs.append({"folder": item.name, "name": item.name, "conclusion": "unknown"})

        if not jobs:
            return "No CI job folders found."

        result = "# Available CI Jobs\n\n"
        for job in jobs:
            status = "SUCCESS" if job["conclusion"] == "success" else "FAILED"
            result += f"- [{status}] **{job['name']}** (folder: `{job['folder']}`)\n"

        return result


# Tool instances for export
read_job_index = ReadJobIndexTool()
check_log_size = CheckLogSizeTool()
read_job_summary = ReadJobSummaryTool()
search_log = SearchLogTool()
read_full_log = ReadFullLogTool()
get_log_stats = GetLogStatsTool()
list_ci_jobs = ListCIJobsTool()
