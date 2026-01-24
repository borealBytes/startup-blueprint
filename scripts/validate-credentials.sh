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
  echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
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
    token_status="❌ Not Set"
    cf_status="❌ Invalid"
    OVERALL_RESULT=1
  else
    log_info "CLOUDFLARE_API_TOKEN is set"
    
    # Verify token with wrangler (works with both User and Account tokens)
    echo "Testing Cloudflare credentials with wrangler..."
    if wrangler whoami > /dev/null 2>&1; then
      log_info "Cloudflare API token verified via wrangler"
      token_status="✅ Valid"
      cf_status="✅ Valid"
    else
      log_error "Cloudflare API token is invalid or expired (wrangler test failed)"
      token_status="❌ Invalid"
      cf_status="❌ Invalid"
      OVERALL_RESULT=1
    fi
  fi
  
  # Check if CLOUDFLARE_ACCOUNT_ID is set
  if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
    log_error "CLOUDFLARE_ACCOUNT_ID not set"
    account_status="❌ Not Set"
    if [ "$cf_status" != "❌ Invalid" ]; then
      cf_status="❌ Invalid"
    fi
    OVERALL_RESULT=1
  else
    log_info "CLOUDFLARE_ACCOUNT_ID is set: ${CLOUDFLARE_ACCOUNT_ID:0:8}..."
    
    # Test account access with API (should work with Account tokens)
    if [ -n "${CLOUDFLARE_API_TOKEN:-}" ] && [ "$token_status" == "✅ Valid" ]; then
      echo "Testing Cloudflare account access..."
      ACCOUNT_RESPONSE=$(curl -s \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID")
      
      if echo "$ACCOUNT_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        log_info "Cloudflare account access verified"
        account_status="✅ Valid"
      else
        ERROR_MSG=$(echo "$ACCOUNT_RESPONSE" | jq -r '.errors[0].message // "Unknown error"' 2>/dev/null)
        log_error "Cannot access Cloudflare account: $ERROR_MSG"
        log_error "Check that your API token has 'Account Settings:Read' permission"
        account_status="❌ Cannot Access"
        cf_status="❌ Invalid"
        OVERALL_RESULT=1
      fi
    else
      account_status="✅ Set"
    fi
  fi
  
  # Add rows with rowspan logic (service column merged)
  add_row "**Cloudflare**" "API Token" "Secret" "•••••••" "$token_status"
  add_row "" "Account ID" "Secret" "${CLOUDFLARE_ACCOUNT_ID:0:8}•••" "$account_status"
  add_row "" "" "" "" "**$cf_status**"
}

# Function to validate Google OAuth credentials
validate_google() {
  local google_status=""
  local client_id_status=""
  local client_secret_status=""
  local redirect_uri_status=""
  local credentials_valid=false
  
  echo ""
  echo "=== Validating Google OAuth Credentials ==="
  
  # Check GOOGLE_CLIENT_ID
  if [ -z "${GOOGLE_CLIENT_ID:-}" ]; then
    log_error "GOOGLE_CLIENT_ID not set"
    client_id_status="❌ Not Set"
    google_status="❌ Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_CLIENT_ID is set"
    
    # Validate format (should end with .apps.googleusercontent.com)
    if [[ "$GOOGLE_CLIENT_ID" =~ apps\.googleusercontent\.com$ ]]; then
      log_info "GOOGLE_CLIENT_ID format is valid"
      client_id_status="✅ Valid Format"
      credentials_valid=true
    else
      log_error "GOOGLE_CLIENT_ID format is invalid (must end with .apps.googleusercontent.com)"
      client_id_status="❌ Invalid Format"
      google_status="❌ Invalid"
      OVERALL_RESULT=1
    fi
  fi
  
  # Check GOOGLE_CLIENT_SECRET
  if [ -z "${GOOGLE_CLIENT_SECRET:-}" ]; then
    log_error "GOOGLE_CLIENT_SECRET not set"
    client_secret_status="❌ Not Set"
    google_status="❌ Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_CLIENT_SECRET is set"
    
    # Validate format (should start with GOCSPX-)
    if [[ "$GOOGLE_CLIENT_SECRET" =~ ^GOCSPX- ]]; then
      log_info "GOOGLE_CLIENT_SECRET format is valid"
      client_secret_status="✅ Valid Format"
    else
      log_error "GOOGLE_CLIENT_SECRET format is invalid (must start with GOCSPX-)"
      client_secret_status="❌ Invalid Format"
      google_status="❌ Invalid"
      OVERALL_RESULT=1
      credentials_valid=false
    fi
  fi
  
  # Check GOOGLE_REDIRECT_URI
  if [ -z "${GOOGLE_REDIRECT_URI:-}" ]; then
    log_error "GOOGLE_REDIRECT_URI not set"
    redirect_uri_status="❌ Not Set"
    google_status="❌ Invalid"
    OVERALL_RESULT=1
  else
    log_info "GOOGLE_REDIRECT_URI is set: $GOOGLE_REDIRECT_URI"
    
    # Validate format - accept both localhost (dev) and production URLs
    if [[ "$GOOGLE_REDIRECT_URI" =~ ^https?://localhost:[0-9]+/auth/callback$ ]] || 
       [[ "$GOOGLE_REDIRECT_URI" =~ ^https://.*\.SuperiorByteWorks\.com/auth/callback$ ]]; then
      log_info "GOOGLE_REDIRECT_URI format is valid"
      redirect_uri_status="✅ Valid Format"
    else
      log_warn "GOOGLE_REDIRECT_URI format may be invalid (expected: http://localhost:PORT/auth/callback or https://*.SuperiorByteWorks.com/auth/callback)"
      redirect_uri_status="⚠️ Check Format"
    fi
  fi
  
  # Verify credentials actually work by calling Google's OAuth2 API
  if [ "$credentials_valid" = true ]; then
    echo "Testing Google OAuth API connectivity..."
    
    # First verify Google's OAuth endpoint is accessible
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "https://accounts.google.com/.well-known/openid-configuration")
    
    if [ "$HTTP_CODE" != "200" ]; then
      log_error "Google OAuth endpoint unreachable (HTTP $HTTP_CODE)"
      google_status="❌ Unreachable"
      OVERALL_RESULT=1
    else
      log_info "Google OAuth endpoint is accessible"
      
      # Now verify credentials by making a token request
      echo "Verifying Google OAuth credentials with API..."
      RESPONSE=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
        -d "client_id=$GOOGLE_CLIENT_ID" \
        -d "client_secret=$GOOGLE_CLIENT_SECRET" \
        -d "grant_type=authorization_code" \
        -d "code=invalid_code_for_testing" \
        -d "redirect_uri=$GOOGLE_REDIRECT_URI" 2>&1)
      
      # Check the error response to determine credential validity
      if echo "$RESPONSE" | grep -q "invalid_client"; then
        log_error "Google OAuth credentials are invalid (client_id or client_secret wrong)"
        google_status="❌ Invalid Credentials"
        OVERALL_RESULT=1
      elif echo "$RESPONSE" | grep -q "invalid_grant\|invalid_request"; then
        # This is expected - the code is invalid, but credentials are accepted by Google
        log_info "Google OAuth credentials verified via API (client_id and client_secret are valid)"
        google_status="✅ Valid"
      elif echo "$RESPONSE" | grep -q "redirect_uri_mismatch"; then
        log_warn "Google OAuth credentials valid but redirect_uri may not be registered in Google Console"
        google_status="⚠️ Check Redirect URI"
      else
        # Unknown response, but credentials format is valid
        log_info "Google OAuth credentials format validated (full verification requires OAuth flow)"
        google_status="✅ Format Valid"
      fi
    fi
  fi
  
  # Add rows
  add_row "**Google OAuth**" "Client ID" "Secret" "${GOOGLE_CLIENT_ID:0:12}•••" "$client_id_status"
  add_row "" "Client Secret" "Secret" "•••••••" "$client_secret_status"
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
    openrouter_status="❌ Not Set"
    OVERALL_RESULT=1
  else
    log_info "OPENROUTER_API_KEY is set"
    
    # Validate format (should start with sk-or-v1-)
    if [[ "$OPENROUTER_API_KEY" =~ ^sk-or-v1- ]]; then
      log_info "OPENROUTER_API_KEY format is valid"
      
      # Test API key with actual API call to models endpoint
      echo "Testing OpenRouter API connectivity..."
      HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        -H "Content-Type: application/json" \
        https://openrouter.ai/api/v1/models)
      
      if [ "$HTTP_CODE" == "200" ]; then
        log_info "OpenRouter API key verified via API (valid and active)"
        openrouter_status="✅ Valid"
      elif [ "$HTTP_CODE" == "401" ]; then
        log_error "OpenRouter API key is invalid or expired (401 Unauthorized)"
        openrouter_status="❌ Invalid/Expired"
        OVERALL_RESULT=1
      elif [ "$HTTP_CODE" == "429" ]; then
        log_warn "OpenRouter API rate limited (429) - key is valid but rate limited"
        openrouter_status="⚠️ Rate Limited"
      else
        log_error "OpenRouter API returned unexpected status: $HTTP_CODE"
        openrouter_status="❌ Error ($HTTP_CODE)"
        OVERALL_RESULT=1
      fi
    else
      log_warn "OPENROUTER_API_KEY format may be invalid (expected: sk-or-v1-...)"
      openrouter_status="⚠️ Invalid Format"
      OVERALL_RESULT=1
    fi
  fi
  
  # Add row
  add_row "**OpenRouter**" "API Key" "Secret" "${OPENROUTER_API_KEY:0:12}•••" "$openrouter_status"
}

# Function to check optional/future credentials
validate_optional() {
  echo ""
  echo "=== Checking Optional Credentials ==="
  
  # GitHub Token (for API access, usually auto-provided in Actions)
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    log_info "GITHUB_TOKEN is available (auto-provided by Actions)"
    add_row "**GitHub**" "Token" "Auto-provided" "•••••••" "✅ Available"
  else
    log_warn "GITHUB_TOKEN not available (expected in Actions context)"
    add_row "**GitHub**" "Token" "Auto-provided" "-" "⚠️ Not Available"
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

# Add footer to summary with collapsible sections
cat >> "$SUMMARY_FILE" << 'EOF'

<details>
<summary><b>Legend</b></summary>

- ✅ **Valid**: Credential is properly configured and verified via API
- ⚠️ **Warning**: Credential is set but format may be invalid or rate limited
- ❌ **Invalid**: Credential is missing, expired, or invalid
- **Bold rows**: Overall service status

</details>

<details>
<summary><b>Validation Methods</b></summary>

- **Cloudflare**: Verified via wrangler CLI (supports Account and User tokens) and account access API
- **Google OAuth**: Verified via OAuth2 token endpoint with client_id and client_secret validation
- **OpenRouter**: Verified via direct API call to models endpoint

</details>

<details>
<summary><b>Actions Required</b></summary>

If any credentials show as invalid:

1. **Cloudflare**: Regenerate API token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
   - **Use Account API Token** (not User API Token)
   - Required permissions: Account Settings:Read, Workers Scripts:Edit, D1:Edit, Pages:Edit, R2:Edit, KV:Edit
   - Required zone permissions: Workers Routes:Edit
2. **Google OAuth**: Update credentials at [console.cloud.google.com](https://console.cloud.google.com/apis/credentials)
3. **OpenRouter**: Regenerate API key at [openrouter.ai/keys](https://openrouter.ai/keys)
4. **Secrets**: Update in repo settings at Settings → Secrets and variables → Actions

#### Testing Credentials Locally

To test credentials locally:

```bash
bash scripts/validate-credentials.sh
```

</details>
EOF

# Print summary
echo ""
echo "========================================"
if [ $OVERALL_RESULT -eq 0 ]; then
  log_info "All credentials validated successfully!"
  echo "✅ PASS" > "$RESULT_FILE"
else
  log_error "Credential validation failed. Check the summary for details."
  echo "❌ FAIL" > "$RESULT_FILE"
fi
echo "========================================"

# Save result code
echo "$OVERALL_RESULT" > "$RESULT_FILE"

exit $OVERALL_RESULT
