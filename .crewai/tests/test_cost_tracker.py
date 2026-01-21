"""Tests for CostTracker."""

import pytest
from tools.cost_tracker import CostTracker


class TestCostTracker:
    """Test suite for CostTracker."""

    def test_singleton_instance(self):
        """Test that CostTracker is a singleton."""
        tracker1 = CostTracker.get_instance()
        tracker2 = CostTracker.get_instance()
        assert tracker1 is tracker2

    def test_track_api_call(self):
        """Test tracking an API call."""
        tracker = CostTracker.get_instance()
        tracker.reset()  # Clear any previous state

        tracker.track_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.01,
        )

        summary = tracker.get_summary()
        assert summary["total_calls"] == 1
        assert summary["total_cost"] == 0.01
        assert summary["total_input_tokens"] == 100
        assert summary["total_output_tokens"] == 50

    def test_track_multiple_calls(self):
        """Test tracking multiple API calls."""
        tracker = CostTracker.get_instance()
        tracker.reset()

        tracker.track_call("gpt-4", 100, 50, 0.01)
        tracker.track_call("gpt-4", 200, 100, 0.02)
        tracker.track_call("gpt-3.5-turbo", 150, 75, 0.005)

        summary = tracker.get_summary()
        assert summary["total_calls"] == 3
        assert summary["total_cost"] == 0.035
        assert summary["total_input_tokens"] == 450
        assert summary["total_output_tokens"] == 225

    def test_get_summary_by_model(self):
        """Test getting summary grouped by model."""
        tracker = CostTracker.get_instance()
        tracker.reset()

        tracker.track_call("gpt-4", 100, 50, 0.01)
        tracker.track_call("gpt-4", 200, 100, 0.02)
        tracker.track_call("gpt-3.5-turbo", 150, 75, 0.005)

        summary = tracker.get_summary()
        assert "by_model" in summary
        assert "gpt-4" in summary["by_model"]
        assert "gpt-3.5-turbo" in summary["by_model"]

        gpt4_summary = summary["by_model"]["gpt-4"]
        assert gpt4_summary["calls"] == 2
        assert gpt4_summary["cost"] == 0.03

    def test_reset(self):
        """Test resetting the tracker."""
        tracker = CostTracker.get_instance()
        tracker.track_call("gpt-4", 100, 50, 0.01)

        tracker.reset()

        summary = tracker.get_summary()
        assert summary["total_calls"] == 0
        assert summary["total_cost"] == 0.0
        assert summary["total_input_tokens"] == 0
        assert summary["total_output_tokens"] == 0

    def test_format_summary(self):
        """Test formatting summary as string."""
        tracker = CostTracker.get_instance()
        tracker.reset()
        tracker.track_call("gpt-4", 100, 50, 0.01)

        formatted = tracker.format_summary()
        assert "gpt-4" in formatted
        assert "0.01" in formatted or "$0.01" in formatted
        assert "100" in formatted  # tokens
