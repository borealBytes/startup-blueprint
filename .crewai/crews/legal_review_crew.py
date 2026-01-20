"""Legal review crew - STUB for future implementation."""

import json
import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class LegalReviewCrew:
    """Legal review crew (stub for future)."""

    def __init__(self):
        """Initialize legal review crew."""
        config_dir = Path(__file__).parent.parent / "config"

        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks" / "legal_review_tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # LLM config
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def legal_reviewer(self) -> Agent:
        """Create legal reviewer agent."""
        return Agent(
            config=self.agents_config["legal_compliance_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def analyze_legal_files(self) -> Task:
        """Analyze legal files task (stub)."""
        return Task(
            config=self.tasks_config["analyze_legal_files"],
            agent=self.legal_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create legal review crew."""
        return Crew(
            agents=[self.legal_reviewer()],
            tasks=[self.analyze_legal_files()],
            process=Process.sequential,
            verbose=True,
        )

    def kickoff(self, inputs=None):
        """Override kickoff to return stub response."""
        logger.info("⚠️ Legal review crew not yet implemented - returning stub")

        # Write stub output to workspace
        workspace = WorkspaceTool()
        stub_output = {
            "status": "not_implemented",
            "message": "Legal review crew coming soon",
            "files_detected": [],
            "recommendations": ["Manual legal review recommended for now"],
        }
        workspace.write_json("legal_review.json", stub_output)

        return "Legal review stub completed"
