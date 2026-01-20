"""Final summary crew - synthesizes all review outputs."""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FinalSummaryCrew:
    """Final summary crew - reads all workspace outputs and creates report."""

    def __init__(self):
        """Initialize final summary crew."""
        config_dir = Path(__file__).parent.parent / "config"

        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks" / "final_summary_tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # LLM config
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def synthesizer(self) -> Agent:
        """Create synthesizer agent."""
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            tools=[WorkspaceTool()],  # Only needs to read workspace
            llm=self.model_name,
            max_iter=10,  # Higher for synthesis
            verbose=True,
        )

    @task
    def synthesize_all_reviews(self) -> Task:
        """Synthesize all reviews into final report."""
        return Task(
            config=self.tasks_config["synthesize_all_reviews"],
            agent=self.synthesizer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create final summary crew."""
        return Crew(
            agents=[self.synthesizer()],
            tasks=[self.synthesize_all_reviews()],
            process=Process.sequential,
            verbose=True,
        )
