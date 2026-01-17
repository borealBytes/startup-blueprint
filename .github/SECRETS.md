# GitHub Secrets Documentation

## Overview

This document lists all GitHub Secrets required for CI/CD workflows in the startup-blueprint repository.

**Security Note:** Secrets are encrypted and never exposed in logs or output.

---

## Current Secrets

### None Required (Yet)

The current CI workflow uses `GITHUB_TOKEN` which is automatically provided by GitHub Actions.

**Note:** The CredibilityMarkets workflow uses `GH_PAT` for retry loops, but we've simplified our workflow to not need that yet.

---

## Future Secrets

As we add more features, we may need:

### `CLOUDFLARE_API_TOKEN`

**Purpose:** Deploy to Cloudflare Workers/Pages

**Status:** Not yet implemented

**Permissions needed:**

- Account.Cloudflare Workers Scripts: Edit
- Account.Cloudflare Pages: Edit

### `NPM_TOKEN`

**Purpose:** Publish packages to npm registry

**Status:** Not yet needed

---

## Secret Management Best Practices

### Security

✅ **DO:**

- Use fine-grained tokens (not classic PATs)
- Set minimal permissions (principle of least privilege)
- Set expiration dates (90 days recommended)
- Rotate tokens regularly
- Document all secrets in this file

❌ **DON'T:**

- Never commit secrets to code
- Never log secrets in workflows
- Never share secrets via email/chat
- Don't grant more permissions than needed

### Adding a New Secret

1. **Generate the secret** (token, API key, etc.)
2. **Add to repository:**
   - Go to **Settings > Secrets and variables > Actions** in your repository
   - Click "New repository secret"
   - Enter name and value
   - Click "Add secret"
3. **Document it here** with:
   - Purpose
   - Permissions needed
   - Which workflows use it
   - Rotation schedule
4. **Update audit trail table** below

---

## Audit Trail

| Secret     | Created | By  | Expires | Last Rotated | Status |
| ---------- | ------- | --- | ------- | ------------ | ------ |
| _None yet_ | -       | -   | -       | -            | -      |

**Update this table when adding/rotating secrets.**

---

## Contact

If you need access to secrets or have questions:

- Repository Admin: @borealBytes
- Security Issues: Create issue with `security` label

---

**Last updated:** 2026-01-17
**Maintainer:** @borealBytes
