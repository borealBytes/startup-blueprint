"""Router crew for workflow orchestration."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import CommitDiffTool, CommitInfoTool
from tools.pr_metadata_tool import PRMetadataTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class RouterCrew:
    """Router crew that decides which review workflows to execute."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/router_tasks.yaml"

    def __init__(self):
        """Initialize router crew with config."""
        # Verify OpenRouter API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        # Set LiteLLM base URL for OpenRouter
        os.environ["OPENROUTER_API_KEY"] = api_key
        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Register cost tracking callbacks (if available)
        try:
            import litellm
            from tools.cost_tracker import get_tracker

            # Import callbacks if they exist
            try:
                from crew import (litellm_failure_callback,
                                  litellm_success_callback)

                litellm.success_callback = [litellm_success_callback]
                litellm.failure_callback = [litellm_failure_callback]
                litellm.set_verbose = True
                logger.info("📊 Cost tracking callbacks registered")
            except ImportError:
                logger.debug("Cost tracking callbacks not available")
        except ImportError:
            logger.debug("LiteLLM cost tracking not available")

        # Use 'openrouter/' prefix to force routing through LiteLLM
        # Same model strategy as feat/crewai-code-review
        default_model = "openrouter/xiaomi/mimo-v2-flash"
        fallback_model = "openrouter/xiaomi/mimo-v2"  # 1M context for overflow

        self.model_name = os.getenv("MODEL_DEFAULT", default_model)
        self.fallback_model = os.getenv("MODEL_FALLBACK", fallback_model)

        logger.info("Router Model Configuration:")
        logger.info(f"  Default: {self.model_name}")
        logger.info(f"  Fallback: {self.fallback_model}")

    @agent
    def router_agent(self) -> Agent:
        """Create router agent."""
        return Agent(
            config=self.agents_config["router_agent"],
            # Tool calling conventions:
            # - @tool decorated functions: WITHOUT () (CommitDiffTool)
            # - BaseTool subclasses: WITH () (PRMetadataTool())
            tools=[
                PRMetadataTool(),   # BaseTool subclass
                CommitDiffTool,     # @tool function
                CommitInfoTool,     # @tool function
                WorkspaceTool(),    # BaseTool subclass
            ],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def analyze_and_route(self) -> Task:
        """Route workflow based on PR analysis."""
        return Task(
            config=self.tasks_config["analyze_pr_and_route"],
            agent=self.router_agent(),
        )

    @crew
    def crew(self) -> Crew:
        """Create router crew."""
        return Crew(
            agents=[self.router_agent()],
            tasks=[self.analyze_and_route()],
            process=Process.sequential,
            verbose=True,
        )
