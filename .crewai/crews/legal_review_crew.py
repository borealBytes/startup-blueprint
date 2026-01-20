"""Legal compliance review crew (future implementation)."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class LegalReviewCrew:
    """Legal compliance review (license, copyright, terms)."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/legal_review_tasks.yaml"

    def __init__(self):
        """Initialize legal review crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def legal_reviewer(self) -> Agent:
        """Create legal reviewer agent."""
        return Agent(
            config=self.agents_config["legal_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def legal_compliance_review(self) -> Task:
        """Perform legal compliance review."""
        return Task(
            config=self.tasks_config["legal_compliance_review"],
            agent=self.legal_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create legal review crew."""
        return Crew(
            agents=[self.legal_reviewer()],
            tasks=[self.legal_compliance_review()],
            process=Process.sequential,
            verbose=True,
        )
