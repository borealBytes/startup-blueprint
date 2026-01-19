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

        # Multi-model strategy for optimal performance and reliability
        # - Xiaomi Mimo V2 Flash: Fast, efficient for simple analysis tasks
        # - ByteDance SEED 1.6: Better for complex reasoning and larger context
        # - Qwen Plus Thinking: Fallback for context overflow (400 errors)

        # Use 'openrouter/' prefix to force routing through LiteLLM
        self.model_config = {
            # Quick tasks: code quality, security, summary
            "fast": os.getenv(
                "MODEL_FAST",
                "openrouter/xiaomi/mimo-v2-flash",
            ),
            # Complex tasks: related files, architecture
            "complex": os.getenv(
                "MODEL_COMPLEX",
                "openrouter/bytedance-seed/seed-1.6",
            ),
            # Fallback for context overflow
            "fallback": os.getenv(
                "MODEL_FALLBACK",
                "openrouter/qwen/qwen-plus-2025-07-28:thinking",
            ),
        }

        # Add max_tokens to prevent oversized responses
        self.llm_config = {
            "max_tokens": 4000,
            "temperature": 0.1,  # Lower temperature for more focused responses
        }

        logger.info("Model Configuration:")
        logger.info(f"  Fast (Tasks 1,2,6): {self.model_config['fast']}")
        logger.info(f"  Complex (Tasks 3-5): {self.model_config['complex']}")
        logger.info(f"  Fallback: {self.model_config['fallback']}")
        logger.info(f"  Max Tokens: {self.llm_config['max_tokens']}")

    def _create_llm_config(self, model_key: str) -> dict:
        """Create LLM configuration with fallback support."""
        config = {"model": self.model_config[model_key], **self.llm_config}
        return config

    # Agents
    @agent
    def code_quality_reviewer(self) -> Agent:
        """Code quality reviewer agent - uses fast model."""
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[
                CommitDiffTool,
                CommitInfoTool,
                FileContentTool,
                PRCommentTool,
            ],
            llm=self.model_config["fast"],
            max_iter=5,  # Limit iterations to prevent runaway loops
            verbose=True,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        """Security and performance analyst agent - uses fast model."""
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[CommitDiffTool, FileContentTool],
            llm=self.model_config["fast"],
            max_iter=5,
            verbose=True,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        """Architecture and impact analyst agent - uses complex model for deep analysis."""
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[CommitDiffTool, FileContentTool, RelatedFilesTool],
            llm=self.model_config["complex"],
            max_iter=5,
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
        Uses complex model (ByteDance SEED) for better reasoning.
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
        Uses complex model for deep analysis.
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
        Uses complex model for architectural reasoning.
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
        Uses fast model for quick summarization.
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
            max_rpm=10,  # Rate limit to 10 requests per minute to avoid quota issues
        )
