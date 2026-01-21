"""Tests for WorkspaceTool."""

import json
from pathlib import Path

import pytest
from tools.workspace_tool import WorkspaceTool


class TestWorkspaceTool:
    """Test suite for WorkspaceTool file operations."""

    def test_init_creates_workspace(self, temp_workspace):
        """Test that WorkspaceTool creates workspace directory."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        assert Path(temp_workspace).exists()
        assert Path(temp_workspace).is_dir()

    def test_write_file(self, temp_workspace):
        """Test writing a file to workspace."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        content = "Test content"
        result = tool._run(operation="write", filename="test.txt", content=content)

        assert "successfully" in result.lower()
        file_path = temp_workspace / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == content

    def test_write_json_file(self, temp_workspace):
        """Test writing JSON data to workspace."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        data = {"key": "value", "number": 42}
        content = json.dumps(data)
        result = tool._run(operation="write", filename="test.json", content=content)

        assert "successfully" in result.lower()
        file_path = temp_workspace / "test.json"
        assert file_path.exists()

        loaded_data = json.loads(file_path.read_text())
        assert loaded_data == data

    def test_read_file(self, temp_workspace):
        """Test reading a file from workspace."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))

        # Write first
        file_path = temp_workspace / "read_test.txt"
        file_path.write_text("Test content to read")

        # Read
        result = tool._run(operation="read", filename="read_test.txt")
        assert "Test content to read" in result

    def test_read_nonexistent_file(self, temp_workspace):
        """Test reading a file that doesn't exist."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        result = tool._run(operation="read", filename="nonexistent.txt")
        assert "not found" in result.lower() or "does not exist" in result.lower()

    def test_list_files_empty(self, temp_workspace):
        """Test listing files in empty workspace."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        result = tool._run(operation="list")
        assert "files" in result.lower() or "empty" in result.lower()

    def test_list_files_with_content(self, temp_workspace):
        """Test listing files in workspace with files."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))

        # Create some files
        (temp_workspace / "file1.txt").write_text("Content 1")
        (temp_workspace / "file2.json").write_text('{"key": "value"}')
        (temp_workspace / "file3.md").write_text("# Markdown")

        result = tool._run(operation="list")
        assert "file1.txt" in result
        assert "file2.json" in result
        assert "file3.md" in result

    def test_invalid_operation(self, temp_workspace):
        """Test handling of invalid operation."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        result = tool._run(operation="invalid_op", filename="test.txt")
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_write_with_subdirectory(self, temp_workspace):
        """Test writing file with subdirectory in path."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        result = tool._run(operation="write", filename="subdir/test.txt", content="Test")

        file_path = temp_workspace / "subdir" / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Test"

    def test_write_empty_content(self, temp_workspace):
        """Test writing empty content."""
        tool = WorkspaceTool(workspace_dir=str(temp_workspace))
        result = tool._run(operation="write", filename="empty.txt", content="")

        file_path = temp_workspace / "empty.txt"
        assert file_path.exists()
        assert file_path.read_text() == ""
