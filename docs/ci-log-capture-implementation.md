# CI Log Capture Implementation Summary

## Overview

This document describes the complete CI log capture system that enables CrewAI agents to analyze all aspects of the CI pipeline efficiently and intelligently.

## Architecture

### Data Flow

```
CI Job Starts
    ↓
[Initialize Capture] - Create log file
    ↓
[Job Steps] - All output → tee to log file
    ↓
[Finalize Capture] - Package log + summary + metadata
    ↓
[Upload Artifact] - GitHub Actions artifact storage
    ↓
[CrewAI Job Starts]
    ↓
[Download All Artifacts] - Get all CI job data
    ↓
[Organize Workspace] - Build ci_results/ structure
    ↓
[CrewAI Analysis] - Smart log reading with size checks
    ↓
[Upload CrewAI Workspace] - Including its own execution log
```

### Key Innovation: No API Scraping

**Traditional Approach (Bad):**
- CrewAI calls GitHub API to fetch job logs
- Rate limits become a problem
- Data may not be complete yet
- Extra latency and complexity

**Our Approach (Good):**
- Each job captures its own output during execution
- Uploads as artifact (GitHub's native feature)
- CrewAI downloads artifacts (unlimited, fast)
- No API calls needed = no rate limits

## Components

### 1. Composite Action: `capture-job-output`

**Location:** `.github/actions/capture-job-output/action.yml`

**Two Modes:**

#### Mode: `start`
- Creates `.crewai-job-output/` directory
- Initializes `current-job.log` file
- Logs job start timestamp
- Saves job folder name for later

#### Mode: `finish`
- Reads current-job.log
- Copies GitHub step summary
- Creates metadata.json with:
  - Job name and conclusion
  - Workflow run info
  - Log size and line count
  - Timestamp
- Uploads as artifact: `ci-job-output-{job-name}`

### 2. Job Pattern (All CI Jobs)

Every CI job follows this structure:

```yaml
steps:
  # ALWAYS FIRST
  - name: Initialize job capture
    uses: ./.github/actions/capture-job-output
    with:
      job-name: 'your-job-name'
      mode: 'start'
  
  # Checkout
  - name: Checkout
    uses: actions/checkout@v4
  
  - name: Log checkout
    run: echo "✅ Checkout complete" | tee -a .crewai-job-output/current-job.log
  
  # Setup with logging
  - name: Setup [tool]
    uses: actions/setup-[tool]@vX
  
  - name: Log setup
    run: |
      echo "✅ Setup complete" | tee -a .crewai-job-output/current-job.log
      [tool] --version | tee -a .crewai-job-output/current-job.log
  
  # Main work with full logging
  - name: Run [task]
    run: |
      echo "🚀 Running..." | tee -a .crewai-job-output/current-job.log
      [command] 2>&1 | tee -a .crewai-job-output/current-job.log
  
  # ALWAYS LAST (even on failure)
  - name: Finalize job capture
    if: always()
    uses: ./.github/actions/capture-job-output
    with:
      job-name: 'your-job-name'
      job-conclusion: ${{ job.status }}
      mode: 'finish'
```

### 3. CrewAI Workflow Updates

**Location:** `.github/workflows/crewai-review-reusable.yml`

**Key Steps:**

1. **Initialize capture** - CrewAI job captures its own execution
2. **Checkout & prepare PR data** - With logging
3. **Download artifacts** - All `ci-job-output-*` artifacts
4. **Organize workspace:**
   ```
   workspace/
   ├── diff.txt
   ├── diff.json
   ├── commits.json
   └── ci_results/
       ├── _job_index.json          # Master index
       ├── credential-validation/
       │   ├── log.txt              # Full log
       │   ├── summary.md           # GitHub summary
       │   └── metadata.json        # Job info
       ├── core-ci/
       ├── test-crewai/
       └── test-build-website/
   ```
5. **Install dependencies** - With logging
6. **Run CrewAI** - Full output captured
7. **Finalize capture** - Upload CrewAI's own log

### 4. Intelligent CI Tools

**Location:** `.crewai/tools/ci_tools.py`

#### Log Size Thresholds

- **< 50KB** = Small log (safe to read fully)
- **50-200KB** = Medium log (read with caution)
- **> 200KB** = Large log (MUST use search/grep)

#### Available Tools

##### `read_job_index()`
**Purpose:** Get overview of all jobs  
**Returns:** Job names, statuses, log sizes, timestamps  
**Use:** ALWAYS call this first

**Example Output:**
```
# CI Job Index

Workflow Run: 123456 (#42)

## Jobs (4 completed)

✅ **credential-validation** (success)
   - Folder: `credential-validation`
   - Log size: 12.3KB (small - safe to read)
   - Timestamp: 2026-01-30T01:09:38Z

❌ **core-ci** (failure)
   - Folder: `core-ci`
   - Log size: 245.7KB (LARGE - use grep/search)
   - Timestamp: 2026-01-30T01:10:15Z
```

##### `check_log_size(folder_name)`
**Purpose:** Check size before reading  
**Returns:** Size stats + recommendation  
**Use:** Before calling `read_full_log`

##### `read_job_summary(folder_name)`
**Purpose:** Read GitHub Actions step summary  
**Returns:** Formatted summary showing what failed  
**Use:** ALWAYS read summaries before logs

**Why:** Summaries are small and tell you WHAT failed. Logs show HOW it failed.

##### `search_log(folder_name, pattern, context_lines=3, max_matches=50)`
**Purpose:** Grep for specific patterns  
**Returns:** Matching lines with context  
**Use:** For large logs instead of reading everything

**Good Patterns:**
- `"error"` - Find error messages
- `"FAILED"` - Find test failures
- `"exception"` - Find stack traces
- `"test_user_login"` - Find specific test

##### `read_full_log(folder_name, max_lines=None)`
**Purpose:** Read complete log  
**Returns:** Full log content  
**Safety:** Blocks reading logs > 200KB without limit

##### `get_log_stats(folder_name)`
**Purpose:** Quick assessment without reading  
**Returns:** Error counts, warning counts, file size  
**Use:** Decide if detailed review is needed

**Example Output:**
```
# Log Statistics: core-ci

Total lines: 5,432
File size: 245.7KB

## Pattern Counts

- 🔴 Errors: 23
- ⚠️ Warnings: 5
- ❌ Failed: 8
- 💥 Exceptions: 2

🚨 Recommendation: This log contains errors/failures.
Use `search_log('core-ci', 'error')` to investigate.
```

## Workflow for CI Analysis Agent

### Mandatory Workflow

```python
# 1. Start with index
index = read_job_index()
# See all jobs, their statuses, log sizes

# 2. Read ALL summaries (they're small)
for job in jobs:
    summary = read_job_summary(job.folder)
    # Summaries tell you WHAT failed

# 3. Smart log analysis (only for failed jobs)
for failed_job in failed_jobs:
    size_check = check_log_size(failed_job.folder)
    
    if size < 50KB:
        # Small log - safe to read
        log = read_full_log(failed_job.folder)
    
    elif size < 200KB:
        # Medium log - get stats first
        stats = get_log_stats(failed_job.folder)
        if stats.error_count > 0:
            errors = search_log(failed_job.folder, 'error')
    
    else:
        # Large log - MUST use search
        errors = search_log(failed_job.folder, 'error')
        failures = search_log(failed_job.folder, 'FAILED')
```

### Do NOT

❌ Call `read_full_log` without checking size first  
❌ Read large logs (>200KB) without using search  
❌ Skip reading summaries (they're always small and informative)  
❌ Assume log content without using tools

### DO

✅ Always call `read_job_index()` first  
✅ Read all summaries before any logs  
✅ Check log size before reading  
✅ Use `search_log` for large logs  
✅ Provide specific file:line references in recommendations

## Implementation Status

### ✅ Completed

1. **Composite Action** (`.github/actions/capture-job-output/action.yml`)
   - Initialize and finalize modes
   - Complete metadata capture
   - Artifact upload

2. **Credential Validation Job** (`.github/workflows/validate-environment-reusable.yml`)
   - Full log capture from start to finish
   - Logs setup, dependencies, validation output
   - Uploads artifact

3. **CI Tools** (`.crewai/tools/ci_tools.py`)
   - All 6 tools implemented
   - Size-aware reading
   - Search/grep functionality
   - Statistics generation

4. **CrewAI Workflow** (`.github/workflows/crewai-review-reusable.yml`)
   - Downloads all CI artifacts
   - Organizes into workspace structure
   - Builds job index
   - Captures its own execution

### 🚧 Remaining Work

These jobs still need log capture added:

1. **Core CI** (`.github/workflows/format-lint-reusable.yml`)
   - Format checks
   - Lint results
   - Pre-commit hooks

2. **Test CrewAI** (`.github/workflows/test-crewai-reusable.yml`)
   - Agent tests
   - Mock PR tests

3. **Test & Build Website** (`.github/workflows/website-test-build-reusable.yml`)
   - Build process
   - Asset generation

4. **CI Analysis Crew** (`.crewai/crews/ci_analysis.py`)
   - Update to use new CI tools
   - Implement smart workflow
   - Generate actionable recommendations

## Benefits

### 1. No API Rate Limits
- Artifacts use GitHub's storage (unlimited reads)
- No GitHub API calls needed
- Faster and more reliable

### 2. Complete Visibility
- See exactly what each job did
- See what data CrewAI received
- Audit trail of AI decisions
- Cost tracking for all crews

### 3. Efficient Token Usage
- Size checks prevent reading huge logs
- Search/grep for targeted investigation
- Summaries give context cheaply
- Statistics provide quick assessment

### 4. Better Debugging
- When CrewAI fails, see its full log
- When CI fails, see complete context
- Reproducible analysis (artifacts retained 7 days)

### 5. Scalable
- Add new jobs easily (use composite action)
- Add new analysis tools easily (standard pattern)
- No infrastructure changes needed

## Example: Complete Job Log

### Before (Partial Capture)
```
========================================
Credential Validation for startup-blueprint
========================================
Timestamp: 2026-01-30 01:09:38 UTC

=== Validating Cloudflare Credentials ===
✅ CLOUDFLARE_API_TOKEN is set
...
✅ All credentials validated successfully!
========================================
```

### After (Complete Capture)
```
========================================
Job: credential-validation
Started: 2026-01-30 01:09:35 UTC
========================================

✅ Code checked out
  Repository: borealBytes/startup-blueprint
  Ref: abc123def

📦 Installing dependencies...

Installing Wrangler...
added 245 packages in 8s

✅ Dependencies installed

🔐 Running credential validation...

========================================
Credential Validation for startup-blueprint
========================================
Timestamp: 2026-01-30 01:09:38 UTC

=== Validating Cloudflare Credentials ===
✅ CLOUDFLARE_API_TOKEN is set
Testing Cloudflare credentials...
✅ Cloudflare API token verified
...
✅ All credentials validated successfully!
========================================

========================================
Job Completed: 2026-01-30 01:09:45 UTC
Conclusion: success
========================================
```

## Testing

### Manual Testing Checklist

1. **Small Log Test**
   - Credential validation (usually < 50KB)
   - Verify full read works
   - Check agent doesn't use search unnecessarily

2. **Large Log Test**
   - Core CI with failures (can exceed 200KB)
   - Verify agent checks size first
   - Verify agent uses search, not full read

3. **Artifact Organization**
   - Check all artifacts downloaded
   - Verify workspace structure correct
   - Verify job index contains all jobs

4. **CrewAI Execution**
   - Verify CrewAI's own log captured
   - Check cost tracking visible
   - Verify tool calls logged

## Future Enhancements

### 1. Log Compression
For jobs with very large logs (>10MB), compress before upload:
```yaml
- name: Finalize with compression
  run: |
    gzip .crewai-job-output/current-job.log
    # Tool would decompress transparently
```

### 2. Streaming Analysis
For extremely large logs, analyze in chunks:
```python
@tool("Stream Log Analysis")
def analyze_log_streaming(folder_name: str, chunk_size: int = 1000):
    # Process log in chunks to avoid memory issues
    pass
```

### 3. Visual Log Viewer
Web UI to view logs with:
- Syntax highlighting
- Collapsible sections
- Error highlighting
- Timeline view

### 4. Historical Comparison
Compare current run to previous runs:
- "This test started failing in run #42"
- "Error count increased by 300%"
- "New error pattern detected"

## Troubleshooting

### Artifacts Not Found

**Symptom:** `No CI artifacts found - jobs may not have uploaded data`

**Causes:**
1. Job didn't finish (canceled/timeout)
2. Job doesn't have capture action
3. Upload failed (network issue)

**Fix:**
- Check job completed successfully
- Verify `finalize job capture` step ran
- Check Actions artifacts page

### Log Size Warning

**Symptom:** `🚨 ERROR: Log is 245.7KB - too large to read without limit!`

**Cause:** Agent tried to read large log without checking size

**Fix:** Agent should:
1. Call `check_log_size()` first
2. Use `search_log()` for large files
3. Or call with limit: `read_full_log(folder, 500)`

### Missing Setup Steps

**Symptom:** Log starts with main task, missing checkout/setup

**Cause:** Job missing log statements after setup steps

**Fix:** Add logging after each step:
```yaml
- name: Setup Node
  uses: actions/setup-node@v4

- name: Log setup  # ADD THIS
  run: echo "✅ Node setup" | tee -a .crewai-job-output/current-job.log
```

## Summary

This implementation provides:

✅ **Complete CI visibility** - Every job from start to finish  
✅ **No API limits** - Artifact-based data transfer  
✅ **Intelligent analysis** - Size-aware log reading  
✅ **Efficient token usage** - Search instead of full reads  
✅ **Complete audit trail** - Including CrewAI's own execution  
✅ **Scalable architecture** - Easy to add new jobs/tools

The system enables CrewAI agents to provide highly specific, actionable feedback on CI failures while minimizing token costs and avoiding API rate limits.
