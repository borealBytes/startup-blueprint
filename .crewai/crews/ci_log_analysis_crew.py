"""CI log analysis crew."""

import logging
import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.ci_output_parser_tool import CIOutputParserTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class CILogAnalysisCrew:
    """CI log analysis crew."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/ci_log_analysis_tasks.yaml"

    def __init__(self):
        """Initialize CI log analysis crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        # Register Trinity model as function-calling capable
        # OpenRouter supports it, but LiteLLM doesn't recognize it by default
        from utils.model_config import register_trinity_model

        register_trinity_model()

        self.model_name = os.getenv("MODEL_DEFAULT", "openrouter/google/gemini-2.0-flash-exp:free")

        # Create LLM instance with function calling
        self.llm = LLM(
            model=self.model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @agent
    def ci_analyst(self) -> Agent:
        """Create CI analyst agent."""
        return Agent(
            config=self.agents_config["ci_analyst"],
            tools=[
                CIOutputParserTool(),
                WorkspaceTool(),
            ],
            llm=self.llm,
            function_calling_llm=self.llm,  # Enable function calling
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def analyze_ci_logs(self) -> Task:
        """Analyze CI logs task."""
        # Use output_file (not output_json) - CrewAI writes string content to file
        # Agent returns JSON as string, CrewAI writes it to ci_summary.json
        return Task(
            config=self.tasks_config["parse_ci_output"],
            agent=self.ci_analyst(),
            output_file="ci_summary.json",  # Direct file write
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
