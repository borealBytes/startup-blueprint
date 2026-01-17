# CI/CD Guide: Format-Lint Loop Workflow

## 📚 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Local Development Setup](#local-development-setup)
- [Troubleshooting](#troubleshooting)
- [Configuration Files Reference](#configuration-files-reference)

---

## Overview

Our CI/CD pipeline uses a **format-lint loop** that automatically fixes code formatting and linting issues before running any tests. This ensures consistent code quality across all commits, whether from humans or AI agents.

### Key Features

✅ **Auto-fixes issues** - Bot commits fixes automatically
✅ **Comprehensive tooling** - Prettier, ESLint, Black, markdownlint, stylelint, commitlint, TypeScript
✅ **Multi-language** - JavaScript/TypeScript, Python, Go, CSS/SCSS, Markdown, YAML, Bash
✅ **Works for all** - Humans, AI agents, web UI commits
✅ **Link checking** - Validates all Markdown links

---

## How It Works

### Workflow Chain

```
Push Commit → Format & Lint Job → Link Check Job
                    |
                    v
              Has changes?
                    |
                    |├─ Yes → Bot commits fixes → Job ends
                    └─ No  → Success → Link check runs
```

### Tools Run

**Formatting:**

1. **Prettier** - Format JS/TS/JSON/MD/YAML/CSS/SCSS
2. **Black** - Format Python code (PEP 8 compliant)
3. **isort** - Sort Python imports
4. **gofmt** - Format Go code (when Go projects exist)

**Linting:**

5. **ESLint** - Lint JavaScript/TypeScript with auto-fix
6. **flake8** - Lint Python code (PEP 8 style guide)
7. **stylelint** - Lint CSS/SCSS with auto-fix
8. **markdownlint** - Lint Markdown files
9. **yamllint** - Check YAML syntax
10. **shellcheck** - Lint Bash scripts
11. **golangci-lint** - Lint Go code (when Go projects exist)
12. **commitlint** - Validate commit message format
13. **TypeScript** - Check types (no emit)

**Link Validation:**

14. **Lychee** - Check Markdown links

---

## Local Development Setup

### Prerequisites

**Node.js & pnpm:**

```bash
# Install pnpm (if not already installed)
npm install -g pnpm@8

# Install dependencies
pnpm install
```

**Python (optional, for Python projects):**

```bash
# Install Python 3.13+ (if not already installed)
# On macOS:
brew install python@3.13

# On Ubuntu/Debian:
sudo apt-get install python3.13 python3-pip

# Install Python formatting/linting tools
pip install black isort flake8
```

### Running Format/Lint Locally

**Before committing, always run:**

```bash
# Format all files
pnpm format

# Fix all linting issues
pnpm lint:all

# Or individually:
pnpm prettier --write "**/*.{js,ts,json,md,yml,yaml,css,scss}"
pnpm eslint --fix "**/*.{js,ts,jsx,tsx}"
pnpm markdownlint-cli2 "**/*.md" --fix
```

**For Python projects:**

```bash
# Format Python code
black .

# Sort imports
isort .

# Lint Python code
flake8 . --max-line-length=88 --extend-ignore=E203,W503
```

### Editor Integration

#### VS Code (Recommended)

**Install Extensions:**

- [Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
- [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)
- [stylelint](https://marketplace.visualstudio.com/items?itemName=stylelint.vscode-stylelint)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) (for Python projects)
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) (for Python projects)
- [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort) (for Python projects)

**Enable Format on Save:**

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.fixAll.stylelint": true,
    "source.organizeImports": true
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "black-formatter.args": ["--line-length=88"],
  "isort.args": ["--profile", "black"]
}
```

---

## Troubleshooting

### Problem: CI fails on format/lint checks

**Symptoms:** Red X on PR, "Format & Lint" job failed

**Solutions:**

1. **Pull latest changes:**

   ```bash
   git pull origin <branch-name>
   ```

2. **Run format/lint locally:**

   ```bash
   # For JS/TS/Markdown/etc:
   pnpm format
   pnpm lint:all

   # For Python (if applicable):
   black .
   isort .
   flake8 . --max-line-length=88 --extend-ignore=E203,W503
   ```

3. **Check what changed:**

   ```bash
   git diff
   ```

4. **Commit fixes:**
   ```bash
   git add -A
   git commit -m "style: fix formatting issues"
   git push
   ```

### Problem: Commit message validation fails

**Error:** "commitlint" check failed

**Cause:** Commit message doesn't follow Conventional Commits format

**Fix:** Use this format:

```
type(scope): description

Valid types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
Scope: optional, kebab-case
Description: required, no period at end
```

**Examples:**

```bash
git commit -m "feat: add new CI workflow"
git commit -m "fix(ci): correct prettier config"
git commit -m "docs: update CI guide"
```

### Problem: TypeScript errors

**Error:** "TypeScript" check failed

**Fix:**

1. **Check types locally:**

   ```bash
   pnpm typecheck
   ```

2. **Fix type errors in your code**

3. **Push fixes:**
   ```bash
   git add -A
   git commit -m "fix: resolve TypeScript errors"
   git push
   ```

### Problem: Python linting errors

**Error:** "Black", "isort", or "flake8" check failed

**Fix:**

1. **Format Python code:**

   ```bash
   black .
   ```

2. **Sort imports:**

   ```bash
   isort .
   ```

3. **Check for remaining issues:**

   ```bash
   flake8 . --max-line-length=88 --extend-ignore=E203,W503
   ```

4. **Fix any remaining issues manually**

5. **Push fixes:**
   ```bash
   git add -A
   git commit -m "style: fix Python formatting"
   git push
   ```

**Common flake8 issues:**

- `E501`: Line too long (Black should fix this)
- `F401`: Imported but unused (remove unused imports)
- `E402`: Module level import not at top (move imports to top)
- `W503`: Line break before binary operator (ignored by our config)

### Problem: Broken Markdown links

**Error:** "Check Documentation Links" job failed

**Fix:**

1. **Check the workflow output** to see which links are broken

2. **Fix links in your Markdown files**

3. **Test links locally** (optional):

   ```bash
   npx lychee --offline '**/*.md'
   ```

4. **Push fixes:**
   ```bash
   git add -A
   git commit -m "docs: fix broken links"
   git push
   ```

---

## Configuration Files Reference

### `.prettierrc.json`

**Key settings:**

- `printWidth: 80` for code, `120` for Markdown/JSON
- `singleQuote: true` (consistent with most JS projects)
- `semi: true` (explicit semicolons)
- `trailingComma: "es5"` (IE11 compatible)
- `endOfLine: "lf"` (Unix line endings)

### `.eslintrc.json`

**Key settings:**

- Extends `plugin:@typescript-eslint/recommended`
- Extends `plugin:prettier/recommended`
- `@typescript-eslint/no-unused-vars: error` with `argsIgnorePattern: "^_"`

### `.markdownlint.json`

**Key settings:**

- `MD013: false` (no line length limit, Prettier handles this)
- `MD033: { allowed_elements: [...] }` (allow some HTML tags)
- `MD041: false` (don't require H1 at top)

### `.stylelintrc.json`

**Key settings:**

- Extends `stylelint-config-standard`
- Extends `stylelint-config-prettier`
- `selector-class-pattern: null` (allow any class naming)

### Python Configuration

**Black** (via command-line args):

- Line length: 88 (Black's default, optimal for readability)
- Target: Python 3.13+

**isort** (via command-line args):

- Profile: `black` (compatible with Black's formatting)

**flake8** (via command-line args):

- `--max-line-length=88` (match Black)
- `--extend-ignore=E203,W503` (ignore Black-incompatible rules)
  - `E203`: Whitespace before ':' (Black's style)
  - `W503`: Line break before binary operator (PEP 8 updated)

---

## Support

If you encounter issues with the CI/CD pipeline:

1. **Check this guide first** for common issues
2. **Check the [workflow file](../.github/workflows/ci.yml)** for details
3. **Open an issue** with:
   - Workflow run link
   - Error message
   - Steps to reproduce

---

**Last updated:** 2026-01-17
**Maintainer:** @borealBytes
