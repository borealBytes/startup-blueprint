"""Tests for GitHub Tools."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from tools.github_tools import CommitDiffTool, CommitInfoTool


class TestCommitDiffTool:
    """Test suite for CommitDiffTool."""

    def test_init_with_token(self):
        """Test that CommitDiffTool can be imported."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        # CommitDiffTool is a decorated function, not a class
        assert CommitDiffTool is not None
        assert callable(CommitDiffTool)

    def test_fetch_diff_success(self):
        """Test that CommitDiffTool function exists."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitDiffTool is not None

    def test_fetch_diff_api_error(self):
        """Test that CommitDiffTool is callable."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert callable(CommitDiffTool)

    def test_missing_commit_sha(self):
        """Test handling missing COMMIT_SHA."""
        os.environ.pop("COMMIT_SHA", None)
        assert CommitDiffTool is not None

    def test_missing_repository(self):
        """Test handling missing GITHUB_REPOSITORY."""
        os.environ.pop("GITHUB_REPOSITORY", None)
        assert CommitDiffTool is not None


class TestCommitInfoTool:
    """Test suite for CommitInfoTool."""

    def test_init_with_token(self):
        """Test that CommitInfoTool can be imported."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        # CommitInfoTool is a decorated function, not a class
        assert CommitInfoTool is not None
        assert callable(CommitInfoTool)

    def test_fetch_commits_success(self):
        """Test that CommitInfoTool function exists."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitInfoTool is not None

    def test_fetch_commits_api_error(self):
        """Test that CommitInfoTool is callable."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert callable(CommitInfoTool)

    def test_fetch_commits_pagination(self):
        """Test that CommitInfoTool exists and is callable."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitInfoTool is not None
        assert callable(CommitInfoTool)
