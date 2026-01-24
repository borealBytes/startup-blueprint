#!/bin/bash
# Shared Cloudflare deployment utilities

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
}

# Check if wrangler is installed
check_wrangler() {
  if ! command -v wrangler &> /dev/null; then
    log_error "wrangler CLI not found. Install: npm install -g wrangler"
    exit 1
  fi
  log_info "wrangler CLI found"
}

# Idempotent D1 database setup
setup_d1_database() {
  local DB_NAME=$1
  local SCHEMA_FILE=$2
  
  log_info "Setting up D1 database: ${DB_NAME}"
  
  # Check if database exists
  if wrangler d1 list | grep -q "${DB_NAME}"; then
    log_warn "Database ${DB_NAME} already exists, skipping creation"
  else
    wrangler d1 create "${DB_NAME}"
    log_info "Created D1 database: ${DB_NAME}"
  fi
  
  # Apply schema if provided
  if [ -n "${SCHEMA_FILE}" ] && [ -f "${SCHEMA_FILE}" ]; then
    wrangler d1 execute "${DB_NAME}" --file="${SCHEMA_FILE}"
    log_info "Applied schema from ${SCHEMA_FILE}"
  fi
}

# Idempotent R2 bucket setup
setup_r2_bucket() {
  local BUCKET_NAME=$1
  
  log_info "Setting up R2 bucket: ${BUCKET_NAME}"
  
  # Check if bucket exists
  if wrangler r2 bucket list | grep -q "${BUCKET_NAME}"; then
    log_warn "Bucket ${BUCKET_NAME} already exists, skipping creation"
  else
    wrangler r2 bucket create "${BUCKET_NAME}"
    log_info "Created R2 bucket: ${BUCKET_NAME}"
  fi
}

# Idempotent KV namespace setup
setup_kv_namespace() {
  local NAMESPACE_NAME=$1
  
  log_info "Setting up KV namespace: ${NAMESPACE_NAME}"
  
  # Check if namespace exists
  if wrangler kv:namespace list | grep -q "${NAMESPACE_NAME}"; then
    log_warn "KV namespace ${NAMESPACE_NAME} already exists, skipping creation"
  else
    wrangler kv:namespace create "${NAMESPACE_NAME}"
    log_info "Created KV namespace: ${NAMESPACE_NAME}"
  fi
}

# Deploy Cloudflare Pages
deploy_pages() {
  local APP_NAME=$1
  local BRANCH=$2
  local SUBDOMAIN=$3
  
  log_info "Deploying Pages: ${APP_NAME} to ${SUBDOMAIN}"
  
  # Deploy using wrangler pages deploy
  wrangler pages deploy "apps/${APP_NAME}/src/pages" \
    --project-name="${APP_NAME}" \
    --branch="${BRANCH}"
  
  log_info "Pages deployed successfully"
}

# Deploy Cloudflare Workers
deploy_workers() {
  local APP_NAME=$1
  local BRANCH=$2
  
  log_info "Deploying Workers for ${APP_NAME}"
  
  cd "apps/${APP_NAME}"
  wrangler deploy
  cd -
  
  log_info "Workers deployed successfully"
}
