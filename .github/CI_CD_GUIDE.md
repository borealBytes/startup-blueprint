# CI/CD Guide: Code Quality Pipeline

## 🔑 Understanding This Workflow

**This CI/CD pipeline differs from traditional local development workflows.**

### The Key Difference

In most projects, developers format and lint code **locally before pushing**. This project does it **in CI after you commit**.

```mermaid
flowchart TB
    accTitle: CI Workflow Comparison
    accDescr: Compares this project's CI-first format/lint approach with traditional local formatting showing how agents, web editors, and local developers all benefit from automated CI formatting

    subgraph this_project ["✅ THIS PROJECT: CI Does Format/Lint"]
        direction TB
        subgraph agent_flow ["Agent/Local/Web"]
            edit_code[Edit Code] --> commit_changes[Commit] --> push_code[Push]
        end
        subgraph ci_pipeline ["CI Pipeline"]
            format_lint[Format/Lint] --> bot_commit[[Bot Auto-Commit]] --> test_code[Test] --> build_app[Build] --> deploy_app[Deploy]
        end
        agent_flow --> ci_pipeline
    end

    subgraph traditional ["⚠️ TRADITIONAL: Local Format/Lint"]
        direction TB
        subgraph local_dev ["Local Machine"]
            edit_local[Edit Code] --> format_local[Format/Lint] --> commit_local[Commit] --> push_local[Push]
        end
        subgraph ci_traditional ["CI Pipeline"]
            test_trad[Test] --> build_trad[Build] --> deploy_trad[Deploy]
        end
        local_dev --> ci_traditional
    end
```

**Key difference:** Format/Lint happens in CI with automatic bot commits (subroutine shape `[[Bot Auto-Commit]]`), not on your machine. ✅ = our approach, ⚠️ = traditional.

### Why This Approach?

This enables **3 different development modes** with consistent results:

1. **🤖 AI Agents (Perplexity MCP, Claude, Cursor)** — Agents commit directly via Git tools, CI handles all formatting
2. **🌐 GitHub Web Editor** — Edit files in browser, commit, CI formats automatically
3. **💻 Local Development** — Edit locally, commit, push, **then pull after CI completes** to get formatted code

**The Universal Flow:**

```mermaid
flowchart LR
    accTitle: Universal Development Workflow
    accDescr: Common workflow for all development modes where CI automatically formats code and developers pull changes to stay synchronized

    any_mode([Any Dev Mode]) --> commit_push[Commit + Push]
    commit_push --> ci_format[CI Format/Lint]
    ci_format --> changes_check{Changes Made?}
    changes_check -->|Yes| bot_commits[[Bot Commits Fixes]]
    changes_check -->|No| ready([Ready to Continue])
    bot_commits --> pull_sync[Pull to Sync]
    pull_sync --> ready
```

### If You're Developing Locally

**Important:** After pushing, wait for GitHub Actions to complete, then:

```bash
git pull
```

This brings down any formatting/linting commits the CI bot made. Then continue your work.

---

## 📚 Table of Contents

- [Understanding This Workflow](#-understanding-this-workflow)
- [How the Pipeline Works](#how-the-pipeline-works)
- [Tools Reference](#tools-run)
- [Troubleshooting](#troubleshooting)
- [Configuration Files](#configuration-files-reference)
- [Development Mode Tips](#development-mode-tips)

---

## How the Pipeline Works

### The Complete Flow

Every commit to a pull request triggers this workflow in two phases:

#### Phase 1: Format & Lint

```mermaid
flowchart TB
    accTitle: CI Pipeline Format and Lint Phase
    accDescr: First phase of CI pipeline that captures commit SHA, runs formatting and linting tools, and creates bot commits if any code changes are needed

    commit_pushed([Commit Pushed to PR]) --> capture_sha[Capture Initial SHA]
    capture_sha --> run_tools{{Run All Format/Lint Tools}}
    run_tools --> detect_changes{Changes Detected?}
    detect_changes -->|Yes| stage_changes[Stage Changes]
    detect_changes -->|No| output_original[Output Initial SHA]
    stage_changes --> generate_msg[Generate Commit Message]
    generate_msg --> bot_commits[[Bot Commits Fixes]]
    bot_commits --> output_bot_sha[Output Bot SHA]
```

#### Phase 2: Validation

```mermaid
flowchart TB
    accTitle: CI Pipeline Validation Phase
    accDescr: Second phase that validates all markdown links using the exact SHA from phase 1 to ensure race-condition safe checking of the correct commit

    from_phase1([From Phase 1]) --> receive_sha[Receive Exact SHA]
    receive_sha --> checkout_sha[Checkout Specific SHA]
    checkout_sha --> verify_sha[Verify SHA Match]
    verify_sha --> validate_links[Validate Markdown Links]
    validate_links --> all_valid{All Valid?}
    all_valid -->|Yes| ci_pass([CI Passes])
    all_valid -->|No| ci_fail([CI Fails])
```

### Step-by-Step Breakdown

1. **Commit Pushed** — You push a commit via Perplexity, GitHub web editor, or local Git
2. **SHA Capture** — CI records the exact commit SHA at the start
3. **Format & Lint** — 15 tools run automatically:
   - Prettier (JS/TS/JSON/MD/YAML/CSS)
   - ESLint (JS/TS)
   - Black, isort, flake8 (Python)
   - SQLFluff (SQL)
   - markdownlint, yamllint (Docs)
   - gofmt, golangci-lint (Go)
   - TypeScript type checking
   - commitlint (commit messages)
4. **Changes Detected** — If any tool modified files, bot stages them
5. **Bot Commits** — Automatic commit with detailed message listing changed files
6. **SHA Output** — Job outputs either original SHA (no changes) or bot SHA (changes applied)
7. **Link Check** — Receives exact SHA, checks out that specific commit
8. **Verification** — Confirms correct commit is checked out
9. **Link Validation** — All Markdown links checked for validity
10. **Result** — ✅ Pass or ❌ Fail

### Key Features

✅ **Race-condition safe** — Exact SHA passed between jobs  
✅ **No re-runs needed** — Single linear workflow per push  
✅ **Bot commits excluded** — GitHub Actions bot doesn't trigger new runs  
✅ **Multi-language** — JavaScript/TypeScript, Python, SQL, Go, CSS, Markdown, YAML, Bash  
✅ **Auto-fixes** — Bot commits formatting/linting fixes automatically

---

## Tools Run

### Tool Execution Order

```mermaid
flowchart TB
    accTitle: Code Quality Tool Execution Pipeline
    accDescr: Sequential execution of formatting and linting tools across multiple languages from initial commit through final link validation

    commit([Commit]) --> detect_lang{{Detect Languages}}

    detect_lang --> prettier[Prettier]
    detect_lang --> black[Black]
    detect_lang --> sqlfluff_fmt[SQLFluff Format]
    detect_lang --> gofmt[gofmt]

    prettier --> eslint[ESLint]
    black --> isort[isort]
    isort --> flake8[flake8]
    sqlfluff_fmt --> sqlfluff_lint[SQLFluff Lint]
    gofmt --> golangci[golangci-lint]

    eslint --> final_checks{{Final Checks}}
    flake8 --> final_checks
    sqlfluff_lint --> final_checks
    golangci --> final_checks

    final_checks --> check_changes{Any Changes?}
    check_changes -->|Yes| bot_commit[[Bot Commits]]
    check_changes -->|No| link_check[Link Check]
    bot_commit --> link_check
    link_check --> complete([Complete])
```

### Formatting Tools (Auto-fix)

| Tool         | Languages                               | Purpose                        |
| ------------ | --------------------------------------- | ------------------------------ |
| **Prettier** | JS, TS, JSON, MD, YAML, CSS, SCSS, HTML | Universal code formatter       |
| **Black**    | Python                                  | PEP 8 compliant formatting     |
| **isort**    | Python                                  | Sort and organize imports      |
| **SQLFluff** | SQL                                     | Format SQL (PostgreSQL/DuckDB) |
| **gofmt**    | Go                                      | Official Go formatter          |

### Linting Tools (Check + Auto-fix)

| Tool              | Languages       | Purpose                         |
| ----------------- | --------------- | ------------------------------- |
| **ESLint**        | JS, TS          | Catch errors, enforce style     |
| **flake8**        | Python          | PEP 8 style guide enforcement   |
| **SQLFluff**      | SQL             | SQL syntax and style linting    |
| **stylelint**     | CSS, SCSS       | CSS/SCSS linting                |
| **markdownlint**  | Markdown        | Markdown style enforcement      |
| **yamllint**      | YAML            | YAML syntax validation          |
| **shellcheck**    | Bash            | Shell script linting            |
| **golangci-lint** | Go              | Comprehensive Go linting        |
| **TypeScript**    | TS              | Type error checking             |
| **commitlint**    | Commit messages | Conventional Commits validation |

### Link Validation

| Tool       | Purpose                                    |
| ---------- | ------------------------------------------ |
| **Lychee** | Validate all Markdown links (with caching) |

---

## Troubleshooting

### Quick Diagnosis

```mermaid
flowchart TB
    accTitle: CI Failure Troubleshooting Decision Tree
    accDescr: Decision tree for diagnosing and fixing common CI failures including build errors, test failures, linting issues, and broken documentation links

    ci_failed{CI Failed?} --> identify_job{Which Job?}

    identify_job -->|Format & Lint| identify_tool{Which Tool?}
    identify_job -->|Link Check| broken_links[Fix Broken Links]

    identify_tool -->|Prettier/ESLint| syntax_error[Fix Syntax Error]
    identify_tool -->|Black/flake8| python_error[Fix Python Error]
    identify_tool -->|SQLFluff| sql_error[Fix SQL Error]
    identify_tool -->|TypeScript| type_error[Fix Type Error]
    identify_tool -->|commitlint| commit_format[Use Conventional Format]

    syntax_error --> commit_fix[Commit Fix]
    python_error --> commit_fix
    sql_error --> commit_fix
    type_error --> commit_fix
    commit_format --> commit_fix
    broken_links --> commit_fix

    commit_fix --> ci_reruns([CI Re-runs])
```

### Common Issues

#### 1. Format/Lint Tool Failed

**Problem:** Red X on "Format & Lint" job

**Solution:**

1. Click the failed job in GitHub Actions
2. Find the tool that failed (e.g., "Run ESLint")
3. Read the error message
4. Fix the issue:
   - **Syntax errors:** Missing brackets, quotes, semicolons
   - **Type errors:** Add proper TypeScript types
   - **Line too long:** Break into multiple lines
   - **Unused imports:** Remove them
5. Commit the fix
6. CI re-runs automatically

#### 2. Commit Message Failed

**Problem:** "commitlint" check failed

**Solution:** Use Conventional Commits format:

```text
type(scope): description

Valid types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
Scope: optional, kebab-case
Description: no period at end, lowercase start
```

**Examples:**

```bash
feat: add new feature
fix(ci): correct workflow
docs: update guide
chore: update deps
```

#### 3. Link Check Failed

**Problem:** "Check Documentation Links" job failed

**Solution:**

1. Check CI logs for broken URLs
2. Common issues:
   - `404`: Update to working URL
   - `429`: Rate limited, add to `.lycheeignore`
   - `Timeout`: Slow server, consider exclusion
   - Relative path broken: Fix file path
3. Fix or exclude URLs
4. Commit and push

#### 4. Bot Committed Changes

**This is normal!** The bot auto-fixed formatting issues.

**What to do:**

- **Web/agent users:** Nothing, continue as usual
- **Local developers:** Run `git pull` to get bot's changes

---

## Configuration Files Reference

### Config File Architecture

```mermaid
flowchart TB
    accTitle: Configuration File Dependencies
    accDescr: How configuration files in the root directory map to their respective tools and contribute to consistent code formatting across the project

    subgraph config_files ["Root Directory Configs"]
        prettierrc[".prettierrc.json"]
        eslintrc[".eslintrc.json"]
        mdlint[".markdownlint.json"]
        stylelintrc[".stylelintrc.json"]
        sqlfluff[".sqlfluff"]
        yamllint[".yamllint.yml"]
        commitlintrc["commitlint.config.js"]
        lycheeignore[".lycheeignore"]
    end

    subgraph tools ["Quality Tools"]
        prettier_tool[Prettier]
        eslint_tool[ESLint]
        mdlint_tool[markdownlint]
        stylelint_tool[stylelint]
        sqlfluff_tool[SQLFluff]
        yamllint_tool[yamllint]
        commitlint_tool[commitlint]
        lychee_tool[Lychee]
    end

    prettierrc --> prettier_tool
    eslintrc --> eslint_tool
    mdlint --> mdlint_tool
    stylelintrc --> stylelint_tool
    sqlfluff --> sqlfluff_tool
    yamllint --> yamllint_tool
    commitlintrc --> commitlint_tool
    lycheeignore --> lychee_tool

    prettier_tool --> consistent[Consistent Quality]
    eslint_tool --> consistent
    mdlint_tool --> consistent
    stylelint_tool --> consistent
    sqlfluff_tool --> consistent
    yamllint_tool --> consistent
    commitlint_tool --> consistent
    lychee_tool --> consistent
```

### Key Configuration Files

#### Formatting

- `.prettierrc.json` — 80 char width, single quotes, trailing commas
- `.prettierignore` — Exclude patterns

#### Linting

- `.eslintrc.json` — JS/TS rules
- `.markdownlint.json` — Markdown rules (relaxed for docs)
- `.stylelintrc.json` — CSS/SCSS rules
- `.sqlfluff` — SQL rules (PostgreSQL dialect)
- `.yamllint.yml` — YAML validation
- `commitlint.config.js` — Commit format validation

#### Link Checking

- `.lycheeignore` — URLs to exclude (bot-protected, known issues)

#### Python (via CLI args)

- **Black:** Line length 88
- **isort:** Profile `black`
- **flake8:** Max line 88, ignore E203/W503

---

## Development Mode Tips

### 🤖 AI Agent Development (Perplexity, Claude, Cursor)

**How it works:**

1. Agent commits via Git MCP/CLI tool
2. CI formats and lints automatically
3. Agent sees results in PR checks
4. Agent makes fixes if needed

**Best practices:**

- Use Conventional Commit format
- Wait for CI before next commit
- Review bot commits (they're part of your PR)

### 🌐 GitHub Web Editor

**How it works:**

1. Edit files directly in GitHub UI
2. Commit with proper message format
3. CI formats automatically
4. Continue editing as needed

**Best practices:**

- Use "feat:", "fix:", "docs:" prefixes
- Wait for green checkmark before merging

### 💻 Local Development

**How it works:**

1. Edit files locally
2. Commit and push
3. CI runs format/lint
4. **Pull to get bot's formatting commits**
5. Continue working

**Best practices:**

```bash
# Your normal workflow
git checkout -b feat/my-feature
vim some-file.ts
git add some-file.ts
git commit -m "feat: add new feature"
git push

# Wait for GitHub Actions to complete (30-60 seconds)
# Check https://github.com/your-repo/actions

# Pull bot's formatting changes
git pull

# Now continue working
vim another-file.ts
# ...
```

**Why pull after CI?**

- Bot may have reformatted your code
- Keeps your local branch in sync
- Prevents merge conflicts

---

## Support

If you encounter issues:

1. **Check CI logs** — Click failed job in GitHub Actions
2. **Review this guide** — Common issues documented above
3. **Check workflow** — [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
4. **Open an issue** — Include:
   - Workflow run link
   - Error message
   - What you were trying to do

---

**Last updated:** 2026-01-23  
**Maintainer:** @borealBytes  
**Workflow:** Universal CI-first format/lint for web agents, GitHub editor, and local dev
