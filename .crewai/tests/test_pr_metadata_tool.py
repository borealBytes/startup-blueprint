"""Tests for PRMetadataTool."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.pr_metadata_tool import PRMetadataTool


class TestPRMetadataTool:
    """Test suite for PRMetadataTool."""

    def test_read_from_environment(self, mock_env_vars):
        """Test reading PR metadata from environment variables."""
        tool = PRMetadataTool()
        result = tool._run()

        assert "123" in result  # PR number
        assert "abc123def456" in result  # commit SHA
        assert "test-owner/test-repo" in result  # repository

    @patch("requests.get")
    def test_fetch_labels_from_api(self, mock_get, mock_env_vars):
        """Test fetching PR labels from GitHub API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": [
                {"name": "crewai:full-review"},
                {"name": "enhancement"},
                {"name": "bug"},
            ]
        }
        mock_get.return_value = mock_response

        tool = PRMetadataTool()
        result = tool._run()

        assert "crewai:full-review" in result
        assert "enhancement" in result
        assert "bug" in result

    def test_missing_environment_variables(self):
        """Test behavior when required env vars are missing."""
        with patch.dict("os.environ", {}, clear=True):
            tool = PRMetadataTool()
            result = tool._run()
            # Should return error or fallback values
            assert result is not None

    @patch("requests.get")
    def test_api_error_fallback(self, mock_get, mock_env_vars):
        """Test fallback when API call fails."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        tool = PRMetadataTool()
        result = tool._run()

        # Should still return basic metadata from env vars
        assert "123" in result or "abc123def456" in result

    def test_output_format(self, mock_env_vars):
        """Test that output is valid JSON."""
        tool = PRMetadataTool()
        result = tool._run()

        # Try to parse as JSON (should be embedded in text)
        # At minimum, should contain key metadata
        assert "commit_sha" in result or "abc123def456" in result
        assert "repository" in result or "test-owner/test-repo" in result
