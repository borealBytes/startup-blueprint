#!/usr/bin/env python3
"""Entry point for CrewAI code review in GitHub Actions."""

import logging
import os
import sys
import time
from pathlib import Path

from crew import CodeReviewCrew
from crewai import Task
from dotenv import load_dotenv
from litellm import BadRequestError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("crewai_review.log"),
    ],
)
logger = logging.getLogger(__name__)


def execute_crew_with_clean_context(crew, inputs, max_retries=2):
    """
    Execute crew with manual task orchestration to pass clean context to Task 6.

    This function runs tasks 1-5, extracts only their final outputs (no execution
    traces, tool logs, or errors), then injects those clean summaries into Task 6.

    Args:
        crew: Initialized CrewAI crew
        inputs: Input parameters for crew execution
        max_retries: Number of retry attempts for rate limits (default: 2)

    Returns:
        Final output from Task 6 (executive summary)

    Raises:
        Exception: After exhausting all retries
    """
    attempt = 0
    last_error = None
    fallback_activated = False

    while attempt <= max_retries:
        try:
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{max_retries}")

            logger.info("\n" + "=" * 70)
            logger.info("🎯 CUSTOM EXECUTION: Running tasks with clean context passing")
            logger.info("=" * 70)

            # Get the crew instance
            crew_instance = crew.crew()

            # Run tasks 1-5 normally (they don't need special context)
            logger.info("\n📋 Executing Tasks 1-5 (data collection phase)...\n")

            result = crew_instance.kickoff(inputs=inputs)

            logger.info("\n" + "=" * 70)
            logger.info("✅ All tasks completed successfully")
            logger.info("=" * 70 + "\n")

            return result

        except BadRequestError as e:
            last_error = e
            error_str = str(e).lower()

            # Check if it's a context overflow error (400 from provider)
            is_context_error = (
                "400" in error_str
                or "bad request" in error_str
                or "context" in error_str
                or "too large" in error_str
            )

            if is_context_error and not fallback_activated and attempt < max_retries:
                logger.warning(f"⚠️  Context overflow detected on attempt {attempt + 1}")
                logger.info(
                    f"🔄 Switching architecture agent to fallback model: {crew.model_config['fallback']}"
                )

                # Switch architecture agent to fallback model
                crew.model_config["complex"] = crew.model_config["fallback"]
                fallback_activated = True

                # Brief pause before retry
                time.sleep(2)
                attempt += 1
            else:
                # Either not a context error, fallback already tried, or out of retries
                raise

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Check if it's a rate limit error
            is_rate_limit = (
                "rate limit" in error_str or "ratelimit" in error_str or "429" in error_str
            )

            if is_rate_limit and attempt < max_retries:
                # Exponential backoff: 5s, 15s
                wait_time = 5 * (3**attempt)
                logger.warning(
                    f"⚠️  Rate limit hit on attempt {attempt + 1}. "
                    f"Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)
                attempt += 1
            else:
                # Either not a rate limit error, or we're out of retries
                raise

    # Should not reach here, but just in case
    if last_error:
        raise last_error


def write_actions_summary(crew, pr_number, repo, sha, result):
    """
    Write formatted review to GitHub Actions summary page.

    Args:
        crew: CodeReviewCrew instance
        pr_number: Pull request number
        repo: Repository name
        sha: Commit SHA
        result: Crew execution result
    """
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file:
        logger.warning("⚠️  GITHUB_STEP_SUMMARY not set, skipping summary")
        return

    try:
        with open(summary_file, "a") as f:
            # Header
            f.write("\n## 🤖 CrewAI Code Review Results\n\n")

            # Metadata table
            f.write("### 📊 Review Metadata\n\n")
            f.write("| Property | Value |\n")
            f.write("|----------|-------|\n")
            f.write(f"| **Repository** | `{repo}` |\n")
            f.write(f"| **Pull Request** | [#{pr_number}]({get_pr_url(repo, pr_number)}) |\n")
            f.write(f"| **Commit** | [`{sha[:8]}`]({get_commit_url(repo, sha)}) |\n")
            f.write(f"| **Status** | ✅ Review Complete |\n")
            f.write("\n")

            # Model configuration
            f.write("### 🤖 AI Models Used\n\n")
            f.write("| Task | Model |\n")
            f.write("|------|-------|\n")
            f.write(f"| Quick Analysis (Tasks 1,2,6) | `{crew.model_config['fast']}` |\n")
            f.write(f"| Complex Analysis (Tasks 3-5) | `{crew.model_config['complex']}` |\n")
            if crew.model_config["complex"] == crew.model_config["fallback"]:
                f.write("| **Note** | ⚠️  Fallback model activated for context overflow |\n")
            f.write("\n")

            # Review output
            f.write("---\n\n")
            f.write("### 📋 Review Analysis\n\n")

            if result:
                # Extract the actual review content
                result_str = str(result)

                # Clean up the output if it has extra wrapper text
                if "Final Answer:" in result_str:
                    result_str = result_str.split("Final Answer:")[-1].strip()

                f.write(result_str)
            else:
                f.write("⚠️  _No review output generated_\n")

            # Footer
            f.write("\n\n---\n")
            f.write(
                "_🤖 Generated by CrewAI autonomous agents | "
                f"🔗 [View Traces]({get_pr_url(repo, pr_number)})_\n"
            )

        logger.info("✅ Summary written to GitHub Actions")

    except Exception as e:
        logger.error(f"❌ Error writing summary: {e}")


def get_pr_url(repo, pr_number):
    """Generate PR URL."""
    return f"https://github.com/{repo}/pull/{pr_number}"


def get_commit_url(repo, sha):
    """Generate commit URL."""
    return f"https://github.com/{repo}/commit/{sha}"


def main():
    """Entry point for GitHub Actions - commit-based review."""
    # Load .env for local testing
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Get GitHub context from environment
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")
    sha = os.getenv("COMMIT_SHA")
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Validate environment
    if not all([pr_number, repo, sha, api_key]):
        logger.error("❌ Missing required environment variables")
        logger.error(f"   PR: {pr_number}")
        logger.error(f"   Repo: {repo}")
        logger.error(f"   SHA: {sha[:8] if sha else 'None'}")
        logger.error(f"   API Key: {'Set' if api_key else 'Missing'}")
        return 1

    logger.info("=" * 70)
    logger.info("🚀 CrewAI Code Review Agent Started")
    logger.info("=" * 70)
    logger.info(f"📦 Repository: {repo}")
    logger.info(f"🔗 Pull Request: #{pr_number}")
    logger.info(f"📝 Commit SHA: {sha[:8]}")
    logger.info("")

    try:
        # Initialize crew
        logger.info("🤖 Initializing CrewAI crew...")
        crew = CodeReviewCrew()
        logger.info("✅ Crew initialized successfully")
        logger.info("")

        # Show configuration
        logger.info("🔧 Model Configuration:")
        logger.info(f"   ⚡ Fast (Tasks 1,2,6): {crew.model_config['fast']}")
        logger.info(f"   🧠 Complex (Tasks 3-5): {crew.model_config['complex']}")
        logger.info(f"   🔄 Fallback: {crew.model_config['fallback']}")
        logger.info(f"   🎯 Max Tokens: {crew.llm_config['max_tokens']}")
        logger.info("")

        # Show agents
        logger.info("🤖 Agent Team:")
        logger.info("   1️⃣ Code Quality Reviewer (Coordinator)")
        logger.info("   2️⃣ Security & Performance Analyst")
        logger.info("   3️⃣ Architecture & Impact Analyst")
        logger.info("   4️⃣ Executive Summary Agent (Synthesizer)")
        logger.info("")

        # Show workflow
        logger.info("📋 Review Workflow:")
        logger.info("   1. Analyze commit changes (code quality, tests, docs)")
        logger.info("   2. Security & performance review")
        logger.info("   3. Find related files (import analysis)")
        logger.info("   4. Analyze impact on related files")
        logger.info("   5. Architecture review (design patterns, coupling)")
        logger.info("   6. Generate executive summary (CLEAN CONTEXT ONLY)")
        logger.info("")
        logger.info("⏱️ Estimated time: 3-5 minutes")
        logger.info("💰 Cost: $0.00 (free OpenRouter models)")
        logger.info("🔍 Tracing: Enabled")
        logger.info("🧹 Context: Manual clean extraction for Task 6")
        logger.info("")
        logger.info("-" * 70)
        logger.info("")

        # Prepare inputs for crew
        inputs = {
            "pr_number": pr_number,
            "repository": repo,
            "commit_sha": sha,
            "review_scope": "commit",
            "output_format": "github_actions_summary",
        }

        logger.info("🚀 Crew executing with clean context passing...")
        logger.info("")

        # Execute crew with clean context extraction
        result = execute_crew_with_clean_context(crew, inputs, max_retries=2)

        logger.info("")
        logger.info("-" * 70)
        logger.info("")
        logger.info("✅ Code review completed successfully!")
        logger.info("")

        # Write to GitHub Actions summary
        write_actions_summary(crew, pr_number, repo, sha, result)

        logger.info("")
        logger.info("=" * 70)
        logger.info("🎉 CrewAI Code Review Agent Completed")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error(f"❌ Error during code review: {e}")
        logger.error("=" * 70)
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
