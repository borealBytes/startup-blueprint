"""Full technical review crew (triggered by label)."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import FileContentTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Comprehensive technical review (security, architecture, related files)."""

    # Use CrewBase.load_yaml() - finds config relative to project root
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks/full_review_tasks.yaml"

    def __init__(self):
        """Initialize full review crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def security_reviewer(self) -> Agent:
        """Create security reviewer agent."""
        return Agent(
            config=self.agents_config["security_reviewer"],
            tools=[WorkspaceTool(), FileContentTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def security_review(self) -> Task:
        """Perform security review."""
        return Task(
            config=self.tasks_config["security_review"],
            agent=self.security_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create full review crew."""
        return Crew(
            agents=[self.security_reviewer()],
            tasks=[self.security_review()],
            process=Process.sequential,
            verbose=True,
        )
