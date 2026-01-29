"""Router crew for workflow orchestration."""

import logging
import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

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

            # Register Trinity model as function-calling capable
            # OpenRouter supports it, but LiteLLM doesn't recognize it by default
            from utils.model_config import register_trinity_model

            register_trinity_model()

            # Import callbacks if they exist
            try:
                from crew import litellm_failure_callback, litellm_success_callback

                litellm.success_callback = [litellm_success_callback]
                litellm.failure_callback = [litellm_failure_callback]
                litellm.set_verbose = True
                logger.info("📊 Cost tracking callbacks registered")
            except ImportError:
                logger.debug("Cost tracking callbacks not available")
        except ImportError:
            logger.debug("LiteLLM cost tracking not available")

        # Use 'openrouter/' prefix to force routing through LiteLLM
        default_model = "openrouter/google/gemini-2.5-flash-lite"
        fallback_model = "openrouter/xiaomi/mimo-v2"  # 1M context for overflow

        self.model_name = os.getenv("MODEL_DEFAULT", default_model)
        self.fallback_model = os.getenv("MODEL_FALLBACK", fallback_model)

        logger.info("Router Model Configuration:")
        logger.info(f"  Default: {self.model_name}")
        logger.info(f"  Fallback: {self.fallback_model}")

        # Create LLM instance with function calling enabled
        self.llm = LLM(
            model=self.model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @agent
    def router_agent(self) -> Agent:
        """Create router agent with function calling enabled.

        IMPORTANT: The GitHub workflow has already prepared all data files
        (diff.txt, commits.json, diff.json) in the workspace. The router
        only needs WorkspaceTool to read these pre-prepared files.
        """
        return Agent(
            config=self.agents_config["router_agent"],
            tools=[WorkspaceTool()],  # Only need workspace tool - data is pre-prepared
            llm=self.llm,  # Use LLM instance
            function_calling_llm=self.llm,  # CRITICAL: Enable function calling
            max_iter=10,  # Allow more iterations for tool use
            verbose=True,
            allow_delegation=False,  # Don't delegate to other agents
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
            max_rpm=10,  # Rate limit: OpenRouter free tier allows 20 RPM, use 10 to be safe
        )
