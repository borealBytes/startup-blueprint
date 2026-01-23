"""CrewAI code review package."""

__version__ = "0.1.0"
__author__ = "Clayton Young"

try:
    from .crew import CodeReviewCrew
except ImportError:
    # Fallback for when running as a script or top-level module (e.g. pytest from inside dir)
    from crew import CodeReviewCrew

__all__ = ["CodeReviewCrew"]
