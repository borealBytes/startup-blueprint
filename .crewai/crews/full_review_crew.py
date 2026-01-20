"""Full review crew for deep technical analysis."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Comprehensive code quality, security, and architecture review."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/full_review_tasks.yaml"

    def __init__(self):
        """Initialize full review crew."""
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
    def code_quality_reviewer(self) -> Agent:
        """Create code quality reviewer."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Create security and performance analyst."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Create architecture analyst."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def review_code_quality(self) -> Task:
        """Review code quality."""
        return Task(
            config=self.tasks_config["review_code_quality"],
            agent=self.code_quality_reviewer(),
        )

    @task
    def analyze_security_performance(self) -> Task:
        """Analyze security and performance."""
        return Task(
            config=self.tasks_config["analyze_security_performance"],
            agent=self.security_performance_analyst(),
        )

    @task
    def analyze_architecture_impact(self) -> Task:
        """Analyze architecture impact."""
        return Task(
            config=self.tasks_config["analyze_architecture_impact"],
            agent=self.architecture_impact_analyst(),
        )

    @crew
    def crew(self) -> Crew:
        """Create full review crew."""
        return Crew(
            agents=[
                self.code_quality_reviewer(),
                self.security_performance_analyst(),
                self.architecture_impact_analyst(),
            ],
            tasks=[
                self.review_code_quality(),
                self.analyze_security_performance(),
                self.analyze_architecture_impact(),
            ],
            process=Process.sequential,
            verbose=True,
        )
