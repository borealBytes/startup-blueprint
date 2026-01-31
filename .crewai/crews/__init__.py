"""CrewAI crews for modular review workflows."""

# CRITICAL: Register Trinity model BEFORE importing any crew classes
# CrewAI checks model capabilities during class decoration, so this must happen first
from utils.model_config import register_trinity_model

register_trinity_model()

from crews.ci_log_analysis_crew import CILogAnalysisCrew
from crews.final_summary_crew import FinalSummaryCrew
from crews.full_review_crew import FullReviewCrew
from crews.legal_review_crew import LegalReviewCrew
from crews.quick_review_crew import QuickReviewCrew
from crews.router_crew import RouterCrew

__all__ = [
    "RouterCrew",
    "CILogAnalysisCrew",
    "QuickReviewCrew",
    "FullReviewCrew",
    "LegalReviewCrew",
    "FinalSummaryCrew",
]
