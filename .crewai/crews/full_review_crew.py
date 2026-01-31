"""Full technical review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Full technical review crew with multiple specialized agents."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/full_review_tasks.yaml"

    def __init__(self):
        """Initialize full review crew."""
        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"FullReview using model: {self.llm.model}")

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
            max_rpm=get_rate_limiter().current_limit,
        )
