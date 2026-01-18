# Startup Blueprint

A startup blueprint *and* a production-grade Git template for running your business in a single monorepo—from “I’m starting a company” to “my website is deployed and CI is green.”

This repo is intentionally opinionated: every meaningful business decision should live in Git as docs, and every code change should ship via branches + pull requests with automation validating quality.

## What this repo is

- **A step-by-step startup guide** (legal, domain/DNS, email, finance, operations) you can follow from day one.
- **A working Git/CI foundation** you can fork or copy to run your own business repo, including automated formatting, linting, and documentation link checks.
- **A monorepo-first mindset**: keep docs, product requirements, code, scripts, and operational playbooks together so the business stays auditable and repeatable.

## Recommended workflow

### If you're using this for your own business

1. Fork this repo into a **private** repository (your business source of truth).
2. Follow the startup guide docs to complete the setup.
3. If you need to do something differently:
   - Create a branch.
   - Update the instructions/docs to match your reality.
   - Merge to `main` in your private fork.

### If you improve something that helps everyone

1. Fork this repo.
2. Create a branch.
3. Make the improvement (docs, automation, templates, etc.).
4. Open a PR back to this repo so others can benefit.

## What’s included today

- Startup setup guides (business foundation + operational basics)
- GitHub Actions CI that:
  - Auto-formats code and docs
  - Runs linters across common file types
  - Checks Markdown links on the exact commit SHA (race-condition safe)
- Repo quality tooling:
  - Prettier, ESLint, markdownlint, stylelint
  - commitlint (Conventional Commits)
  - lychee (link checker)
  - SQLFluff config (for SQL formatting/linting)

## Quick start

- Start here: [`docs/guides/QUICKSTART.md`](./docs/guides/QUICKSTART.md)
- Or begin at Guide 1: [`docs/guides/01-legal-foundation.md`](./docs/guides/01-legal-foundation.md)

## Why this exists

Most “startup advice” is vague. Most “repo templates” ignore the business side.

This project combines both: a practical startup operating blueprint and the engineering workflow to keep execution clean from day one.

## Coming soon (high level)

- **Monorepo scaffolding** (`apps/`, `packages/`, `scripts/`) with example app/package placeholders
- **Product development templates** (PRD/TDD structure) to capture product intent alongside code
- **Deployment templates** (starter setup for common hosting targets, e.g., Cloudflare Pages/Workers)
- **Automation expansion** (tests/build steps once example apps exist)

## Contributing

- Open issues for improvements or gaps.
- Prefer PRs that update docs + automation together when appropriate.
- Keep guidance and templates generic so they can be reused across industries.

## License

MIT (see LICENSE).