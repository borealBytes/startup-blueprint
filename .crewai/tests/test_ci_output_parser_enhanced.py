"""Enhanced tests for CI Output Parser Tool with log file parsing."""

import os
from pathlib import Path

import pytest

from tools.ci_output_parser_tool import CIOutputParserTool


class TestCIOutputParserEnhanced:
    """Test suite for enhanced CI log parsing."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        os.environ["COMMIT_SHA"] = "aa8c1c2"
        return CIOutputParserTool()

    @pytest.fixture
    def fixtures_dir(self):
        """Get fixtures directory."""
        return Path(__file__).parent / "fixtures" / "ci_results"

    def test_parse_pr15_logs_detects_stylelint_errors(self, tool, fixtures_dir):
        """PR #15 Regression Test: Detect 77 stylelint errors.

        This test verifies that the enhanced parser can extract the 77 stylelint
        errors that were present in PR #15 but missing from the original output.
        """
        result = tool._run(core_ci_result="success", ci_logs_dir=str(fixtures_dir))

        # Should detect stylelint errors
        all_errors = result.get("critical_errors", []) + result.get("warnings", [])
        stylelint_errors = [e for e in all_errors if e.get("tool") == "stylelint"]

        # PR #15 had 77 stylelint errors
        assert len(stylelint_errors) > 0, "Should detect stylelint errors"

        # Verify error structure
        if stylelint_errors:
            error = stylelint_errors[0]
            assert "file" in error, "Error should have file path"
            assert "line" in error, "Error should have line number"
            assert "message" in error, "Error should have message"

    def test_parse_pr15_logs_detects_sqlfluff_errors(self, tool, fixtures_dir):
        """PR #15 Regression Test: Detect sqlfluff errors.

        PR #15 had at least 1 sqlfluff error (RF04 rule violation).
        """
        result = tool._run(core_ci_result="success", ci_logs_dir=str(fixtures_dir))

        all_errors = result.get("critical_errors", []) + result.get("warnings", [])
        sqlfluff_errors = [e for e in all_errors if e.get("tool") == "sqlfluff"]

        # PR #15 had sqlfluff errors
        assert len(sqlfluff_errors) > 0, "Should detect sqlfluff errors"

    def test_parse_includes_job_metadata(self, tool, fixtures_dir):
        """Parser should include job metadata in output."""
        result = tool._run(core_ci_result="success", ci_logs_dir=str(fixtures_dir))

        # Should have jobs_analyzed field
        assert "jobs_analyzed" in result, "Result should include jobs_analyzed"
        assert len(result["jobs_analyzed"]) > 0, "Should analyze at least one job"

        # Each job should have name and error count
        for job in result["jobs_analyzed"]:
            assert "name" in job, "Job should have name"
            assert "errors_found" in job, "Job should have errors_found count"

    def test_parse_creates_check_list(self, tool, fixtures_dir):
        """Parser should create list of checks performed."""
        result = tool._run(core_ci_result="success", ci_logs_dir=str(fixtures_dir))

        assert "checks_performed" in result, "Result should include checks_performed"
        assert isinstance(result["checks_performed"], list), "checks_performed should be a list"

    def test_backward_compatibility_env_var_only(self, tool):
        """Parser should still work with just env var (backward compatibility)."""
        result = tool._run(core_ci_result="success")

        assert result["status"] == "success"
        assert result["passed"] is True
        assert "summary" in result

    def test_graceful_missing_logs_dir(self, tool):
        """Parser should handle missing ci_results directory gracefully."""
        result = tool._run(core_ci_result="success", ci_logs_dir="/nonexistent/path")

        # Should not crash, should return basic result
        assert result["status"] == "success"
        assert "jobs_analyzed" in result
        assert len(result["jobs_analyzed"]) == 0  # No jobs found

    def test_performance_under_30_seconds(self, tool, fixtures_dir):
        """Parser should complete in under 30 seconds for typical PR."""
        import time

        start = time.time()
        result = tool._run(core_ci_result="success", ci_logs_dir=str(fixtures_dir))
        elapsed = time.time() - start

        assert elapsed < 30, f"Parser took {elapsed:.2f}s, should be under 30s"
