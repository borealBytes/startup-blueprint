"""Legal compliance review crew (stub for future)."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class LegalReviewCrew:
    """Legal compliance review (stub - not yet implemented)."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/legal_review_tasks.yaml"

    def __init__(self):
        """Initialize legal review crew."""
        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"LegalReview using model: {self.llm.model}")

    @agent
    def legal_compliance_reviewer(self) -> Agent:
        """Create legal compliance reviewer."""
        return Agent(
            config=self.agents_config["legal_compliance_reviewer"],
            # BaseTool subclasses need instantiation
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=3,
            verbose=True,
        )

    @task
    def review_legal_compliance(self) -> Task:
        """Review legal compliance (stub)."""
        return Task(
            config=self.tasks_config["review_legal_compliance"],
            agent=self.legal_compliance_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create legal review crew."""
        return Crew(
            agents=[self.legal_compliance_reviewer()],
            tasks=[self.review_legal_compliance()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
