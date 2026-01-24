# Shared Cloudflare Deployment Utilities

Reusable bash scripts for deploying applications to Cloudflare infrastructure and managing preview environments.

## Scripts Overview

| Script                     | Purpose                                         | Usage                   |
| -------------------------- | ----------------------------------------------- | ----------------------- |
| `deploy-helper.sh`         | Shared deployment functions (D1, R2, KV, Pages) | Source in other scripts |
| `manage-preview-domain.sh` | Custom domain management for previews           | Standalone executable   |
| `teardown-helper.sh`       | Cleanup preview deployments                     | Standalone executable   |

---

## Prerequisites

- **wrangler CLI**: `npm install -g wrangler`
- **jq**: `apt-get install jq` (for JSON processing in domain management)
- Cloudflare account with API token
- Environment variables set (see below)

## Environment Variables

```bash
export CLOUDFLARE_API_TOKEN="your-api-token"
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
```

### Required API Token Permissions

| Permission                     | Level | Used By                  |
| ------------------------------ | ----- | ------------------------ |
| **Account → Cloudflare Pages** | Edit  | All scripts              |
| **Zone → DNS**                 | Edit  | manage-preview-domain.sh |
| **Zone → Zone**                | Read  | manage-preview-domain.sh |

---

## 1. deploy-helper.sh

### Purpose

Shared bash functions for setting up Cloudflare resources (D1, R2, KV) and deploying Pages/Workers.

### Usage

**Source in your app-specific scripts:**

```bash
source ../../scripts/cloudflare/deploy-helper.sh

# Use the functions
check_wrangler
setup_d1_database "my_database" "path/to/schema.sql"
setup_r2_bucket "my-bucket"
setup_kv_namespace "my-sessions"
deploy_pages "my-app" "main" "my-app.example.com"
deploy_workers "my-app" "main"
```

### Available Functions

- `check_wrangler()` - Verify wrangler CLI is installed
- `log_info(message)` - Log success messages (green checkmark)
- `log_warn(message)` - Log warning messages (yellow)
- `log_error(message)` - Log error messages (red)
- `setup_d1_database(name, schema_file)` - Create/update D1 database
- `setup_r2_bucket(name)` - Create R2 bucket
- `setup_kv_namespace(name)` - Create KV namespace
- `deploy_pages(app, branch, subdomain)` - Deploy to Cloudflare Pages
- `deploy_workers(app, branch)` - Deploy Cloudflare Workers

### Idempotency Guarantee

All setup functions check for existing resources before creation. Running twice will **NOT** create duplicates or error.

---

## 2. manage-preview-domain.sh

### Purpose

Manage custom domain assignment for preview deployments. Ensures only one deployment has the preview domain at a time.

### Features

- 🧹 Removes custom domain from ALL Pages projects
- ➕ Adds custom domain to specified project
- 🌐 Creates/updates DNS CNAME record
- ✅ Idempotent and safe to run multiple times
- 📊 Detailed logging for troubleshooting

### Usage

```bash
bash scripts/cloudflare/manage-preview-domain.sh <project-name> <deployment-url>
```

**Example:**

```bash
bash scripts/cloudflare/manage-preview-domain.sh \
  "startup-blueprint" \
  "https://abc123.startup-blueprint.pages.dev"
```

### What It Does

1. Validates environment variables (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`)
2. Finds Zone ID for base domain (`SuperiorByteWorks.com`)
3. Lists all Cloudflare Pages projects
4. **Removes** `preview-startup-blueprint.SuperiorByteWorks.com` from ANY project that has it
5. **Adds** the custom domain to the specified project
6. Creates or updates DNS CNAME record pointing to `<project-name>.pages.dev`

### Configuration

**Edit these variables in the script to customize:**

```bash
CUSTOM_DOMAIN="preview-startup-blueprint.SuperiorByteWorks.com"
BASE_DOMAIN="SuperiorByteWorks.com"
SUBDOMAIN="preview-startup-blueprint"
```

### Requirements

- `jq` installed for JSON processing
- API token with **Zone.DNS:Edit** and **Zone.Zone:Read** permissions

### Exit Codes

- `0` - Success
- `1` - Error (missing env vars, API failures, invalid input)

---

## 3. teardown-helper.sh

### Purpose

Cleanup preview deployments and associated resources.

### Usage

```bash
bash scripts/cloudflare/teardown-helper.sh <app-name> <branch-name>
```

**Example:**

```bash
bash scripts/cloudflare/teardown-helper.sh "startup-blueprint" "preview-pr-42"
```

### What It Does

1. Deletes Pages deployment for specified branch
2. Optionally cleans up test databases (if configured)
3. Optionally empties and deletes R2 buckets (if configured)

### Main Functions

- `teardown_preview(app, branch)` - Remove preview deployment
- `cleanup_d1_database(name)` - Delete test database
- `cleanup_r2_bucket(name)` - Empty and delete R2 bucket

---

## Common Workflows

### Deploy Preview with Custom Domain

```bash
#!/bin/bash
set -euo pipefail

# Source helpers
source scripts/cloudflare/deploy-helper.sh

# Deploy to Pages
DEPLOY_URL=$(wrangler pages deploy ./dist \
  --project-name="startup-blueprint" \
  --branch="preview-pr-42" | grep -oP 'https://[^\s]+' | head -1)

echo "Deployed to: $DEPLOY_URL"

# Configure custom domain
bash scripts/cloudflare/manage-preview-domain.sh \
  "startup-blueprint" \
  "$DEPLOY_URL"

echo "Custom domain configured!"
```

### Cleanup Preview

```bash
bash scripts/cloudflare/teardown-helper.sh "startup-blueprint" "preview-pr-42"
```

---

## Troubleshooting

### "wrangler not found"

```bash
npm install -g wrangler
```

### "jq not found"

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### "Unauthorized" errors

Verify your API token:

```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json"
```

### "Zone not found"

Check Zone ID:

```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq
```

### Custom domain not working

1. **Wait 1-2 minutes** for DNS propagation
2. **Check DNS**: `dig preview-startup-blueprint.SuperiorByteWorks.com CNAME +short`
3. **Expected**: `startup-blueprint.pages.dev.`
4. **Check logs** in GitHub Actions for detailed error messages

---

## Security Best Practices

- ✅ **Never commit** `CLOUDFLARE_API_TOKEN` to git
- ✅ **Use GitHub Secrets** for CI/CD workflows
- ✅ **Rotate tokens** periodically
- ✅ **Limit token scope** to minimum required permissions
- ✅ **Use separate tokens** for dev/staging/prod if possible

---

## Related Documentation

- [Preview Deployment Custom Domain Guide](../../docs/preview-deployment-custom-domain.md)
- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [Cloudflare API Reference](https://developers.cloudflare.com/api/)
- [GitHub Workflows](../../.github/workflows/README.md)

---

**Last Updated**: 2026-01-24  
**Maintainer**: Clayton Young
