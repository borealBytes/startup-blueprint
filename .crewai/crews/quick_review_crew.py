"""Quick review crew for fast code quality checks."""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import FileContentTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Quick review crew (default workflow)."""

    def __init__(self):
        """Initialize quick review crew."""
        config_dir = Path(__file__).parent.parent / "config"

        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks" / "quick_review_tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # LLM config
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def quick_reviewer(self) -> Agent:
        """Create quick reviewer agent."""
        return Agent(
            config=self.agents_config["quick_reviewer"],
            tools=[
                WorkspaceTool(),
                FileContentTool(),  # Only if needed for context
            ],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def quick_code_review(self) -> Task:
        """Quick code review task."""
        return Task(
            config=self.tasks_config["quick_code_review"],
            agent=self.quick_reviewer(),
        )

    @task
    def correlate_ci_and_code(self) -> Task:
        """Correlate CI issues with code changes."""
        return Task(
            config=self.tasks_config["correlate_ci_and_code"],
            agent=self.quick_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create quick review crew."""
        return Crew(
            agents=[self.quick_reviewer()],
            tasks=[self.quick_code_review(), self.correlate_ci_and_code()],
            process=Process.sequential,
            verbose=True,
        )
