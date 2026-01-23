#!/bin/bash
# Credential Validation Script
# Tests all environment variables and secrets required for startup-blueprint
# Outputs formatted markdown table to GitHub Actions summary

set -euo pipefail

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Output file for GitHub Actions summary
SUMMARY_FILE="/tmp/credential-validation-summary.md"
RESULT_FILE="/tmp/credential-validation-result"

# Initialize result
OVERALL_RESULT=0

# Initialize summary markdown
cat > "$SUMMARY_FILE" << 'EOF'
### Credential Status

| Service | Credential | Type | Value | Status |
|---------|------------|------|-------|--------|
EOF

log_info() {
  echo -e "${GREEN}\u2713${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}\u26a0${NC} $1"
}

log_error() {
  echo -e "${RED}\u2717${NC} $1"
}

# Function to add row to table
add_row() {
  local service="$1"
  local credential="$2"
  local type="$3"
  local value="$4"
  local status="$5"
  
  echo "| $service | $credential | $type | $value | $status |" >> "$SUMMARY_FILE"
}

# Function to validate Cloudflare credentials
validate_cloudflare() {
  local cf_status=""
  local token_status=""
  local account_status=""
  
  echo ""
  echo "=== Validating Cloudflare Credentials ==="
  
  # Check if CLOUDFLARE_API_TOKEN is set
  if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
    log_error "CLOUDFLARE_API_TOKEN not set"
    token_status="\u274c Not Set"
    OVERALL_RESULT=1
  else
    log_info "CLOUDFLARE_API_TOKEN is set"
    
    # Test token validity with wrangler
    if wrangler whoami > /dev/null 2>&1; then
      log_info "Cloudflare API token is valid"
      token_status="\u2705 Valid"
      cf_status="\u2705 Valid"
    else
      log_error "Cloudflare API token is invalid or expired"
      token_status="\u274c Invalid"
      cf_status="\u274c Invalid"
      OVERALL_RESULT=1
    fi
  fi
  
  # Check if CLOUDFLARE_ACCOUNT_ID is set
  if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
    log_error "CLOUDFLARE_ACCOUNT_ID not set"
    account_status="\u274c Not Set"
    OVERALL_RESULT=1
  else
    log_info "CLOUDFLARE_ACCOUNT_ID is set: ${CLOUDFLARE_ACCOUNT_ID:0:8}..."
    account_status="\u2705 Set"
  fi
  
  # Add rows with rowspan logic (service column merged)
  add_row "**Cloudflare**" "API Token" "Secret" "\u2022\u2022\u2022\u2022\u2022\u2022\u2022" "$token_status"
  add_row "" "Account ID" "Secret" "${CLOUDFLARE_ACCOUNT_ID:0:8}\u2022\u2022\u2022" "$account_status"
  add_row "" "" "" "" "**$cf_status**"
}

# Function to validate Google OAuth credentials
validate_google() {
  local google_status=""
  local client_id_status=""
  local client_secret_status=""
  local redirect_uri_status=""
  
  echo ""
  echo "=== Validating Google OAuth Credentials ==="
  
  # Check GOOGLE_CLIENT_ID
  if [ -z "${GOOGLE_CLIENT_ID:-}" ]; then
    log_error "GOOGLE_CLIENT_ID not set"
    client_id_status="\u274c Not Set"
    google_status="\u274c Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_CLIENT_ID is set"
    
    # Validate format (should end with .apps.googleusercontent.com)
    if [[ "$GOOGLE_CLIENT_ID" =~ apps\.googleusercontent\.com$ ]]; then
      log_info "GOOGLE_CLIENT_ID format is valid"
      client_id_status="\u2705 Valid Format"
    else
      log_warn "GOOGLE_CLIENT_ID format may be invalid"
      client_id_status="\u26a0\ufe0f Invalid Format"
      OVERALL_RESULT=1
    fi
  fi
  
  # Check GOOGLE_CLIENT_SECRET
  if [ -z "${GOOGLE_CLIENT_SECRET:-}" ]; then
    log_error "GOOGLE_CLIENT_SECRET not set"
    client_secret_status="\u274c Not Set"
    google_status="\u274c Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_CLIENT_SECRET is set"
    
    # Validate format (should start with GOCSPX-)
    if [[ "$GOOGLE_CLIENT_SECRET" =~ ^GOCSPX- ]]; then
      log_info "GOOGLE_CLIENT_SECRET format is valid"
      client_secret_status="\u2705 Valid Format"
    else
      log_warn "GOOGLE_CLIENT_SECRET format may be invalid"
      client_secret_status="\u26a0\ufe0f Invalid Format"
      OVERALL_RESULT=1
    fi
  fi
  
  # Check GOOGLE_REDIRECT_URI
  if [ -z "${GOOGLE_REDIRECT_URI:-}" ]; then
    log_error "GOOGLE_REDIRECT_URI not set"
    redirect_uri_status="\u274c Not Set"
    google_status="\u274c Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_REDIRECT_URI is set: $GOOGLE_REDIRECT_URI"
    
    # Validate format (should be https URL with /auth/callback)
    if [[ "$GOOGLE_REDIRECT_URI" =~ ^https://.*\.SuperiorByteWorks\.com/auth/callback$ ]]; then
      log_info "GOOGLE_REDIRECT_URI format is valid"
      redirect_uri_status="\u2705 Valid Format"
    else
      log_warn "GOOGLE_REDIRECT_URI format may be invalid (expected: https://*.SuperiorByteWorks.com/auth/callback)"
      redirect_uri_status="\u26a0\ufe0f Invalid Format"
    fi
  fi
  
  # Test OAuth endpoint (simple HTTP check)
  echo "Testing Google OAuth endpoint..."
  if curl -s --head https://accounts.google.com/o/oauth2/v2/auth | grep -q "200 OK\|302 Found\|400"; then
    log_info "Google OAuth endpoint is reachable"
    if [ "$google_status" != "\u274c Invalid" ]; then
      google_status="\u2705 Valid"
    fi
  else
    log_error "Google OAuth endpoint unreachable"
    google_status="\u274c Unreachable"
    OVERALL_RESULT=1
  fi
  
  # Add rows
  add_row "**Google OAuth**" "Client ID" "Secret" "${GOOGLE_CLIENT_ID:0:12}\u2022\u2022\u2022" "$client_id_status"
  add_row "" "Client Secret" "Secret" "\u2022\u2022\u2022\u2022\u2022\u2022\u2022" "$client_secret_status"
  add_row "" "Redirect URI" "Variable" "$GOOGLE_REDIRECT_URI" "$redirect_uri_status"
  add_row "" "" "" "" "**$google_status**"
}

# Function to validate OpenRouter API credentials
validate_openrouter() {
  local openrouter_status=""
  
  echo ""
  echo "=== Validating OpenRouter API Credentials ==="
  
  # Check if OPENROUTER_API_KEY is set
  if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    log_error "OPENROUTER_API_KEY not set"
    openrouter_status="\u274c Not Set"
    OVERALL_RESULT=1
  else
    log_info "OPENROUTER_API_KEY is set"
    
    # Validate format (should start with sk-or-v1-)
    if [[ "$OPENROUTER_API_KEY" =~ ^sk-or-v1- ]]; then
      log_info "OPENROUTER_API_KEY format is valid"
      
      # Test API key with actual API call to models endpoint
      echo "Testing OpenRouter API..."
      HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        -H "Content-Type: application/json" \
        https://openrouter.ai/api/v1/models)
      
      if [ "$HTTP_CODE" == "200" ]; then
        log_info "OpenRouter API key is valid and active"
        openrouter_status="\u2705 Valid"
      elif [ "$HTTP_CODE" == "401" ]; then
        log_error "OpenRouter API key is invalid or expired (401 Unauthorized)"
        openrouter_status="\u274c Invalid/Expired"
        OVERALL_RESULT=1
      elif [ "$HTTP_CODE" == "429" ]; then
        log_warn "OpenRouter API rate limited (429) - key is valid but rate limited"
        openrouter_status="\u26a0\ufe0f Rate Limited"
      else
        log_error "OpenRouter API returned unexpected status: $HTTP_CODE"
        openrouter_status="\u274c Error ($HTTP_CODE)"
        OVERALL_RESULT=1
      fi
    else
      log_warn "OPENROUTER_API_KEY format may be invalid (expected: sk-or-v1-...)"
      openrouter_status="\u26a0\ufe0f Invalid Format"
      OVERALL_RESULT=1
    fi
  fi
  
  # Add row
  add_row "**OpenRouter**" "API Key" "Secret" "${OPENROUTER_API_KEY:0:12}\u2022\u2022\u2022" "$openrouter_status"
}

# Function to check optional/future credentials
validate_optional() {
  echo ""
  echo "=== Checking Optional Credentials ==="
  
  # GitHub Token (for API access, usually auto-provided in Actions)
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    log_info "GITHUB_TOKEN is available (auto-provided by Actions)"
    add_row "**GitHub**" "Token" "Auto-provided" "\u2022\u2022\u2022\u2022\u2022\u2022\u2022" "\u2705 Available"
  else
    log_warn "GITHUB_TOKEN not available (expected in Actions context)"
    add_row "**GitHub**" "Token" "Auto-provided" "-" "\u26a0\ufe0f Not Available"
  fi
}

# Main execution
echo "========================================"
echo "Credential Validation for startup-blueprint"
echo "========================================"
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Run all validations
validate_cloudflare
validate_google
validate_openrouter
validate_optional

# Add footer to summary
cat >> "$SUMMARY_FILE" << EOF

### Legend

- \u2705 **Valid**: Credential is properly configured and validated
- \u26a0\ufe0f **Warning**: Credential is set but format may be invalid or rate limited
- \u274c **Invalid**: Credential is missing, expired, or invalid
- **Bold rows**: Overall service status

### Actions Required

If any credentials show as invalid:

1. **Cloudflare**: Regenerate API token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. **Google OAuth**: Update credentials at [console.cloud.google.com](https://console.cloud.google.com/apis/credentials)
3. **OpenRouter**: Regenerate API key at [openrouter.ai/keys](https://openrouter.ai/keys)
4. **Secrets**: Update in repo settings at Settings \u2192 Secrets and variables \u2192 Actions

### Testing Credentials

To test credentials locally:

\\\`\\\`\\\`bash
bash scripts/validate-credentials.sh
\\\`\\\`\\\`
EOF

# Print summary
echo ""
echo "========================================"
if [ $OVERALL_RESULT -eq 0 ]; then
  log_info "All credentials validated successfully!"
  echo "\u2705 PASS" > "$RESULT_FILE"
else
  log_error "Credential validation failed. Check the summary for details."
  echo "\u274c FAIL" > "$RESULT_FILE"
fi
echo "========================================"

# Save result code
echo "$OVERALL_RESULT" > "$RESULT_FILE"

exit $OVERALL_RESULT
