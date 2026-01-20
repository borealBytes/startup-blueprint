"""CI log analysis crew."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.ci_output_parser_tool import CIOutputParserTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class CILogAnalysisCrew:
    """Analyzes CI logs for errors, warnings, and suggestions."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/ci_log_analysis_tasks.yaml"

    def __init__(self):
        """Initialize CI log analysis crew."""
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
    def ci_analyst(self) -> Agent:
        """Create CI analyst agent."""
        return Agent(
            config=self.agents_config["ci_analyst"],
            # BaseTool subclasses need instantiation
            tools=[CIOutputParserTool(), WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def analyze_ci_logs(self) -> Task:
        """Analyze CI logs."""
        return Task(
            config=self.tasks_config["parse_ci_output"],
            agent=self.ci_analyst(),
        )

    @crew
    def crew(self) -> Crew:
        """Create CI log analysis crew."""
        return Crew(
            agents=[self.ci_analyst()],
            tasks=[self.analyze_ci_logs()],
            process=Process.sequential,
            verbose=True,
        )
