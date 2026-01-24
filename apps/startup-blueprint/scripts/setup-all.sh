#!/bin/bash
# Complete setup orchestration for startup-blueprint

set -euo pipefail

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "${SCRIPT_DIR}")"
REPO_ROOT="$(dirname "$(dirname "${APP_DIR}")")"

# Source shared utilities
source "${REPO_ROOT}/scripts/cloudflare/deploy-helper.sh"

# Configuration
APP_NAME="startup-blueprint"
BRANCH="${1:-$(git branch --show-current)}"
BASE_DOMAIN="startup-blueprint.SuperiorByteWorks.com"
SUBDOMAIN="${BRANCH}.${BASE_DOMAIN}"
DB_NAME="startup_blueprint_db"
BUCKET_NAME="startup-blueprint-assets"
KV_NAME="startup-blueprint-sessions"

echo "🚀 Setting up Startup Blueprint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Branch: ${BRANCH}"
echo "URL: https://${SUBDOMAIN}"
echo ""

# Check prerequisites
check_wrangler

# Setup infrastructure
log_info "Setting up Cloudflare infrastructure..."
setup_d1_database "${DB_NAME}" "${APP_DIR}/data/schema.sql"
setup_r2_bucket "${BUCKET_NAME}"
setup_kv_namespace "${KV_NAME}"

# Deploy
log_info "Deploying application..."
deploy_pages "${APP_NAME}" "${BRANCH}" "${SUBDOMAIN}"
deploy_workers "${APP_NAME}" "${BRANCH}"

# Seed demo data
log_info "Seeding demo data..."
bash "${SCRIPT_DIR}/seed-demo-data.sh" "${DB_NAME}"

echo ""
echo "✅ Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Visit: https://${SUBDOMAIN}"
echo ""
