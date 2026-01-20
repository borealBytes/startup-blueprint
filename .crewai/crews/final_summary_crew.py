"""Final summary crew."""

import logging
import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FinalSummaryCrew:
    """Final summary crew."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/final_summary_tasks.yaml"

    def __init__(self):
        """Initialize final summary crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        self.model_name = os.getenv("MODEL_DEFAULT", "openrouter/xiaomi/mimo-v2-flash")
        
        # Create LLM instance with function calling
        self.llm = LLM(
            model=self.model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @agent
    def executive_summary_agent(self) -> Agent:
        """Create executive summary agent."""
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,  # Enable function calling
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def synthesize_summary(self) -> Task:
        """Synthesize final summary task."""
        return Task(
            config=self.tasks_config["synthesize_summary"],
            agent=self.executive_summary_agent(),
        )

    @crew
    def crew(self) -> Crew:
        """Create final summary crew."""
        return Crew(
            agents=[self.executive_summary_agent()],
            tasks=[self.synthesize_summary()],
            process=Process.sequential,
            verbose=True,
        )
