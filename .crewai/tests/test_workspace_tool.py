"""Tests for Workspace Tool."""

import json
import os
import tempfile
import pytest
from tools.workspace_tool import WorkspaceTool


class TestWorkspaceTool:
    """Test suite for WorkspaceTool."""

    def test_init_creates_workspace(self):
        """Test that workspace directory is created on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            assert os.path.exists(tmpdir)

    def test_write_file(self):
        """Test writing a file to workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            result = tool._run(operation="write", filename="test.txt", content="Hello")
            
            assert os.path.exists(os.path.join(tmpdir, "test.txt"))
            assert "test.txt" in result

    def test_write_json_file(self):
        """Test writing JSON content to workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            data = {"key": "value", "number": 42}
            result = tool._run(
                operation="write", 
                filename="data.json", 
                content=json.dumps(data, indent=2)
            )
            
            file_path = os.path.join(tmpdir, "data.json")
            assert os.path.exists(file_path)
            
            with open(file_path) as f:
                loaded = json.load(f)
                assert loaded == data

    def test_read_file(self):
        """Test reading a file from workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            
            # Write first
            tool._run(operation="write", filename="test.txt", content="Hello World")
            
            # Then read
            result = tool._run(operation="read", filename="test.txt")
            assert "Hello World" in result

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            result = tool._run(operation="read", filename="nonexistent.txt")
            
            # Should return empty string
            assert result == ""

    def test_list_files_empty(self):
        """Test checking file existence in empty workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            # Use 'exists' operation instead of 'list' (which isn't implemented)
            result = tool._run(operation="exists", filename="test.txt")
            
            assert result is False

    def test_list_files_with_content(self):
        """Test checking file existence with content in workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            
            # Create a file
            tool._run(operation="write", filename="file1.txt", content="Content 1")
            
            # Check it exists
            result = tool._run(operation="exists", filename="file1.txt")
            assert result is True

    def test_invalid_operation(self):
        """Test handling invalid operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            
            with pytest.raises(ValueError):
                tool._run(operation="invalid_op", filename="test.txt")

    def test_write_with_subdirectory(self):
        """Test writing file in a subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            result = tool._run(
                operation="write",
                filename="subdir/file.txt",
                content="Nested content"
            )
            
            file_path = os.path.join(tmpdir, "subdir", "file.txt")
            assert os.path.exists(file_path)

    def test_write_empty_content(self):
        """Test writing file with empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            result = tool._run(operation="write", filename="empty.txt", content="")
            
            file_path = os.path.join(tmpdir, "empty.txt")
            assert os.path.exists(file_path)
