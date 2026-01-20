"""Cost tracking for LiteLLM API calls during CrewAI execution."""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class APICallMetrics:
    """Metrics for a single API call."""

    call_number: int
    task_name: str
    model: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    cost: float
    duration_seconds: float
    tokens_per_second: float
    timestamp: float

    def __str__(self) -> str:
        """Format metrics as a table row."""
        return (
            f"| {self.call_number} "
            f"| {self.task_name} "
            f"| {self.model} "
            f"| {self.tokens_in:,} "
            f"| {self.tokens_out:,} "
            f"| {self.total_tokens:,} "
            f"| ${self.cost:.6f} "
            f"| {self.tokens_per_second:.1f} |"
        )


class CostTracker:
    """Track costs and metrics for all LiteLLM API calls."""

    def __init__(self):
        """Initialize cost tracker."""
        self.calls: List[APICallMetrics] = []
        self.current_task: Optional[str] = None
        self.call_counter = 0
        self.start_times = {}  # Track start time per call
        logger.info("📊 Cost tracker initialized")

    def set_current_task(self, task_name: str):
        """Set the current task name for associating API calls."""
        self.current_task = task_name
        logger.info(f"🏷️  Tracking costs for: {task_name}")

    def log_api_call(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        duration_seconds: float,
    ):
        """Log metrics for a single API call.

        Args:
            model: Model name (e.g., 'xiaomi/mimo-v2-flash')
            tokens_in: Input tokens (prompt)
            tokens_out: Output tokens (completion)
            cost: Cost in USD
            duration_seconds: Call duration in seconds
        """
        self.call_counter += 1
        total_tokens = tokens_in + tokens_out

        # Calculate tokens per second
        tokens_per_second = total_tokens / duration_seconds if duration_seconds > 0 else 0

        # Use current task or "Unknown" if not set
        task_name = self.current_task or "Unknown"

        metrics = APICallMetrics(
            call_number=self.call_counter,
            task_name=task_name,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            total_tokens=total_tokens,
            cost=cost,
            duration_seconds=duration_seconds,
            tokens_per_second=tokens_per_second,
            timestamp=time.time(),
        )

        self.calls.append(metrics)

        logger.debug(
            f"💸 Call #{self.call_counter}: {model} "
            f"({tokens_in:,} in, {tokens_out:,} out, "
            f"${cost:.6f}, {tokens_per_second:.1f} tok/s)"
        )

    def get_total_cost(self) -> float:
        """Get total cost across all API calls."""
        return sum(call.cost for call in self.calls)

    def get_total_tokens(self) -> int:
        """Get total tokens (in + out) across all API calls."""
        return sum(call.total_tokens for call in self.calls)

    def get_total_tokens_in(self) -> int:
        """Get total input tokens across all API calls."""
        return sum(call.tokens_in for call in self.calls)

    def get_total_tokens_out(self) -> int:
        """Get total output tokens across all API calls."""
        return sum(call.tokens_out for call in self.calls)

    def get_average_tokens_per_second(self) -> float:
        """Get average tokens per second across all API calls."""
        if not self.calls:
            return 0.0
        return sum(call.tokens_per_second for call in self.calls) / len(self.calls)

    def format_as_markdown_table(self) -> str:
        """Format all metrics as a markdown table.

        Returns:
            Markdown-formatted table string
        """
        if not self.calls:
            return "_No API calls recorded_"

        lines = [
            "| # | Task | Model | Tokens In | Tokens Out | Total | Cost | Tok/Sec |",
            "|---|------|-------|-----------|------------|-------|------|---------|",
        ]

        # Add each call
        for call in self.calls:
            lines.append(str(call))

        # Add totals row
        lines.append(
            f"| **TOTAL** | **{len(self.calls)} calls** | - "
            f"| **{self.get_total_tokens_in():,}** "
            f"| **{self.get_total_tokens_out():,}** "
            f"| **{self.get_total_tokens():,}** "
            f"| **${self.get_total_cost():.6f}** "
            f"| **{self.get_average_tokens_per_second():.1f}** |"
        )

        return "\n".join(lines)

    def format_summary(self) -> str:
        """Format a brief summary of costs.

        Returns:
            Human-readable summary string
        """
        if not self.calls:
            return "No API calls recorded"

        return (
            f"📊 Total API Calls: {len(self.calls)}\n"
            f"💰 Total Cost: ${self.get_total_cost():.6f}\n"
            f"🔢 Total Tokens: {self.get_total_tokens():,} "
            f"({self.get_total_tokens_in():,} in, {self.get_total_tokens_out():,} out)\n"
            f"⚡ Average Speed: {self.get_average_tokens_per_second():.1f} tokens/sec"
        )


# Global tracker instance
_global_tracker: Optional[CostTracker] = None


def get_tracker() -> CostTracker:
    """Get or create the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def reset_tracker():
    """Reset the global tracker (useful for testing)."""
    global _global_tracker
    _global_tracker = CostTracker()
