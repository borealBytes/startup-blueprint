"""Router crew for workflow orchestration."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.github_tools import CommitDiffTool, CommitInfoTool
from tools.pr_metadata_tool import PRMetadataTool
from tools.workspace_tool import WorkspaceTool

logger = logging.getLogger(__name__)


@CrewBase
class RouterCrew:
    """Router crew that decides which review workflows to execute."""

    # Use CrewBase.load_yaml() - finds config relative to project root
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks/router_tasks.yaml"

    def __init__(self):
        """Initialize router crew with config."""
        # LLM config
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY required")

        os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        self.model_name = os.getenv("CREWAI_MODEL", "google/gemini-flash-1.5")

    @agent
    def router_agent(self) -> Agent:
        """Create router agent."""
        return Agent(
            config=self.agents_config["router_agent"],
            tools=[
                PRMetadataTool(),
                CommitDiffTool(),
                CommitInfoTool(),
                WorkspaceTool(),
            ],
            llm=self.model_name,
            max_iter=5,
            verbose=True,
        )

    @task
    def analyze_and_route(self) -> Task:
        """Route workflow based on PR analysis."""
        return Task(
            config=self.tasks_config["analyze_pr_and_route"],
            agent=self.router_agent(),
        )

    @crew
    def crew(self) -> Crew:
        """Create router crew."""
        return Crew(
            agents=[self.router_agent()],
            tasks=[self.analyze_and_route()],
            process=Process.sequential,
            verbose=True,
        )
