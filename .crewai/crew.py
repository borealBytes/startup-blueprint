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

        # Simplified model strategy using Xiaomi Mimo V2 family:
        # - Mimo V2 Flash: Fast, efficient, 128k context (default for all tasks)
        # - Mimo V2: Full model with 1M context (fallback for overflow)

        # Use 'openrouter/' prefix to force routing through LiteLLM
        default_model = "openrouter/xiaomi/mimo-v2-flash"
        fallback_model = "openrouter/xiaomi/mimo-v2"  # 1M context for overflow

        self.model_config = {
            # Primary model for all tasks
            "default": os.getenv("MODEL_DEFAULT", default_model),
            # Fallback for context overflow (uses full 1M context)
            "fallback": os.getenv("MODEL_FALLBACK", fallback_model),
        }

        # Add max_tokens to prevent oversized responses
        self.llm_config = {
            "max_tokens": 4000,
            "temperature": 0.05,  # Very low temperature for consistent, focused output
        }

        logger.info("Model Configuration:")
        logger.info(f"  Default (All Tasks): {self.model_config['default']}")
        logger.info(f"  Fallback (Overflow): {self.model_config['fallback']}")
        logger.info(f"  Max Tokens: {self.llm_config['max_tokens']}")
        logger.info(f"  Temperature: {self.llm_config['temperature']}")

    def _create_llm_config(self, model_key: str) -> dict:
        """Create LLM configuration with fallback support."""
        config = {"model": self.model_config[model_key], **self.llm_config}
        return config

    # Agents
    @agent
    def code_quality_reviewer(self) -> Agent:
        """Code quality reviewer agent - uses default model."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[
                CommitDiffTool,
                CommitInfoTool,
                FileContentTool,
                PRCommentTool,
            ],
            llm=self.model_config["default"],
            max_iter=5,  # Limit iterations to prevent runaway loops
            verbose=True,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Security and performance analyst agent - uses default model."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[CommitDiffTool, FileContentTool],
            llm=self.model_config["default"],
            max_iter=5,
            verbose=True,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Architecture and impact analyst agent - uses default model."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[CommitDiffTool, FileContentTool, RelatedFilesTool],
            llm=self.model_config["default"],
            max_iter=5,
            verbose=True,
        )

    @agent
    def executive_summary_agent(self) -> Agent:
        """Executive summary agent - synthesizes findings from all previous tasks.

        This agent has NO tools - it only receives context from previous tasks
        and synthesizes them into a final markdown report. This prevents it from
        trying to re-fetch data and hitting iteration limits.
        """
        return Agent(
            config=self.agents_config["code_quality_reviewer"],  # Reuse config
            tools=[],  # NO TOOLS - only synthesize previous outputs
            llm=self.model_config["default"],
            max_iter=10,  # Higher limit for synthesis iterations
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

        CRITICAL: Context will be manually injected in main.py with CLEAN outputs only.
        DO NOT add context=[] here - it will be set during manual orchestration.

        The dedicated executive_summary_agent has NO tools, preventing it from
        trying to re-fetch data and hitting iteration limits.
        """
        return Task(
            config=self.tasks_config["generate_executive_summary"],
            agent=self.executive_summary_agent(),
            # NO context parameter - will be manually set with clean outputs
        )

    @crew
    def crew(self) -> Crew:
        """Create and return the crew."""
        return Crew(
            agents=[
                self.code_quality_reviewer(),
                self.security_performance_analyst(),
                self.architecture_impact_analyst(),
                self.executive_summary_agent(),  # Add new synthesis agent
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
            max_rpm=10,  # Rate limit to 10 requests per minute to avoid quota issues
        )
