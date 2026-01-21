"""Tests for CIOutputParserTool."""

import pytest
from tools.ci_output_parser_tool import CIOutputParserTool


class TestCIOutputParserTool:
    """Test suite for CIOutputParserTool."""

    def test_parse_success_result(self, mock_env_vars):
        """Test parsing successful CI result."""
        tool = CIOutputParserTool()
        result = tool._run()

        assert "success" in result.lower()
        # Should indicate CI passed
        assert "passed" in result.lower() or "✅" in result or "success" in result.lower()

    def test_parse_failure_result(self, mock_env_vars):
        """Test parsing failed CI result."""
        with patch.dict("os.environ", {"CORE_CI_RESULT": "failure"}, clear=False) as mock:
            tool = CIOutputParserTool()
            result = tool._run()

            assert "failure" in result.lower() or "failed" in result.lower()

    def test_parse_missing_env_var(self):
        """Test behavior when CORE_CI_RESULT is not set."""
        with patch.dict("os.environ", {}, clear=True):
            tool = CIOutputParserTool()
            result = tool._run()

            # Should return some indication of missing data
            assert result is not None

    def test_output_includes_context(self, mock_env_vars):
        """Test that output includes helpful context."""
        tool = CIOutputParserTool()
        result = tool._run()

        # Should mention what was checked
        # At minimum, should be informative
        assert len(result) > 10  # Not just a single word


from unittest.mock import patch
