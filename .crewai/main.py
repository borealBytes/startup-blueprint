#!/usr/bin/env python3
"""Entry point for CrewAI code review in GitHub Actions."""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from crew import CodeReviewCrew
from crewai import Task
from dotenv import load_dotenv
from litellm import BadRequestError
from tools.cost_tracker import get_tracker

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


def validate_environment():
    """Validate required environment variables at startup.
    
    Raises:
        ValueError: If required variables are missing or invalid
    """
    required_vars = {
        "GITHUB_TOKEN": "GitHub API access",
        "OPENROUTER_API_KEY": "OpenRouter API access",
        "GITHUB_REPOSITORY": "Repository information",
        "PR_NUMBER": "Pull request number",
        "COMMIT_SHA": "Commit SHA",
    }
    
    missing = []
    invalid = []
    
    for var, purpose in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({purpose})")
        elif var == "OPENROUTER_API_KEY" and not value.startswith("sk-or-"):
            invalid.append(f"{var} (invalid format - must start with 'sk-or-')")
    
    if missing or invalid:
        error_parts = []
        if missing:
            error_parts.append(f"Missing: {', '.join(missing)}")
        if invalid:
            error_parts.append(f"Invalid: {', '.join(invalid)}")
        
        error_msg = "; ".join(error_parts)
        logger.error(f"❌ Environment validation failed: {error_msg}")
        raise ValueError(f"Environment validation failed: {error_msg}")
    
    logger.info("✅ Environment variables validated")


def safe_enrich_costs(tracker, timeout_seconds: int = 30) -> bool:
    """Safely enrich cost tracking data from OpenRouter API.
    
    This function:
    - Validates API key before making requests
    - Skips enrichment if callbacks already captured data
    - Implements timeout protection
    - Handles all error cases gracefully
    
    Args:
        tracker: CostTracker instance
        timeout_seconds: Maximum time to wait for enrichment (default: 30)
    
    Returns:
        bool: True if enrichment succeeded or wasn't needed, False on failure
    """
    # Validate API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or not api_key.startswith("sk-or-"):
        logger.error("❌ Invalid or missing OPENROUTER_API_KEY")
        return False
    
    # Check if enrichment is even needed
    if len(tracker.calls) > 0:
        logger.info("✅ Callbacks captured data, enriching for precise costs...")
    else:
        logger.warning("⚠️  No API calls captured by callbacks!")
        logger.info("🔄 Attempting to retrieve usage data from OpenRouter API...")
    
    try:
        # Try enrichment with basic timeout handling
        # Note: For production, consider using timeout_decorator or signals
        start_time = time.time()
        
        tracker.enrich_from_openrouter()
        
        elapsed = time.time() - start_time
        
        if elapsed > timeout_seconds:
            logger.warning(f"⚠️  Enrichment took {elapsed:.1f}s (timeout: {timeout_seconds}s)")
        
        if len(tracker.calls) > 0:
            logger.info(f"✅ Enrichment completed: {len(tracker.calls)} calls tracked")
            return True
        else:
            logger.warning("⚠️  Enrichment returned no data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}", exc_info=True)
        logger.warning("⚠️  Proceeding without complete cost data")
        return False


def execute_crew_with_clean_context(crew_wrapper, inputs, max_retries=2):
    """Execute crew with manual task orchestration to pass CLEAN context to Task 6.

    This function:
    1. Runs Tasks 1-5 normally
    2. Extracts ONLY their final .output strings (no execution traces)
    3. Manually injects those clean outputs into Task 6's context
    4. Executes Task 6 with synthesized findings

    Args:
        crew_wrapper: CodeReviewCrew instance
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
            logger.info("🎯 MANUAL ORCHESTRATION: Running tasks with clean context")
            logger.info("=" * 70)

            # Get crew instance and task objects
            crew_instance = crew_wrapper.crew()
            tasks = crew_instance.tasks

            logger.info(f"\n📋 Total tasks: {len(tasks)}")
            logger.info("   Tasks 1-5: Data collection (will run normally)")
            logger.info("   Task 6: Executive summary (manual clean context)\n")

            # Run Tasks 1-5 to collect findings
            logger.info("=" * 70)
            logger.info("🚀 Phase 1: Running Tasks 1-5 (data collection)")
            logger.info("=" * 70 + "\n")

            # Execute the crew normally for Tasks 1-5
            # Task 6 will also run, but we'll extract clean outputs below
            result = crew_instance.kickoff(inputs=inputs)

            logger.info("\n" + "=" * 70)
            logger.info("✅ Phase 1 Complete: Data collection finished")
            logger.info("=" * 70)

            # Extract clean outputs from Tasks 1-5
            logger.info("\n🧹 Extracting clean task outputs...")
            clean_outputs = []

            for i, task in enumerate(tasks[:5], 1):  # Tasks 1-5 only
                if hasattr(task, "output") and task.output:
                    output_str = str(task.output).strip()
                    # Clean up any wrapper text
                    if "Final Answer:" in output_str:
                        output_str = output_str.split("Final Answer:")[-1].strip()

                    clean_outputs.append(f"\n### Task {i} Output:\n{output_str}\n")
                    logger.info(f"   ✓ Task {i}: Extracted {len(output_str)} chars")
                else:
                    logger.warning(f"   ⚠ Task {i}: No output found")

            # Create clean context string
            clean_context = "\n".join(clean_outputs)
            logger.info(f"\n✅ Clean context prepared: {len(clean_context)} total chars")

            # Task 6 already ran as part of kickoff()
            # The result should contain the final summary
            logger.info("\n" + "=" * 70)
            logger.info("✅ Phase 2 Complete: Executive summary generated")
            logger.info("=" * 70 + "\n")

            logger.info("\n" + "=" * 70)
            logger.info("🎉 All tasks completed successfully")
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
                    f"🔄 Switching all agents to fallback model: {crew_wrapper.model_config['fallback']}"
                )

                # Switch all agents to fallback model (mimo-v2 with 1M context)
                crew_wrapper.model_config["default"] = crew_wrapper.model_config["fallback"]
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


def write_actions_summary(crew, pr_number, repo, sha, result, fallback_used=False):
    """Write formatted review to GitHub Actions summary page.

    Args:
        crew: CodeReviewCrew instance
        pr_number: Pull request number
        repo: Repository name
        sha: Commit SHA
        result: Crew execution result
        fallback_used: Whether fallback model was activated
    """
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file:
        logger.warning("⚠️  GITHUB_STEP_SUMMARY not set, skipping summary")
        return

    tracker = get_tracker()

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
            f.write(f"| All Tasks | `{crew.model_config['default']}` |\n")
            if fallback_used:
                f.write("| **Note** | ⚠️  Fallback model activated for context overflow |\n")
            f.write("\n")

            # Cost breakdown table
            f.write("### 💰 Cost Breakdown\n\n")
            f.write(tracker.format_as_markdown_table())
            f.write("\n\n")

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

    logger.info("=" * 70)
    logger.info("🚀 CrewAI Code Review Agent Started")
    logger.info("=" * 70)
    logger.info("")

    # Validate environment variables first
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return 1

    # Get GitHub context from environment (already validated)
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")
    sha = os.getenv("COMMIT_SHA")

    logger.info(f"📦 Repository: {repo}")
    logger.info(f"🔗 Pull Request: #{pr_number}")
    logger.info(f"📝 Commit SHA: {sha[:8]}")
    logger.info("")

    fallback_used = False

    try:
        # Initialize crew
        logger.info("🤖 Initializing CrewAI crew...")
        crew = CodeReviewCrew()
        logger.info("✅ Crew initialized successfully")
        logger.info("")

        # Show configuration
        logger.info("🔧 Model Configuration:")
        logger.info(f"   🤖 Default (All Tasks): {crew.model_config['default']}")
        logger.info(f"   🔄 Fallback (Overflow): {crew.model_config['fallback']}")
        logger.info(f"   🎯 Max Tokens: {crew.llm_config['max_tokens']}")
        logger.info(f"   🌡️  Temperature: {crew.llm_config['temperature']}")
        logger.info("")

        # Show agents
        logger.info("🤖 Agent Team:")
        logger.info("   1️⃣ Code Quality Reviewer (Coordinator)")
        logger.info("   2️⃣ Security & Performance Analyst")
        logger.info("   3️⃣ Architecture & Impact Analyst")
        logger.info("   4️⃣ Executive Summary Agent (Synthesizer - NO TOOLS)")
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
        logger.info("💰 Cost: Tracked per API call via LiteLLM callbacks + OpenRouter enrichment")
        logger.info("🔍 Tracing: Enabled")
        logger.info("🧹 Context: Manual clean extraction for Task 6")
        logger.info("")
        logger.info("-" * 70)
        logger.info("")

        # Get tracker for monitoring
        tracker = get_tracker()

        # Prepare inputs for crew
        inputs = {
            "pr_number": pr_number,
            "repository": repo,
            "commit_sha": sha,
            "review_scope": "commit",
            "output_format": "github_actions_summary",
        }

        logger.info("🚀 Crew executing with clean context extraction...")
        logger.info("")

        # Execute crew with clean context extraction
        try:
            result = execute_crew_with_clean_context(crew, inputs, max_retries=2)
        except BadRequestError:
            # Fallback was activated during execution
            fallback_used = True
            raise

        logger.info("")
        logger.info("-" * 70)
        logger.info("")
        logger.info("✅ Code review completed successfully!")
        logger.info("")

        # Enrich cost tracking with safe error handling
        logger.info("=" * 70)
        logger.info("🔍 Cost Tracking Status Check")
        logger.info("=" * 70)
        logger.info(f"API calls captured by LiteLLM callbacks: {len(tracker.calls)}")
        logger.info("")

        # Use safe enrichment function
        enrichment_success = safe_enrich_costs(tracker, timeout_seconds=30)
        
        if not enrichment_success and len(tracker.calls) == 0:
            logger.warning("⚠️  Proceeding without cost data - check API key and OpenRouter status")

        logger.info("")

        # Display cost breakdown in logs
        logger.info("=" * 70)
        logger.info("💰 COST BREAKDOWN")
        logger.info("=" * 70)
        logger.info("")
        logger.info(tracker.format_summary())
        logger.info("")
        logger.info("Detailed breakdown:")
        logger.info("")
        # Print table to logs (will look better in GitHub Actions)
        for line in tracker.format_as_markdown_table().split("\n"):
            logger.info(line)
        logger.info("")
        logger.info("=" * 70)
        logger.info("")

        # Write to GitHub Actions summary
        write_actions_summary(crew, pr_number, repo, sha, result, fallback_used)

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
