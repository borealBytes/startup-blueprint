"""Quick review crew."""

import logging
import os
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Quick review crew."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/quick_review_tasks.yaml"

    def __init__(self):
        """Initialize quick review crew."""
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

        # Get workspace path (absolute)
        self.workspace_dir = (Path(__file__).parent.parent / "workspace").resolve()

    @agent
    def quick_reviewer(self) -> Agent:
        """Create quick reviewer agent."""
        return Agent(
            config=self.agents_config["quick_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,  # Enable function calling
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def quick_code_review(self) -> Task:
        """Quick code review task."""
        # CRITICAL: Set output_json with full path to force file creation
        output_file = str(self.workspace_dir / "quick_review.json")
        
        return Task(
            config=self.tasks_config["quick_code_review"],
            agent=self.quick_reviewer(),
            output_json=output_file,  # Force JSON output to file
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
