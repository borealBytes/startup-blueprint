"""Quick review crew for fast code checks."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Quick code quality review crew."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/quick_review_tasks.yaml"

    def __init__(self):
        """Initialize quick review crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_KEY"] = api_key
        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Register cost tracking callbacks (if available)
        try:
            import litellm

            try:
                from crew import (litellm_failure_callback,
                                  litellm_success_callback)

                litellm.success_callback = [litellm_success_callback]
                litellm.failure_callback = [litellm_failure_callback]
                litellm.set_verbose = True
            except ImportError:
                pass
        except ImportError:
            pass

        # Use openrouter/ prefix
        default_model = "openrouter/xiaomi/mimo-v2-flash"
        self.model_name = os.getenv("MODEL_DEFAULT", default_model)

    @agent
    def quick_reviewer(self) -> Agent:
        """Create quick reviewer agent."""
        return Agent(
            config=self.agents_config["quick_reviewer"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def quick_code_review(self) -> Task:
        """Quick code review task."""
        return Task(
            config=self.tasks_config["quick_code_check"],
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
