"""Enhanced CI output parser tool for analyzing CI job logs."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CIError(BaseModel):
    """Schema for CI error/warning."""

    tool: str = Field(description="Tool that reported the error")
    type: str = Field(description="Error type/category")
    severity: str = Field(description="critical|warning|info")
    file: str = Field(description="File path")
    line: str = Field(description="Line number")
    column: str = Field(default="", description="Column number if available")
    message: str = Field(description="Error message")
    code: str = Field(default="", description="Error code/rule if available")
    context: str = Field(default="", description="Additional context")
    fix_suggestion: str = Field(default="", description="Suggested fix")


class CISummary(BaseModel):
    """Schema for CI analysis summary."""

    status: str = Field(description="success|failure|warning")
    passed: bool = Field(description="Whether CI passed")
    summary: str = Field(description="Brief summary")
    checks_performed: list[str] = Field(default_factory=list)
    critical_errors: list[CIError] = Field(default_factory=list)
    warnings: list[CIError] = Field(default_factory=list)
    info: list[CIError] = Field(default_factory=list)
    jobs_analyzed: list[dict] = Field(default_factory=list)
    issue_analysis: dict = Field(default_factory=dict)


class CIOutputParserTool(BaseTool):
    """Parse CI job logs and extract detailed error information."""

    name: str = "CI Output Parser Tool"
    description: str = (
        "Parse CI job logs from ci_results directory. "
        "Returns: detailed errors, warnings, job summaries with file paths and line numbers. "
        "Can search logs for specific patterns and extract error context."
    )

    def _run(
        self,
        core_ci_result: str = "",
        ci_logs_dir: str = "ci_results",
        search_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Parse CI outputs from environment and log files.

        Args:
            core_ci_result: Job result from needs.core-ci.result
            ci_logs_dir: Directory containing CI job folders
            search_patterns: Optional patterns to search for in logs

        Returns:
            Dict with detailed CI status, errors, warnings
        """
        if not core_ci_result:
            core_ci_result = os.getenv("CORE_CI_RESULT", "success")

        logger.info(f"📊 Parsing CI results: {core_ci_result}")

        ci_summary = CISummary(
            status=core_ci_result,
            passed=core_ci_result == "success",
            summary="",
            checks_performed=[],
            critical_errors=[],
            warnings=[],
            info=[],
            jobs_analyzed=[],
            issue_analysis={},
        )

        resolved_logs_dir = self._resolve_ci_logs_dir(ci_logs_dir)
        job_index_path = Path(resolved_logs_dir) / "_job_index.json"
        if job_index_path.exists():
            try:
                with open(job_index_path) as f:
                    job_index = json.load(f)
                logger.info(f"📋 Found {len(job_index.get('jobs', []))} jobs in index")
            except Exception as e:
                logger.warning(f"Could not read job index: {e}")
                job_index = {"jobs": []}
        else:
            job_index = self._discover_jobs(resolved_logs_dir)

        all_errors = []
        for job in job_index.get("jobs", []):
            job_name = job.get("job_name", "unknown")
            job_folder = job.get("job_folder", job_name)
            log_path = Path(resolved_logs_dir) / job_folder / "log.txt"

            if log_path.exists():
                logger.info(f"🔍 Analyzing {job_name} logs...")
                job_errors = self._parse_job_log(log_path, job_name)
                all_errors.extend(job_errors)

                job_summary = {
                    "name": job_name,
                    "conclusion": job.get("conclusion", "unknown"),
                    "errors_found": len(job_errors),
                    "log_size": log_path.stat().st_size,
                }
                ci_summary.jobs_analyzed.append(job_summary)

                logger.info(f"  Found {len(job_errors)} issues in {job_name}")

        for error in all_errors:
            if error.severity == "critical":
                ci_summary.critical_errors.append(error)
            elif error.severity == "warning":
                ci_summary.warnings.append(error)
            else:
                ci_summary.info.append(error)

        ci_summary.checks_performed = list(set(e.tool for e in all_errors))

        total_errors = len(ci_summary.critical_errors)
        total_warnings = len(ci_summary.warnings)

        if core_ci_result == "success" and total_errors == 0:
            ci_summary.summary = (
                f"All CI checks passed ✅ ({len(ci_summary.jobs_analyzed)} jobs analyzed)"
            )
            logger.info("✅ Core CI passed with no errors")
        elif total_errors > 0:
            ci_summary.status = "failure"
            ci_summary.passed = False
            ci_summary.summary = (
                f"CI failed with {total_errors} critical errors and {total_warnings} warnings ❌"
            )
            logger.warning(f"⚠️ CI failed: {total_errors} errors, {total_warnings} warnings")
        elif total_warnings > 0:
            ci_summary.status = "warning"
            ci_summary.summary = f"CI passed with {total_warnings} warnings ⚠️"
            logger.warning(f"⚠️ CI passed with {total_warnings} warnings")
        else:
            ci_summary.summary = f"CI status: {core_ci_result}"

        ci_summary.issue_analysis = self._generate_issue_analysis(all_errors)

        if search_patterns:
            search_results = self._search_logs(resolved_logs_dir, search_patterns)
            ci_summary.issue_analysis["search_results"] = search_results

        return ci_summary.model_dump()

    def _resolve_ci_logs_dir(self, ci_logs_dir: str) -> str:
        logs_path = Path(ci_logs_dir)
        if logs_path.is_absolute():
            return str(logs_path)

        if logs_path.exists():
            return str(logs_path)

        workspace_logs = Path(__file__).parent.parent / "workspace" / ci_logs_dir
        if workspace_logs.exists():
            return str(workspace_logs)

        return str(logs_path)

    def _discover_jobs(self, ci_logs_dir: str) -> dict:
        """Discover CI jobs from directory structure."""
        jobs = []
        logs_path = Path(ci_logs_dir)

        if not logs_path.exists():
            return {"jobs": jobs}

        for job_dir in logs_path.iterdir():
            if job_dir.is_dir() and not job_dir.name.startswith("."):
                log_file = job_dir / "log.txt"
                if log_file.exists():
                    jobs.append(
                        {
                            "job_name": job_dir.name,
                            "job_folder": job_dir.name,
                            "conclusion": "unknown",
                            "log_exists": True,
                        }
                    )

        return {"jobs": jobs}

    def _parse_job_log(self, log_path: Path, job_name: str) -> list[CIError]:
        """Parse a single job log file."""
        errors = []

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {log_path}: {e}")
            return errors

        errors.extend(self._parse_sqlfluff(content, job_name))
        errors.extend(self._parse_stylelint(content, job_name))
        errors.extend(self._parse_markdownlint(content, job_name))
        errors.extend(self._parse_commitlint(content, job_name))
        errors.extend(self._parse_prettier(content, job_name))
        errors.extend(self._parse_black(content, job_name))
        errors.extend(self._parse_isort(content, job_name))
        errors.extend(self._parse_ruff(content, job_name))
        errors.extend(self._parse_eslint(content, job_name))
        errors.extend(self._parse_mypy(content, job_name))
        errors.extend(self._parse_pytest(content, job_name))
        errors.extend(self._parse_build_errors(content, job_name))

        return errors

    def _parse_sqlfluff(self, content: str, job_name: str) -> list[CIError]:
        """Parse sqlfluff output."""
        errors = []
        pattern = r"L:\s*(\d+)\s*\|\s*P:\s*(\d+)\s*\|\s*(\w+)\s*\|\s*(.+?)(?=\nL:|\n==|\n\n|$)"
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_match = re.search(r"\[([^\]]+)\]\s*FAIL", content[: match.start()])
            file_path = file_match.group(1) if file_match else "unknown.sql"

            errors.append(
                CIError(
                    tool="sqlfluff",
                    type="SQL Lint Error",
                    severity="warning",
                    file=file_path,
                    line=match.group(1),
                    column=match.group(2),
                    message=match.group(4).strip(),
                    code=match.group(3),
                    fix_suggestion="Review SQL syntax and follow best practices",
                )
            )

        return errors

    def _parse_stylelint(self, content: str, job_name: str) -> list[CIError]:
        """Parse stylelint output."""
        errors = []
        stylelint_match = re.search(r"--- stylelint ---(.+?)(?=--- \w+ ---|$)", content, re.DOTALL)
        if not stylelint_match:
            return errors

        stylelint_content = stylelint_match.group(1)

        # Remove ANSI escape codes (e.g., [2m, [31m, [39m, etc.)
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        stylelint_content = ansi_escape.sub("", stylelint_content)

        file_match = re.search(r"^\s*(\S+\.css|\.scss|\.less)", stylelint_content, re.MULTILINE)
        file_path = file_match.group(1) if file_match else "unknown.css"

        # Pattern: line:column  ✖  message  rule
        pattern = r"\s*(\d+):(\d+)\s+✖\s+(.+?)\s{2,}(\S+)\s*$"
        matches = re.finditer(pattern, stylelint_content, re.MULTILINE)

        for match in matches:
            message = match.group(3).strip()
            rule = match.group(4).strip()

            severity = "warning"
            if "error" in rule.lower() or any(
                x in message.lower() for x in ["invalid", "error", "fail"]
            ):
                severity = "critical"

            errors.append(
                CIError(
                    tool="stylelint",
                    type="CSS Lint Error",
                    severity=severity,
                    file=file_path,
                    line=match.group(1),
                    column=match.group(2),
                    message=message,
                    code=rule,
                    fix_suggestion=f"Fix CSS linting issue: {rule}",
                )
            )

        return errors

        stylelint_content = stylelint_match.group(1)
        file_match = re.search(r"^\s*(\S+\.css|\.scss|\.less)", stylelint_content, re.MULTILINE)
        file_path = file_match.group(1) if file_match else "unknown.css"

        pattern = r"\s*(\d+):(\d+)\s+✖\s+(.+?)\s{2,}(\S+)\s*$"
        matches = re.finditer(pattern, stylelint_content, re.MULTILINE)

        for match in matches:
            message = match.group(3).strip()
            rule = match.group(4).strip()

            severity = "warning"
            if "error" in rule.lower() or any(
                x in message.lower() for x in ["invalid", "error", "fail"]
            ):
                severity = "critical"

            errors.append(
                CIError(
                    tool="stylelint",
                    type="CSS Lint Error",
                    severity=severity,
                    file=file_path,
                    line=match.group(1),
                    column=match.group(2),
                    message=message,
                    code=rule,
                    fix_suggestion=f"Fix CSS linting issue: {rule}",
                )
            )

        return errors

    def _parse_markdownlint(self, content: str, job_name: str) -> list[CIError]:
        """Parse markdownlint output."""
        errors = []
        pattern = r"(.+\.md):(\d+):?(\d*)\s+(MD\w+)\s+(.+)"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="markdownlint",
                    type="Markdown Lint Error",
                    severity="info",
                    file=match.group(1),
                    line=match.group(2),
                    column=match.group(3) or "",
                    message=match.group(5).strip(),
                    code=match.group(4),
                    fix_suggestion=f"Fix markdown linting rule {match.group(4)}",
                )
            )

        return errors

    def _parse_commitlint(self, content: str, job_name: str) -> list[CIError]:
        """Parse commitlint output."""
        errors = []
        pattern = r"✖\s+(.+?)\s*\[([^\]]+)\]"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="commitlint",
                    type="Commit Message Error",
                    severity="warning",
                    file="commit message",
                    line="",
                    message=match.group(1).strip(),
                    code=match.group(2),
                    fix_suggestion="Follow conventional commit format",
                )
            )

        return errors

    def _parse_prettier(self, content: str, job_name: str) -> list[CIError]:
        """Parse prettier output."""
        errors = []
        pattern = r"\[warn\]\s+(.+?\.\w+)"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="prettier",
                    type="Format Warning",
                    severity="info",
                    file=match.group(1),
                    line="",
                    message="File needs formatting",
                    fix_suggestion="Run prettier to auto-format",
                )
            )

        return errors

    def _parse_black(self, content: str, job_name: str) -> list[CIError]:
        """Parse black output."""
        errors = []
        pattern = r"would reformat\s+(.+\.py)"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="black",
                    type="Format Warning",
                    severity="info",
                    file=match.group(1),
                    line="",
                    message="File needs formatting",
                    fix_suggestion="Run black to auto-format Python code",
                )
            )

        return errors

    def _parse_isort(self, content: str, job_name: str) -> list[CIError]:
        """Parse isort output."""
        errors = []
        pattern = r"ERROR:\s*(.+\.py)\s+Imports are incorrectly sorted"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="isort",
                    type="Import Order Error",
                    severity="warning",
                    file=match.group(1),
                    line="",
                    message="Imports are incorrectly sorted",
                    fix_suggestion="Run isort to fix import order",
                )
            )

        return errors

    def _parse_ruff(self, content: str, job_name: str) -> list[CIError]:
        """Parse ruff output."""
        errors = []
        pattern = r"(.+\.py):(\d+):(\d+):\s*(\w+)\s+(.+)"
        matches = re.finditer(pattern, content)

        for match in matches:
            code = match.group(4)
            severity = "critical" if code.startswith(("E", "F")) else "warning"

            errors.append(
                CIError(
                    tool="ruff",
                    type="Python Lint Error",
                    severity=severity,
                    file=match.group(1),
                    line=match.group(2),
                    column=match.group(3),
                    message=match.group(5).strip(),
                    code=code,
                    fix_suggestion=f"Fix ruff error {code}",
                )
            )

        return errors

    def _parse_eslint(self, content: str, job_name: str) -> list[CIError]:
        """Parse eslint output."""
        errors = []
        file_pattern = r"^(/.+\.\w+)$"
        error_pattern = r"\s+(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+(\S+)\s*$"

        lines = content.split("\n")
        current_file = None

        for line in lines:
            file_match = re.match(file_pattern, line)
            if file_match:
                current_file = file_match.group(1)
                continue

            error_match = re.match(error_pattern, line)
            if error_match and current_file:
                severity = "critical" if error_match.group(3) == "error" else "warning"
                errors.append(
                    CIError(
                        tool="eslint",
                        type="JavaScript/TypeScript Lint Error",
                        severity=severity,
                        file=current_file,
                        line=error_match.group(1),
                        column=error_match.group(2),
                        message=error_match.group(4).strip(),
                        code=error_match.group(5),
                        fix_suggestion=f"Fix eslint rule {error_match.group(5)}",
                    )
                )

        return errors

    def _parse_mypy(self, content: str, job_name: str) -> list[CIError]:
        """Parse mypy output."""
        errors = []
        pattern = r"(.+\.py):(\d+):\s*(error|warning|note):\s*(.+)"
        matches = re.finditer(pattern, content)

        for match in matches:
            msg_type = match.group(3)
            severity = (
                "critical"
                if msg_type == "error"
                else "warning"
                if msg_type == "warning"
                else "info"
            )

            errors.append(
                CIError(
                    tool="mypy",
                    type="Type Error",
                    severity=severity,
                    file=match.group(1),
                    line=match.group(2),
                    message=match.group(4).strip(),
                    fix_suggestion="Fix type annotation or adjust types",
                )
            )

        return errors

    def _parse_pytest(self, content: str, job_name: str) -> list[CIError]:
        """Parse pytest output."""
        errors = []
        pattern = r"FAILED\s+(.+?)::(.+?)\s*-\s*(.+)"
        matches = re.finditer(pattern, content)

        for match in matches:
            errors.append(
                CIError(
                    tool="pytest",
                    type="Test Failure",
                    severity="critical",
                    file=match.group(1),
                    line="",
                    message=f"Test failed: {match.group(2)} - {match.group(3)}",
                    fix_suggestion="Review test logic and fix failing assertions",
                )
            )

        return errors

    def _parse_build_errors(self, content: str, job_name: str) -> list[CIError]:
        """Parse general build errors."""
        errors = []
        pattern = r"(?:Error|ERROR):\s*(.+?)(?=\n|$)"
        matches = re.finditer(pattern, content)

        for match in matches:
            if any(
                tool in content[max(0, match.start() - 50) : match.start()]
                for tool in ["sqlfluff", "stylelint", "eslint", "mypy", "ruff"]
            ):
                continue

            errors.append(
                CIError(
                    tool="build",
                    type="Build Error",
                    severity="critical",
                    file="",
                    line="",
                    message=match.group(1).strip(),
                    fix_suggestion="Review build configuration and dependencies",
                )
            )

        return errors

    def _generate_issue_analysis(self, errors: list[CIError]) -> dict:
        """Generate analysis of issues found."""
        if not errors:
            return {
                "root_cause": "No issues detected",
                "fix_applied": "N/A",
                "recommendation": "All checks passed successfully",
            }

        tool_counts = {}
        for error in errors:
            tool_counts[error.tool] = tool_counts.get(error.tool, 0) + 1

        worst_tool = max(tool_counts, key=tool_counts.get)

        critical_count = len([e for e in errors if e.severity == "critical"])
        warning_count = len([e for e in errors if e.severity == "warning"])

        return {
            "root_cause": f"{worst_tool} reported the most issues ({tool_counts[worst_tool]})",
            "fix_applied": f"Auto-fix attempted for {len([e for e in errors if e.tool in ['prettier', 'black', 'isort']])} formatting issues",
            "recommendation": f"Address {critical_count} critical errors and {warning_count} warnings before merging",
            "tool_breakdown": tool_counts,
        }

    def _search_logs(self, ci_logs_dir: str, patterns: list[str]) -> list[dict]:
        """Search logs for specific patterns."""
        results = []
        logs_path = Path(ci_logs_dir)

        for job_dir in logs_path.iterdir():
            if not job_dir.is_dir():
                continue

            log_file = job_dir / "log.txt"
            if not log_file.exists():
                continue

            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")

                for pattern in patterns:
                    regex = re.compile(pattern, re.IGNORECASE)
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = "\n".join(lines[start:end])

                            results.append(
                                {
                                    "job": job_dir.name,
                                    "pattern": pattern,
                                    "line_number": i + 1,
                                    "match": line.strip(),
                                    "context": context,
                                }
                            )
            except Exception as e:
                logger.warning(f"Could not search {log_file}: {e}")

        return results
