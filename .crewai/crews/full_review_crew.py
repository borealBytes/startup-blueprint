"""Full technical review crew."""

import logging
import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Full technical review crew with multiple specialized agents."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/full_review_tasks.yaml"

    def __init__(self):
        """Initialize full review crew."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        # Register Trinity model as function-calling capable
        # OpenRouter supports it, but LiteLLM doesn't recognize it by default
        from utils.model_config import register_trinity_model

        register_trinity_model()

        self.model_name = os.getenv("MODEL_DEFAULT", "openrouter/google/gemini-2.0-flash-exp")

        # Create LLM instance with function calling
        self.llm = LLM(
            model=self.model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @agent
    def code_quality_reviewer(self) -> Agent:
        """Create code quality reviewer agent."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Create security and performance analyst agent."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Create architecture and impact analyst agent."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def analyze_commit_changes(self) -> Task:
        """Analyze commit changes task."""
        # CRITICAL: Task name must match YAML key
        return Task(
            config=self.tasks_config["full_technical_review"],  # Match YAML
            agent=self.code_quality_reviewer(),
        )

    @task
    def security_deep_dive(self) -> Task:
        """Security deep dive task."""
        return Task(
            config=self.tasks_config["security_deep_dive"],  # Match YAML
            agent=self.security_performance_analyst(),
        )

    @crew
    def crew(self) -> Crew:
        """Create full review crew."""
        return Crew(
            agents=[
                self.code_quality_reviewer(),
                self.security_performance_analyst(),
                # architecture_impact_analyst reserved for future
            ],
            tasks=[
                self.analyze_commit_changes(),
                self.security_deep_dive(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=10,  # Rate limit: OpenRouter free tier allows 20 RPM, use 10 to be safe
        )
