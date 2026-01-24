#!/bin/bash
# Manage custom preview domain for Cloudflare Pages deployment
# Removes old domain assignment and adds to current deployment

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

log_step() {
  echo -e "${BLUE}→${NC} $1"
}

# Configuration
PROJECT_NAME="${1:-startup-blueprint}"
DEPLOYMENT_URL="${2:-}"
CUSTOM_DOMAIN="preview-startup-blueprint.SuperiorByteWorks.com"
BASE_DOMAIN="SuperiorByteWorks.com"
SUBDOMAIN="preview-startup-blueprint"

# Check required environment variables
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  log_error "CLOUDFLARE_API_TOKEN environment variable is required"
  exit 1
fi

if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  log_error "CLOUDFLARE_ACCOUNT_ID environment variable is required"
  exit 1
fi

if [ -z "$DEPLOYMENT_URL" ]; then
  log_error "Deployment URL is required as second argument"
  exit 1
fi

echo ""
log_step "🌐 Managing Custom Preview Domain"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PROJECT_NAME"
echo "Custom Domain: $CUSTOM_DOMAIN"
echo "Deployment URL: $DEPLOYMENT_URL"
echo ""

# Step 1: Get Zone ID for base domain
log_step "Finding Zone ID for $BASE_DOMAIN..."

ZONE_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${BASE_DOMAIN}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

ZONE_ID=$(echo "$ZONE_RESPONSE" | jq -r '.result[0].id // empty')

if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" = "null" ]; then
  log_error "Could not find Zone ID for $BASE_DOMAIN"
  echo "API Response: $ZONE_RESPONSE" | jq .
  exit 1
fi

log_info "Found Zone ID: $ZONE_ID"

# Step 2: Check if domain is already assigned to current project
log_step "Checking if $CUSTOM_DOMAIN is already assigned to $PROJECT_NAME..."

CURRENT_DOMAINS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PROJECT_NAME}/domains" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

# Check if our custom domain is already assigned to THIS project
ALREADY_ASSIGNED=$(echo "$CURRENT_DOMAINS_RESPONSE" | jq -r --arg domain "$CUSTOM_DOMAIN" '.result[]? | select(.name == $domain) | .name' 2>/dev/null || echo "")

if [ -n "$ALREADY_ASSIGNED" ] && [ "$ALREADY_ASSIGNED" = "$CUSTOM_DOMAIN" ]; then
  log_info "✅ Custom domain already assigned to $PROJECT_NAME (idempotent - no action needed)"
  SKIP_DOMAIN_ADD=true
else
  log_info "Custom domain not yet assigned to $PROJECT_NAME"
  SKIP_DOMAIN_ADD=false

  # Step 3: Remove custom domain from OTHER Pages projects (cleanup)
  log_step "Checking for assignments to other projects..."

  # Get all Pages projects
  PROJECTS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json")

  PROJECT_COUNT=$(echo "$PROJECTS_RESPONSE" | jq -r '.result | length')
  log_info "Found $PROJECT_COUNT Pages project(s)"

  # Store project names in an array
  mapfile -t PROJECT_NAMES < <(echo "$PROJECTS_RESPONSE" | jq -r '.result[].name')

  REMOVED_COUNT=0

  # Iterate through each project (except current one)
  for proj_name in "${PROJECT_NAMES[@]}"; do
    # Skip current project
    if [ "$proj_name" = "$PROJECT_NAME" ]; then
      continue
    fi

    log_step "  Checking project: $proj_name"

    # Get domains for this project
    DOMAINS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${proj_name}/domains" \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json")

    # Check if our custom domain is assigned to this project
    HAS_DOMAIN=$(echo "$DOMAINS_RESPONSE" | jq -r --arg domain "$CUSTOM_DOMAIN" '.result[]? | select(.name == $domain) | .name' 2>/dev/null || echo "")

    if [ -n "$HAS_DOMAIN" ] && [ "$HAS_DOMAIN" = "$CUSTOM_DOMAIN" ]; then
      log_warn "    Found $CUSTOM_DOMAIN assigned to $proj_name - removing..."

      DELETE_RESPONSE=$(curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${proj_name}/domains/${CUSTOM_DOMAIN}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
        -H "Content-Type: application/json")

      DELETE_SUCCESS=$(echo "$DELETE_RESPONSE" | jq -r '.success')

      if [ "$DELETE_SUCCESS" = "true" ]; then
        log_info "    Successfully removed from $proj_name"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))

        # Wait a moment for the API to propagate the change
        sleep 2
      else
        log_warn "    Failed to remove from $proj_name"
        echo "    API Response: $(echo "$DELETE_RESPONSE" | jq -c .)"
      fi
    else
      log_info "    Not assigned to $proj_name"
    fi
  done

  if [ $REMOVED_COUNT -gt 0 ]; then
    log_info "Removed custom domain from $REMOVED_COUNT project(s)"
    log_step "Waiting for domain removal to propagate..."
    sleep 3
  else
    log_info "Custom domain not assigned to any other projects"
  fi
fi

# Step 4: Add custom domain to current project (if not already assigned)
if [ "$SKIP_DOMAIN_ADD" = "false" ]; then
  log_step "Adding $CUSTOM_DOMAIN to $PROJECT_NAME..."

  ADD_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PROJECT_NAME}/domains" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"${CUSTOM_DOMAIN}\"
    }")

  ADD_SUCCESS=$(echo "$ADD_RESPONSE" | jq -r '.success')

  if [ "$ADD_SUCCESS" = "true" ]; then
    log_info "Successfully added custom domain to $PROJECT_NAME"
  else
    # Check if error is because domain is already added (race condition)
    ERROR_CODE=$(echo "$ADD_RESPONSE" | jq -r '.errors[0].code // "unknown"')
    ERROR_MSG=$(echo "$ADD_RESPONSE" | jq -r '.errors[0].message // "unknown"')

    if [ "$ERROR_CODE" = "8000018" ]; then
      # Domain already added - this is OK (idempotent)
      log_warn "Domain already added (error 8000018) - continuing (idempotent)"
    else
      log_error "Failed to add custom domain"
      echo "API Response:"
      echo "$ADD_RESPONSE" | jq .
      log_error "Error code: $ERROR_CODE"
      log_error "Error message: $ERROR_MSG"
      exit 1
    fi
  fi
fi

# Step 5: Get the CNAME target from deployment URL
log_step "Extracting CNAME target from deployment URL..."

# Extract hostname from deployment URL (e.g., https://abc123.website-c9f.pages.dev -> abc123.website-c9f.pages.dev)
CNAME_TARGET=$(echo "$DEPLOYMENT_URL" | sed -E 's|https?://([^/]+).*|\1|')

if [ -z "$CNAME_TARGET" ] || [ "$CNAME_TARGET" = "$DEPLOYMENT_URL" ]; then
  log_error "Failed to extract hostname from deployment URL: $DEPLOYMENT_URL"
  exit 1
fi

log_info "CNAME target: $CNAME_TARGET"

# Step 6: Update DNS record
log_step "Updating DNS CNAME record..."

# Check if DNS record already exists
DNS_RECORDS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=CNAME&name=${CUSTOM_DOMAIN}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

EXISTING_RECORD_ID=$(echo "$DNS_RECORDS_RESPONSE" | jq -r '.result[0].id // empty')
EXISTING_CONTENT=$(echo "$DNS_RECORDS_RESPONSE" | jq -r '.result[0].content // empty')

if [ -n "$EXISTING_RECORD_ID" ] && [ "$EXISTING_RECORD_ID" != "null" ]; then
  # Check if record already points to correct target
  if [ "$EXISTING_CONTENT" = "$CNAME_TARGET" ]; then
    log_info "DNS record already points to correct target (idempotent - no update needed)"
  else
    # Update existing record
    log_step "  Updating existing DNS record (ID: $EXISTING_RECORD_ID)..."
    log_step "  Old target: $EXISTING_CONTENT"
    log_step "  New target: $CNAME_TARGET"

    DNS_UPDATE_RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${EXISTING_RECORD_ID}" \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"type\": \"CNAME\",
        \"name\": \"${SUBDOMAIN}\",
        \"content\": \"${CNAME_TARGET}\",
        \"ttl\": 1,
        \"proxied\": true
      }")

    DNS_SUCCESS=$(echo "$DNS_UPDATE_RESPONSE" | jq -r '.success')

    if [ "$DNS_SUCCESS" = "true" ]; then
      log_info "Successfully updated DNS record"
    else
      log_error "Failed to update DNS record"
      jq . <<< "$DNS_UPDATE_RESPONSE"
      exit 1
    fi
  fi
else
  # Create new record
  log_step "  Creating new DNS record..."

  DNS_CREATE_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"CNAME\",
      \"name\": \"${SUBDOMAIN}\",
      \"content\": \"${CNAME_TARGET}\",
      \"ttl\": 1,
      \"proxied\": true
    }")

  DNS_SUCCESS=$(echo "$DNS_CREATE_RESPONSE" | jq -r '.success')

  if [ "$DNS_SUCCESS" = "true" ]; then
    log_info "Successfully created DNS record"
  else
    log_error "Failed to create DNS record"
    jq . <<< "$DNS_CREATE_RESPONSE"
    exit 1
  fi
fi

echo ""
log_info "✅ Custom domain configuration complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Your preview is accessible at: https://${CUSTOM_DOMAIN}"
echo "🔗 Direct URL: ${DEPLOYMENT_URL}"
echo "📍 CNAME target: ${CNAME_TARGET}"
echo ""
log_warn "Note: DNS propagation may take 1-2 minutes"
echo ""
