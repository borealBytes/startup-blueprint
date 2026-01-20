"""Workspace tool for shared context between agents."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from crewai.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)


class WorkspaceTool(BaseTool):
    """Read/write shared workspace to minimize duplicate API calls."""

    name: str = "Workspace Tool"
    description: str = (
        "Read and write files to shared workspace. "
        "Use this to cache data fetched by other agents and avoid duplicate API calls. "
        "Available operations: read(filename), write(filename, content), exists(filename)"
    )

    # Pydantic v2 requires fields to be declared
    # Use absolute path to avoid CWD issues when workflow sets working-directory
    workspace_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "workspace")
    trace_dir: Optional[Path] = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize workspace directories after Pydantic validation."""
        super().model_post_init(__context)
        # Ensure we're using an absolute path
        self.workspace_dir = self.workspace_dir.resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_dir = self.workspace_dir / "trace"
        self.trace_dir.mkdir(exist_ok=True)
        logger.info(f"📁 WorkspaceTool initialized: {self.workspace_dir}")

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
            logger.warning(f"⚠️ Workspace file not found: {filepath}")
            return ""

        try:
            with open(filepath) as f:
                content = f.read()
            logger.info(f"📖 Read {len(content)} bytes from {filepath}")
            return content
        except Exception as e:
            logger.error(f"❌ Error reading {filepath}: {e}")
            return ""

    def write(self, filename: str, content: str) -> str:
        """Write file to workspace."""
        filepath = self.workspace_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"💾 Wrote {len(content)} bytes to {filepath}")
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            error_msg = f"❌ Error writing to {filepath}: {e}"
            logger.error(error_msg)
            return error_msg

    def exists(self, filename: str) -> bool:
        """Check if file exists in workspace."""
        filepath = self.workspace_dir / filename
        exists = filepath.exists()
        logger.info(f"🔍 Check {filepath}: {'EXISTS' if exists else 'NOT FOUND'}")
        return exists

    def read_json(self, filename: str) -> dict:
        """Read JSON file from workspace."""
        content = self.read(filename)
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON from {filename}: {e}")
            return {}

    def write_json(self, filename: str, data: dict) -> str:
        """Write JSON file to workspace."""
        try:
            content = json.dumps(data, indent=2)
            return self.write(filename, content)
        except Exception as e:
            error_msg = f"❌ Error serializing JSON to {filename}: {e}"
            logger.error(error_msg)
            return error_msg
