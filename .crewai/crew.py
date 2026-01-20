"""CrewAI-based code review crew for automated pull request analysis."""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.cost_tracker import get_tracker
from tools.github_tools import (CommitDiffTool, CommitInfoTool,
                                FileContentTool, PRCommentTool)
from tools.related_files_tool import RelatedFilesTool

logger = logging.getLogger(__name__)


def litellm_success_callback(kwargs, completion_response, start_time, end_time):
    """Callback for successful LiteLLM API calls.

    Args:
        kwargs: Request arguments (model, messages, etc.)
        completion_response: LiteLLM ModelResponse object
        start_time: Request start timestamp
        end_time: Request end timestamp
    """
    try:
        tracker = get_tracker()

        # Extract model name
        model = kwargs.get("model", "unknown")

        # Extract usage from response
        # LiteLLM returns a ModelResponse object with usage attribute
        tokens_in = 0
        tokens_out = 0
        cost = None  # Initialize as None to detect missing data
        generation_id = None

        # Try to get usage from response object
        if hasattr(completion_response, "usage"):
            usage = completion_response.usage
            if usage:
                tokens_in = getattr(usage, "prompt_tokens", 0)
                tokens_out = getattr(usage, "completion_tokens", 0)
                # FIX 1: Check for cost in usage object first
                cost = getattr(usage, "cost", None)
                logger.debug(f"🔍 LiteLLM callback: {model} - {tokens_in} in, {tokens_out} out, cost={cost}")

        # FIX 1: Check for cost attribute directly on response (most common location)
        if cost is None and hasattr(completion_response, "cost"):
            cost = completion_response.cost
            logger.debug(f"🔍 Got cost from response.cost: {cost}")

        # FIX 1: Check for cost in _hidden_params (legacy fallback)
        if cost is None and hasattr(completion_response, "_hidden_params"):
            hidden = completion_response._hidden_params
            if isinstance(hidden, dict):
                cost = hidden.get("response_cost", None)
                # OpenRouter may provide generation_id
                generation_id = hidden.get("generation_id")
                if cost is not None:
                    logger.debug(f"🔍 Got cost from _hidden_params: {cost}")

        # Fallback: try to access as dict
        if tokens_in == 0 and isinstance(completion_response, dict):
            usage_dict = completion_response.get("usage", {})
            tokens_in = usage_dict.get("prompt_tokens", 0)
            tokens_out = usage_dict.get("completion_tokens", 0)
            if cost is None and "cost" in usage_dict:
                cost = usage_dict.get("cost")
                logger.debug(f"🔍 Got cost from dict usage: {cost}")

        # Handle None cost to prevent formatting errors
        if cost is None:
            logger.warning(
                f"⚠️  Cost data missing from LiteLLM response for model {model}. "
                f"Enrichment fallback will be used."
            )
            cost = 0.0  # Default to zero, enrichment will fill it
        else:
            # FIX: Add type safety - convert to float and handle errors
            try:
                cost_float = float(cost)
                logger.debug(f"✅ Cost captured: ${cost_float:.6f}")
                cost = cost_float
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"⚠️  Invalid cost type: {type(cost)} = {cost}. "
                    f"Error: {e}. Defaulting to 0.0"
                )
                cost = 0.0

        # Calculate duration in seconds (FIX: convert timedelta to float)
        duration = end_time - start_time
        duration_seconds = (
            duration.total_seconds() if hasattr(duration, "total_seconds") else float(duration)
        )

        # Only log if we got meaningful data
        if tokens_in > 0 or tokens_out > 0:
            # FIX: Safe cost formatting with guaranteed float
            try:
                logger.info(
                    f"✅ Captured API call: {model} "
                    f"({tokens_in} in, {tokens_out} out, ${cost:.6f})"
                )
            except (ValueError, TypeError):
                logger.info(
                    f"✅ Captured API call: {model} "
                    f"({tokens_in} in, {tokens_out} out, cost={cost})"
                )

            tracker.log_api_call(
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                duration_seconds=duration_seconds,
                generation_id=generation_id,
            )
        else:
            logger.warning(
                f"⚠️  No usage data in response for {model}. "
                f"Response type: {type(completion_response)}"
            )
            # Log with zeros to track that a call happened
            tracker.log_api_call(
                model=model,
                tokens_in=0,
                tokens_out=0,
                cost=0.0,
                duration_seconds=duration_seconds,
                generation_id=generation_id,
            )

    except Exception as e:
        logger.error(f"❌ Error in cost tracking callback: {e}", exc_info=True)


def litellm_failure_callback(kwargs, completion_response, start_time, end_time):
    """Callback for failed LiteLLM API calls.

    Args:
        kwargs: Request arguments
        completion_response: Error response
        start_time: Request start time
        end_time: Request end time
    """
    model = kwargs.get("model", "unknown")
    duration = end_time - start_time
    duration_seconds = (
        duration.total_seconds() if hasattr(duration, "total_seconds") else float(duration)
    )
    logger.warning(f"⚠️  API call failed for {model} after {duration_seconds:.2f}s")


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

        # Register cost tracking callbacks
        # Must be done BEFORE any LiteLLM calls
        import litellm

        # Set callbacks - must be lists
        litellm.success_callback = [litellm_success_callback]
        litellm.failure_callback = [litellm_failure_callback]

        # Enable detailed logging from LiteLLM
        litellm.set_verbose = True

        logger.info("📊 Cost tracking callbacks registered")

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
    # FIX 2: Remove tracker.set_current_task() from here - it runs at task DEFINITION time,
    # not EXECUTION time. Task names will be set in main.py during actual execution.

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
