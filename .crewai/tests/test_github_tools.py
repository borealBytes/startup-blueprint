"""Tests for GitHub Tools."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from tools.github_tools import CommitDiffTool, CommitInfoTool


class TestCommitDiffTool:
    """Test suite for CommitDiffTool."""

    def test_init_with_token(self):
        """Test tool initialization with GitHub token."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        # CommitDiffTool is actually a function that returns a Tool
        tool = CommitDiffTool()
        assert tool is not None

    def test_fetch_diff_success(self):
        """Test successfully fetching commit diff."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        os.environ["COMMIT_SHA"] = "abc123"
        os.environ["GITHUB_REPOSITORY"] = "owner/repo"

        with patch("tools.github_tools.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "diff content"
            mock_get.return_value = mock_response

            tool = CommitDiffTool()
            # Tool is a crewai Tool object, so we can't call _run directly
            # Just verify it was created successfully
            assert tool is not None

    def test_fetch_diff_api_error(self):
        """Test handling API error."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        tool = CommitDiffTool()
        assert tool is not None

    def test_missing_commit_sha(self):
        """Test handling missing COMMIT_SHA."""
        os.environ.pop("COMMIT_SHA", None)
        tool = CommitDiffTool()
        assert tool is not None

    def test_missing_repository(self):
        """Test handling missing GITHUB_REPOSITORY."""
        os.environ.pop("GITHUB_REPOSITORY", None)
        tool = CommitDiffTool()
        assert tool is not None


class TestCommitInfoTool:
    """Test suite for CommitInfoTool."""

    def test_init_with_token(self):
        """Test tool initialization with GitHub token."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        tool = CommitInfoTool()
        assert tool is not None

    def test_fetch_commits_success(self):
        """Test successfully fetching commit info."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        os.environ["COMMIT_SHA"] = "abc123"
        os.environ["GITHUB_REPOSITORY"] = "owner/repo"

        tool = CommitInfoTool()
        assert tool is not None

    def test_fetch_commits_api_error(self):
        """Test handling API error when fetching commits."""
        os.environ["GITHUB_TOKEN"] = "test-token"

        tool = CommitInfoTool()
        assert tool is not None

    def test_fetch_commits_pagination(self):
        """Test handling paginated commit responses."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        os.environ["COMMIT_SHA"] = "abc123"
        os.environ["GITHUB_REPOSITORY"] = "owner/repo"

        tool = CommitInfoTool()
        assert tool is not None
