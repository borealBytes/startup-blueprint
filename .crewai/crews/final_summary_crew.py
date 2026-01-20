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

        os.environ["OPENROUTER_API_KEY"] = api_key
        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Register cost tracking callbacks (if available)
        try:
            import litellm

            try:
                from crew import litellm_failure_callback, litellm_success_callback

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
    def executive_summary_agent(self) -> Agent:
        """Create executive summary agent.
        
        IMPORTANT: Method name must match the agent key in agents.yaml.
        """
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=3,
            verbose=True,
        )

    @task
    def synthesize_summary(self) -> Task:
        """Synthesize final summary.
        
        IMPORTANT: Method name must match the task key in tasks YAML.
        """
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
