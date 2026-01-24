#!/bin/bash
#
# Manage custom domain for preview deployments
# This script ensures preview-startup-blueprint.SuperiorByteWorks.com points to the active preview
#
# Usage: bash manage-preview-domain.sh <project_name> <deployment_url>
# Example: bash manage-preview-domain.sh website https://abc123.website.pages.dev

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
  echo -e "${BLUE}▶${NC} $1"
}

# Validate environment variables
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  log_error "CLOUDFLARE_API_TOKEN is not set"
  exit 1
fi

if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  log_error "CLOUDFLARE_ACCOUNT_ID is not set"
  exit 1
fi

# Configuration
PROJECT_NAME="${1:-website}"
DEPLOYMENT_URL="${2:-}"
CUSTOM_DOMAIN="preview-startup-blueprint.SuperiorByteWorks.com"
BASE_DOMAIN="SuperiorByteWorks.com"
SUBDOMAIN="preview-startup-blueprint"

if [ -z "$DEPLOYMENT_URL" ]; then
  log_error "Usage: $0 <project_name> <deployment_url>"
  log_error "Example: $0 website https://abc123.website.pages.dev"
  exit 1
fi

echo ""
echo "🌐 Custom Preview Domain Management"
echo "═══════════════════════════════════════"
echo "Project: $PROJECT_NAME"
echo "Domain: $CUSTOM_DOMAIN"
echo "Target: $DEPLOYMENT_URL"
echo ""

# Extract deployment domain from URL (e.g., abc123.website.pages.dev)
DEPLOYMENT_DOMAIN=$(echo "$DEPLOYMENT_URL" | sed -E 's|https?://([^/]+).*|\1|')
log_info "Deployment domain: $DEPLOYMENT_DOMAIN"

# Step 1: Get Zone ID for base domain
log_step "Step 1: Finding zone ID for $BASE_DOMAIN"

ZONE_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$BASE_DOMAIN" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json")

ZONE_ID=$(echo "$ZONE_RESPONSE" | jq -r '.result[0].id // empty')

if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" == "null" ]; then
  log_error "Failed to find zone ID for $BASE_DOMAIN"
  echo "Response: $ZONE_RESPONSE" | jq .
  exit 1
fi

log_info "Found zone ID: $ZONE_ID"

# Step 2: Remove custom domain from ALL Cloudflare Pages projects
log_step "Step 2: Removing custom domain from any existing projects"

# List all Pages projects
PROJECTS_RESPONSE=$(curl -s -X GET \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json")

PROJECTS=$(echo "$PROJECTS_RESPONSE" | jq -r '.result[].name // empty')

if [ -n "$PROJECTS" ]; then
  for project in $PROJECTS; do
    log_info "Checking project: $project"
    
    # List custom domains for this project
    DOMAINS_RESPONSE=$(curl -s -X GET \
      "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$project/domains" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json")
    
    HAS_DOMAIN=$(echo "$DOMAINS_RESPONSE" | jq -r ".result[] | select(.name == \"$CUSTOM_DOMAIN\") | .name // empty")
    
    if [ -n "$HAS_DOMAIN" ]; then
      log_warn "Found custom domain on project $project, removing..."
      
      DELETE_RESPONSE=$(curl -s -X DELETE \
        "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$project/domains/$CUSTOM_DOMAIN" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json")
      
      if echo "$DELETE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        log_info "Removed custom domain from $project"
      else
        log_warn "Failed to remove from $project (may not exist): $(echo "$DELETE_RESPONSE" | jq -r '.errors[0].message // "Unknown error"')"
      fi
    fi
  done
else
  log_warn "No Pages projects found"
fi

# Step 3: Add custom domain to current project
log_step "Step 3: Adding custom domain to $PROJECT_NAME"

ADD_RESPONSE=$(curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$PROJECT_NAME/domains" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$CUSTOM_DOMAIN\"}")

if echo "$ADD_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
  log_info "Successfully added custom domain to $PROJECT_NAME"
else
  # Check if it already exists (which is fine)
  ERROR_CODE=$(echo "$ADD_RESPONSE" | jq -r '.errors[0].code // empty')
  if [ "$ERROR_CODE" == "8000007" ] || echo "$ADD_RESPONSE" | grep -q "already exists"; then
    log_info "Custom domain already exists on $PROJECT_NAME (OK)"
  else
    log_error "Failed to add custom domain"
    echo "$ADD_RESPONSE" | jq .
    exit 1
  fi
fi

# Step 4: Create or update DNS CNAME record
log_step "Step 4: Managing DNS CNAME record"

# Check if DNS record already exists
DNS_RECORDS_RESPONSE=$(curl -s -X GET \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=CNAME&name=$CUSTOM_DOMAIN" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json")

RECORD_ID=$(echo "$DNS_RECORDS_RESPONSE" | jq -r '.result[0].id // empty')

if [ -n "$RECORD_ID" ] && [ "$RECORD_ID" != "null" ]; then
  log_info "Found existing DNS record, updating..."
  
  UPDATE_RESPONSE=$(curl -s -X PATCH \
    "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"CNAME\",
      \"name\": \"$SUBDOMAIN\",
      \"content\": \"$DEPLOYMENT_DOMAIN\",
      \"ttl\": 1,
      \"proxied\": true
    }")
  
  if echo "$UPDATE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    log_info "DNS record updated successfully"
  else
    log_error "Failed to update DNS record"
    echo "$UPDATE_RESPONSE" | jq .
    exit 1
  fi
else
  log_info "Creating new DNS record..."
  
  CREATE_RESPONSE=$(curl -s -X POST \
    "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"CNAME\",
      \"name\": \"$SUBDOMAIN\",
      \"content\": \"$DEPLOYMENT_DOMAIN\",
      \"ttl\": 1,
      \"proxied\": true
    }")
  
  if echo "$CREATE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    log_info "DNS record created successfully"
  else
    log_error "Failed to create DNS record"
    echo "$CREATE_RESPONSE" | jq .
    exit 1
  fi
fi

# Step 5: Verify setup
log_step "Step 5: Verifying setup"

# Check custom domain status
STATUS_RESPONSE=$(curl -s -X GET \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$PROJECT_NAME/domains/$CUSTOM_DOMAIN" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json")

STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.result.status // "unknown"')

log_info "Custom domain status: $STATUS"

if [ "$STATUS" == "active" ] || [ "$STATUS" == "pending" ]; then
  log_info "Custom domain is active or pending verification"
else
  log_warn "Custom domain status is '$STATUS' - may need time to propagate"
fi

echo ""
echo "═══════════════════════════════════════"
log_info "✅ Custom domain setup complete!"
echo ""
log_info "Your preview is accessible at:"
echo "   🔗 https://$CUSTOM_DOMAIN"
echo ""
log_info "DNS propagation may take 1-2 minutes"
echo ""
