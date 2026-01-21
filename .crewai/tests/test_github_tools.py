"""Tests for GitHub-related tools."""

import json
from unittest.mock import MagicMock, patch

import pytest
from tools.github_tools import CommitDiffTool, CommitInfoTool


class TestCommitDiffTool:
    """Test suite for CommitDiffTool."""

    def test_init_with_token(self, mock_env_vars):
        """Test initialization with GitHub token."""
        tool = CommitDiffTool()
        assert tool.github_token == mock_env_vars["GITHUB_TOKEN"]

    @patch("requests.get")
    def test_fetch_diff_success(self, mock_get, mock_env_vars, sample_diff):
        """Test fetching diff successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_diff
        mock_get.return_value = mock_response

        tool = CommitDiffTool()
        result = tool._run(commit_sha="abc123def456", repository="test-owner/test-repo")

        assert "abc123def456" in result
        assert "src/app.py" in result
        assert "README.md" in result

    @patch("requests.get")
    def test_fetch_diff_api_error(self, mock_get, mock_env_vars):
        """Test handling of API error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        tool = CommitDiffTool()
        result = tool._run(commit_sha="invalid", repository="test-owner/test-repo")

        assert "error" in result.lower() or "failed" in result.lower()

    def test_missing_commit_sha(self, mock_env_vars):
        """Test error when commit_sha is missing."""
        tool = CommitDiffTool()
        result = tool._run(commit_sha="", repository="test-owner/test-repo")
        assert "error" in result.lower() or "required" in result.lower()

    def test_missing_repository(self, mock_env_vars):
        """Test error when repository is missing."""
        tool = CommitDiffTool()
        result = tool._run(commit_sha="abc123", repository="")
        assert "error" in result.lower() or "required" in result.lower()


class TestCommitInfoTool:
    """Test suite for CommitInfoTool."""

    def test_init_with_token(self, mock_env_vars):
        """Test initialization with GitHub token."""
        tool = CommitInfoTool()
        assert tool.github_token == mock_env_vars["GITHUB_TOKEN"]

    @patch("requests.get")
    def test_fetch_commits_success(self, mock_get, mock_env_vars, sample_commits):
        """Test fetching commit history successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_commits
        mock_get.return_value = mock_response

        tool = CommitInfoTool()
        result = tool._run(commit_sha="abc123def456", repository="test-owner/test-repo")

        assert "feat: add new feature" in result
        assert "fix: resolve bug" in result

    @patch("requests.get")
    def test_fetch_commits_api_error(self, mock_get, mock_env_vars):
        """Test handling of API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        tool = CommitInfoTool()
        result = tool._run(commit_sha="abc123", repository="test-owner/test-repo")

        assert "error" in result.lower() or "failed" in result.lower()

    @patch("requests.get")
    def test_fetch_commits_pagination(self, mock_get, mock_env_vars):
        """Test that tool requests correct number of commits."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        tool = CommitInfoTool()
        tool._run(commit_sha="abc123", repository="test-owner/test-repo")

        # Verify API was called with per_page parameter
        call_args = mock_get.call_args
        assert "per_page" in call_args[1]["params"]
        assert call_args[1]["params"]["per_page"] == 10
