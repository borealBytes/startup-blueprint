# Shared Cloudflare Deployment Utilities

Reusable bash functions for deploying applications to Cloudflare infrastructure.

## Prerequisites

- wrangler CLI: `npm install -g wrangler`
- Cloudflare account with API token
- Environment variables set (see below)

## Environment Variables

```bash
export CLOUDFLARE_API_TOKEN="your-api-token"
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
```

## Usage

### Source in your app-specific scripts

```bash
source ../../scripts/cloudflare/deploy-helper.sh

setup_d1_database "my_database" "path/to/schema.sql"
setup_r2_bucket "my-bucket"
deploy_pages "my-app" "main" "my-app.example.com"
```

### Available Functions

- `check_wrangler()` - Verify wrangler CLI is installed
- `setup_d1_database(name, schema_file)` - Create/update D1 database
- `setup_r2_bucket(name)` - Create R2 bucket
- `setup_kv_namespace(name)` - Create KV namespace
- `deploy_pages(app, branch, subdomain)` - Deploy to Cloudflare Pages
- `deploy_workers(app, branch)` - Deploy Cloudflare Workers

### Idempotency Guarantee

All setup functions check for existing resources before creation.
Running twice will NOT create duplicates or error.

## Cleanup

```bash
bash scripts/cloudflare/teardown-helper.sh my-app my-branch
```
