"""GitHub API integration tools for CrewAI code review."""

import logging
import os
from typing import Any, Dict

from crewai.tools import tool
from github import Github, GithubException

logger = logging.getLogger(__name__)

# Initialize GitHub client
GHUB = None


def get_github_client():
    """Get or create GitHub client."""
    global GHUB
    if GHUB is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        GHUB = Github(token)
    return GHUB


@tool
def CommitDiffTool(commit_sha: str, repository: str) -> Dict[str, Any]:
    """
    Get the diff for a specific commit.

    Args:
        commit_sha: The commit SHA to get diff for
        repository: Repository name in format 'owner/repo'

    Returns:
        Dictionary with diff content, file stats, and added/removed lines
    """
    try:
        ghub = get_github_client()
        repo = ghub.get_repo(repository)
        commit = repo.get_commit(commit_sha)

        # Convert PaginatedList to list to avoid len() error
        files_list = list(commit.files)

        diff_data = {
            "commit_sha": commit_sha[:8],
            "message": commit.commit.message,
            "author": commit.commit.author.name,
            "files": [],
            "total_additions": commit.stats.additions,
            "total_deletions": commit.stats.deletions,
            "total_changes": commit.stats.total,
        }

        for file_change in files_list:
            file_info = {
                "filename": file_change.filename,
                "status": file_change.status,
                "additions": file_change.additions,
                "deletions": file_change.deletions,
                "changes": file_change.changes,
                "patch": file_change.patch or "(binary file)",
            }
            diff_data["files"].append(file_info)

        logger.info(f"Retrieved diff for {commit_sha[:8]}: " f"{len(files_list)} files changed")
        return diff_data

    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {"error": str(e), "commit_sha": commit_sha}


@tool
def CommitInfoTool(commit_sha: str, repository: str) -> Dict[str, Any]:
    """
    Get detailed commit information.

    Args:
        commit_sha: The commit SHA
        repository: Repository name in format 'owner/repo'

    Returns:
        Commit metadata: message, author, date, stats
    """
    try:
        ghub = get_github_client()
        repo = ghub.get_repo(repository)
        commit = repo.get_commit(commit_sha)

        # Convert PaginatedList to list to get accurate count
        files_count = len(list(commit.files))

        return {
            "sha": commit.sha[:8],
            "message": commit.commit.message,
            "author": {
                "name": commit.commit.author.name,
                "email": commit.commit.author.email,
                "date": commit.commit.author.date.isoformat(),
            },
            "stats": {
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "total_changes": commit.stats.total,
            },
            "files_changed": files_count,
            "url": commit.html_url,
        }

    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {"error": str(e)}


@tool
def FileContentTool(file_path: str, repository: str, ref: str = "HEAD") -> Dict[str, Any]:
    """
    Read file content from repository.

    Args:
        file_path: Path to file in repository
        repository: Repository name in format 'owner/repo'
        ref: Git ref (branch, tag, commit SHA) - defaults to HEAD

    Returns:
        File content and metadata
    """
    try:
        ghub = get_github_client()
        repo = ghub.get_repo(repository)

        try:
            file_obj = repo.get_contents(file_path, ref=ref)
            return {
                "path": file_path,
                "content": file_obj.decoded_content.decode("utf-8"),
                "encoding": file_obj.encoding,
                "size": file_obj.size,
                "sha": file_obj.sha[:8],
            }
        except GithubException as e:
            if e.status == 404:
                return {
                    "error": f"File not found: {file_path}",
                    "path": file_path,
                }
            raise

    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {"error": str(e), "path": file_path}


@tool
def PRCommentTool(pr_number: int, repository: str, comment_body: str) -> Dict[str, Any]:
    """
    Post a comment on a pull request.

    Args:
        pr_number: Pull request number
        repository: Repository name in format 'owner/repo'
        comment_body: Markdown comment to post

    Returns:
        Comment details including URL
    """
    try:
        ghub = get_github_client()
        repo = ghub.get_repo(repository)
        pr = repo.get_pull(pr_number)

        # Truncate if too large (GitHub limit: 65536 chars)
        if len(comment_body) > 65000:
            comment_body = comment_body[:64900] + "\n\n_Comment truncated (exceeded GitHub limit)_"

        comment = pr.create_issue_comment(comment_body)

        logger.info(f"Posted comment to PR #{pr_number}: {comment.html_url}")
        return {
            "pr_number": pr_number,
            "comment_url": comment.html_url,
            "comment_id": comment.id,
            "created_at": comment.created_at.isoformat(),
        }

    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {"error": str(e), "pr_number": pr_number}
