"""CrewAI-based code review crew for automated pull request analysis."""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import (CommitDiffTool, CommitInfoTool,
                                FileContentTool, PRCommentTool)
from tools.related_files_tool import RelatedFilesTool

logger = logging.getLogger(__name__)


@CrewBase
class CodeReviewCrew:
    """Code review crew for GitHub commit analysis."""

    def __init__(self):
        """Initialize crew with configuration and LLM models."""
        config_dir = Path(__file__).parent / "config"

        # Load configuration from YAML
        with open(config_dir / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # Verify OpenRouter API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable required")

        # Set LiteLLM base URL for OpenRouter
        os.environ["OPENROUTER_API_KEY"] = api_key
        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Model configuration per agent
        # DeepSeek V3.2 Speciale: 685B params, optimized for agentic tool-use
        # High-compute variant with maximum reasoning and function calling reliability
        # Free on OpenRouter, proven for code review and agent workflows
        # Eliminates empty response issues seen with Qwen models
        # Use 'openrouter/' prefix to force routing through LiteLLM
        self.model_config = {
            "code_quality": os.getenv(
                "MODEL_CODE_QUALITY",
                "openrouter/deepseek/deepseek-v3.2-speciale",
            ),
            "security": os.getenv(
                "MODEL_SECURITY",
                "openrouter/deepseek/deepseek-v3.2-speciale",
            ),
            "architecture": os.getenv(
                "MODEL_ARCHITECTURE",
                "openrouter/deepseek/deepseek-v3.2-speciale",
            ),
        }

        logger.info("Model Configuration:")
        logger.info(f"  Code Quality: {self.model_config['code_quality']}")
        logger.info(f"  Security: {self.model_config['security']}")
        logger.info(f"  Architecture: {self.model_config['architecture']}")

    # Agents
    @agent
    def code_quality_reviewer(self) -> Agent:
        """Code quality reviewer agent."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[
                CommitDiffTool,
                CommitInfoTool,
                FileContentTool,
                PRCommentTool,
            ],
            llm=self.model_config["code_quality"],
            verbose=True,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Security and performance analyst agent."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[CommitDiffTool, FileContentTool],
            llm=self.model_config["security"],
            verbose=True,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Architecture and impact analyst agent."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[CommitDiffTool, FileContentTool, RelatedFilesTool],
            llm=self.model_config["architecture"],
            verbose=True,
        )

    # Tasks
    @task
    def analyze_commit_changes(self) -> Task:
        """Task: Analyze commit changes.

        Note: This is the first task, so it has no previous context.
        No need for context=[] here.
        """
        return Task(
            config=self.tasks_config["analyze_commit_changes"],
            agent=self.code_quality_reviewer(),
        )

    @task
    def security_performance_review(self) -> Task:
        """Task: Security and performance review.

        Note: context=[] prevents automatic injection of previous task outputs
        as system messages, which causes 'Unexpected role system after assistant'
        errors with Mistral API. Task still has full access to commit data via tools.
        """
        return Task(
            config=self.tasks_config["security_performance_review"],
            agent=self.security_performance_analyst(),
            context=[],  # Disable automatic context passing to avoid message ordering issues
        )

    @task
    def find_related_files(self) -> Task:
        """Task: Find related files.

        Note: context=[] prevents automatic context injection.
        Task uses RelatedFilesTool to analyze imports directly.
        """
        return Task(
            config=self.tasks_config["find_related_files"],
            agent=self.architecture_impact_analyst(),
            context=[],  # Disable automatic context passing
        )

    @task
    def analyze_related_files(self) -> Task:
        """Task: Analyze related files.

        Note: context=[] prevents automatic injection of previous task outputs
        as system messages, which causes 'Unexpected role system after assistant'
        errors with Mistral API. Task can still access find_related_files output
        via explicit task references.
        """
        return Task(
            config=self.tasks_config["analyze_related_files"],
            agent=self.architecture_impact_analyst(),
            context=[],  # Disable automatic context passing to avoid message ordering issues
        )

    @task
    def architecture_review(self) -> Task:
        """Task: Architecture review.

        Note: context=[] prevents automatic context injection.
        Task uses FileContentTool to analyze architecture directly.
        """
        return Task(
            config=self.tasks_config["architecture_review"],
            agent=self.architecture_impact_analyst(),
            context=[],  # Disable automatic context passing
        )

    @task
    def generate_executive_summary(self) -> Task:
        """Task: Generate executive summary.

        Note: context=[] prevents automatic context injection.
        Task generates final summary for PR comment.
        """
        return Task(
            config=self.tasks_config["generate_executive_summary"],
            agent=self.code_quality_reviewer(),
            context=[],  # Disable automatic context passing
        )

    @crew
    def crew(self) -> Crew:
        """Create and return the crew."""
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
                self.generate_executive_summary(),
            ],
            process=Process.sequential,
            verbose=True,
        )
