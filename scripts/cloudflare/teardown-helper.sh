#!/bin/bash
# Cleanup utilities for preview deployments
# shellcheck source=scripts/cloudflare/deploy-helper.sh

set -euo pipefail

source "$(dirname "$0")/deploy-helper.sh"

# Remove preview deployment
teardown_preview() {
  local APP_NAME=$1
  local BRANCH=$2
  
  log_warn "Tearing down preview for ${APP_NAME} (${BRANCH})"
  
  # Delete Pages deployment
  wrangler pages deployment list --project-name="${APP_NAME}" \
    | grep "${BRANCH}" \
    | xargs -I {} wrangler pages deployment delete {} || true
  
  log_info "Preview deployment removed"
}

# Delete test database
cleanup_d1_database() {
  local DB_NAME=$1
  
  log_warn "Deleting D1 database: ${DB_NAME}"
  wrangler d1 delete "${DB_NAME}" --force || true
  log_info "Database deleted"
}

# Delete R2 bucket (empties first)
cleanup_r2_bucket() {
  local BUCKET_NAME=$1
  
  log_warn "Deleting R2 bucket: ${BUCKET_NAME}"
  
  # Empty bucket first
  wrangler r2 object list "${BUCKET_NAME}" \
    | jq -r '.[].key' \
    | xargs -I {} wrangler r2 object delete "${BUCKET_NAME}/{}" || true
  
  # Delete bucket
  wrangler r2 bucket delete "${BUCKET_NAME}" --force || true
  log_info "Bucket deleted"
}

# Main teardown function
main() {
  local APP_NAME=${1:-startup-blueprint}
  local BRANCH=${2:-$(git branch --show-current)}
  
  echo "🧹 Starting teardown for ${APP_NAME} (${BRANCH})"
  
  teardown_preview "${APP_NAME}" "${BRANCH}"
  
  echo "✅ Teardown complete"
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
  main "$@"
fi
