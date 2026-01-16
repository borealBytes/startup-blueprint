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
✅ **Comprehensive tooling** - Prettier, ESLint, markdownlint, stylelint, commitlint, TypeScript  
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
                    ├─ Yes → Bot commits fixes → Job ends
                    └─ No  → Success → Link check runs
```

### Tools Run

1. **Prettier** - Format all code files
2. **ESLint** - Lint JavaScript/TypeScript with auto-fix
3. **stylelint** - Lint CSS/SCSS with auto-fix
4. **markdownlint** - Lint Markdown files
5. **commitlint** - Validate commit message format
6. **TypeScript** - Check types (no emit)
7. **Lychee** - Check Markdown links (offline mode)

---

## Local Development Setup

### Prerequisites

```bash
# Install pnpm (if not already installed)
npm install -g pnpm@8

# Install dependencies
pnpm install
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

### Editor Integration

#### VS Code (Recommended)

**Install Extensions:**

- [Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
- [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)
- [stylelint](https://marketplace.visualstudio.com/items?itemName=stylelint.vscode-stylelint)

**Enable Format on Save:**

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.fixAll.stylelint": true
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
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
   pnpm format
   pnpm lint:all
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

---

## Support

If you encounter issues with the CI/CD pipeline:

1. **Check this guide first** for common issues
2. **Check the [workflow file](.github/workflows/ci.yml)** for details
3. **Open an issue** with:
   - Workflow run link
   - Error message
   - Steps to reproduce

---

**Last updated:** 2026-01-16  
**Maintainer:** @borealBytes
