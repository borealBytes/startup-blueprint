"""Quick review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Quick review crew."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/quick_review_tasks.yaml"

    def __init__(self):
        """Initialize quick review crew."""
        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"QuickReview using model: {self.llm.model}")

    @agent
    def quick_reviewer(self) -> Agent:
        """Create quick reviewer agent."""
        return Agent(
            config=self.agents_config["quick_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,  # Enable function calling
            max_iter=15,  # Increased from 10 to allow more tool calls
            verbose=True,
            allow_delegation=False,
        )

    @task
    def quick_code_review(self) -> Task:
        """Quick code review task."""
        #CRITICAL: Do NOT use expected_output from config - agent copies it without working
        # Instead, agent MUST write quick_review.json via WorkspaceTool
        # Validation happens by checking if file exists, not by matching output text
        task_config = self.tasks_config["quick_code_review"].copy()
        # Remove expected_output to prevent agent from copying template
        task_config.pop("expected_output", None)
        
        return Task(
            description=task_config["description"],
            agent=self.quick_reviewer(),
            expected_output="Write quick_review.json to workspace. Confirm with: 'Written quick_review.json'",
        )

    @crew
    def crew(self) -> Crew:
        """Create quick review crew."""
        return Crew(
            agents=[self.quick_reviewer()],
            tasks=[self.quick_code_review()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
