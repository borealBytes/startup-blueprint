#!/usr/bin/env python3
"""Entry point for CrewAI code review in GitHub Actions."""

import logging
import os
import sys
import time
from pathlib import Path

from crew import CodeReviewCrew
from dotenv import load_dotenv

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


def execute_with_retry(crew, inputs, max_retries=2):
    """
    Execute crew with retry logic for rate limit errors.

    Args:
        crew: Initialized CrewAI crew
        inputs: Input parameters for crew execution
        max_retries: Number of retry attempts (default: 2)

    Returns:
        Crew execution result

    Raises:
        Exception: After exhausting all retries
    """
    attempt = 0
    last_error = None

    while attempt <= max_retries:
        try:
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{max_retries}")

            result = crew.crew().kickoff(inputs=inputs)
            return result

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Check if it's a rate limit error
            is_rate_limit = (
                "rate limit" in error_str
                or "ratelimit" in error_str
                or "429" in error_str
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


def main():
    """Entry point for GitHub Actions - commit-based review."""
    # Load .env for local testing
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Get GitHub context from environment
    # Note: These match the env vars set in crewai-review-reusable.yml
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
        logger.info(
            f"   1️⃣ Code Quality: {crew.model_config['code_quality']}"
        )
        logger.info(f"   2️⃣ Security: {crew.model_config['security']}")
        logger.info(
            f"   3️⃣ Architecture: {crew.model_config['architecture']}"
        )
        logger.info("")

        # Show agents
        logger.info("🤖 Agent Team:")
        logger.info("   1️⃣ Code Quality Reviewer (Coordinator)")
        logger.info("   2️⃣ Security & Performance Analyst")
        logger.info("   3️⃣ Architecture & Impact Analyst")
        logger.info("")

        # Show workflow
        logger.info("📋 Review Workflow:")
        logger.info(
            "   1. Analyze commit changes (code quality, tests, docs)"
        )
        logger.info("   2. Security & performance review")
        logger.info("   3. Find related files (import analysis)")
        logger.info("   4. Analyze impact on related files")
        logger.info("   5. Architecture review (design patterns, coupling)")
        logger.info("   6. Generate executive summary & post to PR")
        logger.info("")
        logger.info("⏱️ Estimated time: 3-5 minutes")
        logger.info("💰 Cost: $0.00 (free OpenRouter models)")
        logger.info("")
        logger.info("-" * 70)
        logger.info("")

        # Prepare inputs for crew
        inputs = {
            "pr_number": pr_number,
            "repository": repo,
            "commit_sha": sha,
            "review_scope": "commit",
            "output_format": "executive_summary",
        }

        logger.info("🚀 Crew executing...")
        logger.info("")

        # Execute crew with retry logic
        result = execute_with_retry(crew, inputs, max_retries=2)

        logger.info("")
        logger.info("-" * 70)
        logger.info("")
        logger.info("✅ Code review completed successfully!")
        logger.info(f"📊 Review posted to PR #{pr_number}")
        logger.info("")

        # Write summary to GitHub Actions
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write("\n## 🤖 CrewAI Code Review Results\n\n")
                f.write(f"**Repository:** {repo}\n\n")
                f.write(f"**Pull Request:** #{pr_number}\n\n")
                f.write(f"**Commit:** {sha[:8]}\n\n")
                f.write("**Models Used:**\n")
                f.write(
                    f"- Code Quality: {crew.model_config['code_quality']}\n"
                )
                f.write(f"- Security: {crew.model_config['security']}\n")
                f.write(
                    f"- Architecture: {crew.model_config['architecture']}\n\n"
                )
                f.write("**Status:** ✅ Review Complete\n\n")
                if result:
                    f.write(f"**Review Output:**\n\n{result}\n")

            logger.info("📝 Summary written to GitHub Actions")

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
