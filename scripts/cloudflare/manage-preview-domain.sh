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

# Step 2: Remove custom domain from ALL Pages projects (cleanup)
log_step "Checking for existing custom domain assignments..."

# Get all Pages projects
PROJECTS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

PROJECT_COUNT=$(echo "$PROJECTS_RESPONSE" | jq -r '.result | length')
log_info "Found $PROJECT_COUNT Pages project(s)"

# Store project names in an array
mapfile -t PROJECT_NAMES < <(echo "$PROJECTS_RESPONSE" | jq -r '.result[].name')

REMOVED_COUNT=0

# Iterate through each project
for proj_name in "${PROJECT_NAMES[@]}"; do
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
  log_info "Custom domain not assigned to any projects"
fi

# Step 3: Verify domain is not assigned anywhere
log_step "Verifying domain is free..."

for proj_name in "${PROJECT_NAMES[@]}"; do
  VERIFY_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${proj_name}/domains" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json")
  
  STILL_HAS=$(echo "$VERIFY_RESPONSE" | jq -r --arg domain "$CUSTOM_DOMAIN" '.result[]? | select(.name == $domain) | .name' 2>/dev/null || echo "")
  
  if [ -n "$STILL_HAS" ]; then
    log_error "Domain still assigned to $proj_name after removal attempt"
    exit 1
  fi
done

log_info "Domain is free and ready to assign"

# Step 4: Add custom domain to current project
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
  log_error "Failed to add custom domain"
  echo "API Response:" 
  echo "$ADD_RESPONSE" | jq .
  
  # Try to get more info about why it failed
  ERROR_CODE=$(echo "$ADD_RESPONSE" | jq -r '.errors[0].code // "unknown"')
  ERROR_MSG=$(echo "$ADD_RESPONSE" | jq -r '.errors[0].message // "unknown"')
  
  log_error "Error code: $ERROR_CODE"
  log_error "Error message: $ERROR_MSG"
  
  if [ "$ERROR_CODE" = "8000018" ]; then
    log_error "Domain appears to still be in use. Manual cleanup may be required."
    log_error "Visit Cloudflare Dashboard → Pages → Projects to manually remove the domain."
  fi
  
  exit 1
fi

# Step 5: Get the CNAME target from Cloudflare Pages
log_step "Getting CNAME target for DNS..."

# The CNAME target is typically the project's pages.dev domain
CNAME_TARGET="${PROJECT_NAME}.pages.dev"

log_info "CNAME target: $CNAME_TARGET"

# Step 6: Update DNS record
log_step "Updating DNS CNAME record..."

# Check if DNS record already exists
DNS_RECORDS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=CNAME&name=${CUSTOM_DOMAIN}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

EXISTING_RECORD_ID=$(echo "$DNS_RECORDS_RESPONSE" | jq -r '.result[0].id // empty')

if [ -n "$EXISTING_RECORD_ID" ] && [ "$EXISTING_RECORD_ID" != "null" ]; then
  # Update existing record
  log_step "  Updating existing DNS record (ID: $EXISTING_RECORD_ID)..."
  
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
    echo "API Response:" | jq . <<< "$DNS_UPDATE_RESPONSE"
    exit 1
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
    echo "API Response:" | jq . <<< "$DNS_CREATE_RESPONSE"
    exit 1
  fi
fi

echo ""
log_info "✅ Custom domain configuration complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Your preview is accessible at: https://${CUSTOM_DOMAIN}"
echo "🔗 Direct URL: ${DEPLOYMENT_URL}"
echo ""
log_warn "Note: DNS propagation may take 1-2 minutes"
echo ""
