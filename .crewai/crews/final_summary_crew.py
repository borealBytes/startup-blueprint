"""Final summary crew that synthesizes all review outputs."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FinalSummaryCrew:
    """Synthesizes all review outputs into final markdown report."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/final_summary_tasks.yaml"

    def __init__(self):
        """Initialize final summary crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def summarizer(self) -> Agent:
        """Create summarizer agent."""
        return Agent(
            config=self.agents_config["summarizer"],
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def synthesize_summary(self) -> Task:
        """Synthesize final summary."""
        return Task(
            config=self.tasks_config["synthesize_summary"],
            agent=self.summarizer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create final summary crew."""
        return Crew(
            agents=[self.summarizer()],
            tasks=[self.synthesize_summary()],
            process=Process.sequential,
            verbose=True,
        )
