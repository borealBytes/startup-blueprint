"""Workspace tool for shared context between agents."""

import json
import logging
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class WorkspaceTool(BaseTool):
    """Read/write shared workspace to minimize duplicate API calls."""

    name: str = "Workspace Tool"
    description: str = (
        "Read and write files to shared workspace. "
        "Use this to cache data fetched by other agents and avoid duplicate API calls. "
        "Available operations: read(filename), write(filename, content), exists(filename)"
    )

    def __init__(self):
        super().__init__()
        self.workspace_dir = Path(".crewai/workspace")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_dir = self.workspace_dir / "trace"
        self.trace_dir.mkdir(exist_ok=True)

    def _run(self, operation: str, filename: str, content: str = "") -> Any:
        """Execute workspace operation.

        Args:
            operation: One of 'read', 'write', 'exists'
            filename: File to operate on (relative to workspace/)
            content: Content to write (only for 'write' operation)

        Returns:
            For 'read': File content as string
            For 'write': Success message
            For 'exists': Boolean
        """
        filepath = self.workspace_dir / filename

        if operation == "read":
            return self.read(filename)
        elif operation == "write":
            return self.write(filename, content)
        elif operation == "exists":
            return self.exists(filename)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def read(self, filename: str) -> str:
        """Read file from workspace."""
        filepath = self.workspace_dir / filename
        if not filepath.exists():
            logger.warning(f"Workspace file not found: {filename}")
            return ""

        try:
            with open(filepath) as f:
                content = f.read()
            logger.info(f"📖 Read {len(content)} bytes from workspace/{filename}")
            return content
        except Exception as e:
            logger.error(f"Error reading workspace/{filename}: {e}")
            return ""

    def write(self, filename: str, content: str) -> str:
        """Write file to workspace."""
        filepath = self.workspace_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"💾 Wrote {len(content)} bytes to workspace/{filename}")
            return f"Successfully wrote to workspace/{filename}"
        except Exception as e:
            error_msg = f"Error writing to workspace/{filename}: {e}"
            logger.error(error_msg)
            return error_msg

    def exists(self, filename: str) -> bool:
        """Check if file exists in workspace."""
        filepath = self.workspace_dir / filename
        exists = filepath.exists()
        logger.debug(f"Check workspace/{filename}: {exists}")
        return exists

    def read_json(self, filename: str) -> dict:
        """Read JSON file from workspace."""
        content = self.read(filename)
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {filename}: {e}")
            return {}

    def write_json(self, filename: str, data: dict) -> str:
        """Write JSON file to workspace."""
        try:
            content = json.dumps(data, indent=2)
            return self.write(filename, content)
        except Exception as e:
            error_msg = f"Error serializing JSON to {filename}: {e}"
            logger.error(error_msg)
            return error_msg
