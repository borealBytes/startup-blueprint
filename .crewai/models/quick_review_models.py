"""Pydantic models for quick review crew structured output."""

from typing import List, Literal

from pydantic import BaseModel, Field


class ChangedFile(BaseModel):
    """Model for a changed file in the diff."""

    path: str = Field(description="File path")
    type: str = Field(description="File type/extension")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        description="Risk level of changes"
    )


class DiffContext(BaseModel):
    """Model for diff context output."""

    commit_intent: str = Field(description="Summary of what changed from commit messages")
    total_changes: int = Field(description="Total count of changed lines")
    changed_files: List[ChangedFile] = Field(description="List of changed files with metadata")
    review_focus_areas: List[str] = Field(
        description="Focus tags like security, database, config, etc."
    )
    sampled_diff: str = Field(description="Filtered/focused diff text for next agent")


class CodeIssue(BaseModel):
    """Model for a single code issue."""

    file: str = Field(description="File path where issue was found")
    line: int = Field(description="Line number (0 if unknown)")
    code_snippet: str = Field(description="Relevant code snippet")
    description: str = Field(description="Issue description")
    severity: Literal["critical", "warning", "info"] = Field(
        default="info", description="Issue severity"
    )


class CodeIssues(BaseModel):
    """Model for code issues output."""

    critical: List[CodeIssue] = Field(default_factory=list, description="Critical issues")
    warnings: List[CodeIssue] = Field(default_factory=list, description="Warning-level issues")
    info: List[CodeIssue] = Field(default_factory=list, description="Informational issues")


class QuickReview(BaseModel):
    """Model for final quick review output."""

    status: Literal["ok", "warning", "critical"] = Field(description="Overall review status")
    summary: str = Field(description="One-line summary (minimum 100 characters)")
    total_findings: int = Field(description="Total number of findings")
    critical: List[CodeIssue] = Field(default_factory=list, description="Critical issues")
    warnings: List[CodeIssue] = Field(default_factory=list, description="Warning-level issues")
    info: List[CodeIssue] = Field(default_factory=list, description="Informational issues")
    merge_status: Literal["APPROVE", "REQUEST_CHANGES", "NEEDS_DISCUSSION"] = Field(
        description="Merge recommendation"
    )
    merge_rationale: str = Field(description="Explanation for merge decision")
