"""Full technical review crew - deep analysis workflow."""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Full technical review crew (runs when crewai:full-review label present)."""

    def __init__(self):
        """Initialize full review crew."""
        config_dir = Path(__file__).parent.parent / "config"

        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks" / "full_review_tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # LLM config
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def code_quality_reviewer(self) -> Agent:
        """Code quality reviewer agent."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[
                WorkspaceTool(),  # Read from workspace
                FileContentTool(),  # Only if needed
            ],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Security and performance analyst agent."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[WorkspaceTool(), FileContentTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Architecture and impact analyst agent."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[WorkspaceTool(), FileContentTool(), RelatedFilesTool()],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def analyze_commit_changes(self) -> Task:
        """Task: Deep commit analysis."""
        return Task(
            config=self.tasks_config["analyze_commit_changes"],
            agent=self.code_quality_reviewer(),
        )

    @task
    def security_performance_review(self) -> Task:
        """Task: Security and performance review."""
        return Task(
            config=self.tasks_config["security_performance_review"],
            agent=self.security_performance_analyst(),
        )

    @task
    def find_related_files(self) -> Task:
        """Task: Find related files."""
        return Task(
            config=self.tasks_config["find_related_files"],
            agent=self.architecture_impact_analyst(),
        )

    @task
    def analyze_related_files(self) -> Task:
        """Task: Analyze related files."""
        return Task(
            config=self.tasks_config["analyze_related_files"],
            agent=self.architecture_impact_analyst(),
        )

    @task
    def architecture_review(self) -> Task:
        """Task: Architecture review."""
        return Task(
            config=self.tasks_config["architecture_review"],
            agent=self.architecture_impact_analyst(),
        )

    @task
    def generate_full_review_summary(self) -> Task:
        """Task: Generate full review summary."""
        return Task(
            config=self.tasks_config["generate_full_review_summary"],
            agent=self.code_quality_reviewer(),
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
                self.analyze_commit_changes(),
                self.security_performance_review(),
                self.find_related_files(),
                self.analyze_related_files(),
                self.architecture_review(),
                self.generate_full_review_summary(),
            ],
            process=Process.sequential,
            verbose=True,
        )
