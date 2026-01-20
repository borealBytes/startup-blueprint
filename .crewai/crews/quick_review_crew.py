"""Quick review crew for fast, lightweight code review."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Fast code quality review (~1 minute)."""

    # Use CrewBase.load_yaml() - finds config relative to project root
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks/quick_review_tasks.yaml"

    def __init__(self):
        """Initialize quick review crew."""
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
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def quick_code_review(self) -> Task:
        """Perform quick code review."""
        return Task(
            config=self.tasks_config["quick_code_review"],
            agent=self.quick_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create quick review crew."""
        return Crew(
            agents=[self.quick_reviewer()],
            tasks=[self.quick_code_review()],
            process=Process.sequential,
            verbose=True,
        )
