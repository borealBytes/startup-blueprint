# Scripts

Utility scripts for startup-blueprint repository.

## Credential Validation

### `validate-credentials.sh`

Validates all environment variables and secrets required for the startup-blueprint project.

**Runs automatically** on every PR commit via GitHub Actions.

#### What It Checks

| Service          | Credentials   | Type          | Validation                                                         |
| ---------------- | ------------- | ------------- | ------------------------------------------------------------------ |
| **Cloudflare**   | API Token     | Secret        | Tests with `wrangler whoami`                                       |
|                  | Account ID    | Secret        | Checks if set                                                      |
| **Google OAuth** | Client ID     | Secret        | Format validation (.apps.googleusercontent.com)                    |
|                  | Client Secret | Secret        | Format validation (GOCSPX-)                                        |
|                  | Redirect URI  | Variable      | Format validation (https://\*.SuperiorByteWorks.com/auth/callback) |
| **GitHub**       | Token         | Auto-provided | Checks availability in Actions context                             |

#### Usage

**In GitHub Actions (Automatic)**:

```yaml
# Runs in CI on every PR
validate-credentials:
  name: Validate Credentials
  uses: ./.github/workflows/validate-credentials-reusable.yml
  secrets: inherit
```

**Local Testing**:

```bash
# Export credentials first
export CLOUDFLARE_API_TOKEN="your-token"
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-secret"
export GOOGLE_REDIRECT_URI="https://yourdomain.com/auth/callback"

# Run validation
bash scripts/validate-credentials.sh
```

#### Output

The script generates a formatted markdown table in GitHub Actions summary:

```markdown
| Service          | Credential    | Type     | Value        | Status          |
| ---------------- | ------------- | -------- | ------------ | --------------- |
| **Cloudflare**   | API Token     | Secret   | ••••••••     | ✅ Valid        |
|                  | Account ID    | Secret   | abc12345•••  | ✅ Set          |
|                  |               |          |              | **✅ Valid**    |
| **Google OAuth** | Client ID     | Secret   | 123456789••• | ✅ Valid Format |
|                  | Client Secret | Secret   | ••••••••     | ✅ Valid Format |
|                  | Redirect URI  | Variable | https://...  | ✅ Valid Format |
|                  |               |          |              | **✅ Valid**    |
```

#### Status Codes

- ✅ **Valid**: Credential is properly configured and validated
- ⚠️ **Warning**: Credential is set but format may be invalid
- ❌ **Invalid**: Credential is missing, expired, or invalid
- **Bold rows**: Overall service status (merged cells concept)

#### Exit Codes

- `0`: All credentials valid
- `1`: One or more credentials invalid or missing

#### Troubleshooting

**Cloudflare Token Invalid**:

1. Generate new token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Ensure permissions include:
   - Cloudflare Pages (Edit)
   - D1 (Edit)
   - Workers Scripts (Edit)
   - Workers R2 Storage (Edit)
   - Workers KV Storage (Edit)
3. Update in GitHub: Settings → Secrets → `CLOUDFLARE_API_TOKEN`

**Google OAuth Invalid**:

1. Verify credentials at [console.cloud.google.com](https://console.cloud.google.com/apis/credentials)
2. Check redirect URI matches exactly (including trailing paths)
3. Update in GitHub Secrets

**Script Fails in CI**:

1. Check Actions logs for specific error
2. Verify all secrets are set in repo settings
3. Ensure secrets aren't expired

#### Adding New Credentials

To add validation for new services:

1. **Add validation function** in `validate-credentials.sh`:

   ```bash
   validate_myservice() {
     if [ -z "${MY_API_KEY:-}" ]; then
       log_error "MY_API_KEY not set"
       add_row "**MyService**" "API Key" "Secret" "•••" "❌ Not Set"
       OVERALL_RESULT=1
       return
     fi

     # Test the credential
     if curl -s -H "Authorization: Bearer $MY_API_KEY" https://api.myservice.com/test | grep -q "success"; then
       add_row "**MyService**" "API Key" "Secret" "•••" "✅ Valid"
     else
       add_row "**MyService**" "API Key" "Secret" "•••" "❌ Invalid"
       OVERALL_RESULT=1
     fi
   }
   ```

2. **Call function** in main execution:

   ```bash
   validate_cloudflare
   validate_google
   validate_myservice  # Add here
   validate_optional
   ```

3. **Add to workflow** in `.github/workflows/validate-credentials-reusable.yml`:

   ```yaml
   env:
     MY_API_KEY: ${{ secrets.MY_API_KEY }}
   ```

4. **Document** in this README

#### Files

- **Script**: `scripts/validate-credentials.sh`
- **Workflow**: `.github/workflows/validate-credentials-reusable.yml`
- **CI Integration**: `.github/workflows/ci.yml` (Phase 2)

---

## Future Scripts

Additional scripts will be documented here as they're added:

- `setup-cloudflare.sh` - Initial Cloudflare infrastructure setup
- `deploy-preview.sh` - Deploy preview environments
- `cleanup-old-deployments.sh` - Remove stale preview deployments
