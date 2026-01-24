# ADR-003: Idempotent Scripts and Operational Reliability

**Status**: Accepted  
**Date**: 2026-01-12  
**Decision Maker**: BUSINESS_NAME Development Team

---

## Problem Statement

BUSINESS_NAME operates across multiple workspaces and environments (development, staging, production). Operational tasks require:

1. **Reliability** - Scripts must work repeatedly without side effects
2. **Safety** - Operations should never corrupt data or create duplicate entries
3. **Auditability** - Changes must be trackable and reversible
4. **Clarity** - Teams should understand exactly what a script does before running it
5. **Consistency** - Same script behavior across all environments

**Challenge**: Traditional scripts can:

- ❌ Fail silently if run twice (data corruption)
- ❌ Create duplicate database records
- ❌ Partially complete without rollback
- ❌ Be unclear about side effects
- ❌ Work in dev but fail in production

---

## Constraints

1. **BUSINESS_NAME Architecture**
   - Multiple workspaces and business lines
   - Different database environments (dev, staging, prod)
   - CI/CD pipeline runs scripts automatically
   - Scripts must be safe to re-run on failure

2. **Team Capabilities**
   - Developers comfortable with shell scripting
   - Some operations run via GitHub Actions
   - Mix of Linux and development machine execution
   - Scripts should be debuggable and loggable

3. **Operational Requirements**
   - Deployments happen frequently
   - Failed deployments must be recoverable
   - Data integrity is critical
   - Audit trail needed for compliance

---

## Decision

**All BUSINESS_NAME operational scripts must be idempotent**:

### **1. Idempotent Principle**

Each script must satisfy:

```bash
# Running once = same result as running multiple times
script.sh          # First run: creates resources X, Y, Z
script.sh          # Second run: verifies X, Y, Z exist, makes no changes
script.sh          # Third run: same as second (no side effects)
```

### **2. Implementation Patterns**

**Pattern A: Check-before-create**

```bash
#!/bin/bash
set -e  # Exit on error

# Check if resource exists
if ! resource_exists "my-resource"; then
  echo "Creating resource..."
  create_resource "my-resource"
else
  echo "Resource already exists, skipping creation"
fi

echo "✓ Script completed successfully"
```

**Pattern B: Versioned migrations**

```bash
#!/bin/bash
set -e

# Track applied migrations
MIGRATION_VERSION="001_create_users_table"
MIGRATION_LOG=".migration_log"

if grep -q "$MIGRATION_VERSION" "$MIGRATION_LOG"; then
  echo "Migration $MIGRATION_VERSION already applied"
else
  echo "Running migration $MIGRATION_VERSION..."
  # SQL: CREATE TABLE IF NOT EXISTS users
  echo "$MIGRATION_VERSION" >> "$MIGRATION_LOG"
fi
```

**Pattern C: Idempotent database updates**

```bash
#!/bin/bash
set -e

# For database operations: use UPSERT or conditional logic
sqlite3 production.db << EOF
-- Only update if record exists and is different
UPDATE products
SET price = 49.99
WHERE sku = 'ITEM-001' AND price != 49.99;

-- Only insert if doesn't exist
INSERT OR IGNORE INTO products (sku, name, price)
VALUES ('ITEM-001', 'Sample Item', 49.99);
EOF
```

### **3. Required Elements**

Every BUSINESS_NAME operational script must have:

**Header**:

```bash
#!/bin/bash
# Purpose: [What this script does]
# Idempotent: YES (can be run multiple times safely)
# Environment: [dev|staging|production|all]
# Author: [Name or team]
# Last Updated: YYYY-MM-DD

set -e  # Exit on error
set -u  # Error on undefined variable
set -o pipefail  # Catch errors in pipes
```

**Logging**:

```bash
LOG_FILE="/tmp/script-$(date +%Y%m%d-%H%M%S).log"
echo "Starting script at $(date)" | tee "$LOG_FILE"

# Every action logged
echo "[INFO] Creating database..." | tee -a "$LOG_FILE"
# ... do thing ...
echo "[SUCCESS] Database created" | tee -a "$LOG_FILE"
```

**Error Handling**:

```bash
# Define cleanup function
cleanup() {
  echo "[ERROR] Script failed at line $1"
  # Rollback any partial state if needed
  exit 1
}

# Trap errors
trap 'cleanup $LINENO' ERR
```

**Exit Status**:

```bash
# Always exit with clear status
if [[ $SUCCESS == true ]]; then
  echo "✓ Script completed successfully"
  exit 0
else
  echo "✗ Script failed"
  exit 1
fi
```

### **4. Testing Before Production**

All scripts must follow:

1. **Dry-run mode**: `script.sh --dry-run` (shows what would happen)
2. **Dev testing**: Run 3x on dev and verify same result
3. **Staging test**: Run on staging before production
4. **Documentation**: Include expected output for verification

---

## Consequences

### **Positive**

✅ **Safe re-execution**

- Failed deployments can be re-run without corruption
- No duplicate database entries
- Partial failures can be recovered from

✅ **CI/CD friendly**

- GitHub Actions can retry automatically
- No manual intervention needed for transient failures
- Clear success/failure signals

✅ **Auditable**

- Logs show exactly what happened
- Timestamps for every operation
- Easy to track changes across environments

✅ **Team confidence**

- Developers understand what scripts do
- Safe to run during troubleshooting
- New team members can run scripts without fear

✅ **Data integrity**

- No corruption from duplicate operations
- Compliance-ready audit trail

### **Negative / Trade-offs**

⚠️ **Slightly more complex logic**

- Need to check before creating
- Need to handle "already exists" case
- Adds a few lines to every script
- Mitigation: Template snippets provided

⚠️ **Performance trade-off**

- Checking existence adds slight overhead
- Multiple runs slower than one-shot scripts
- Mitigation: Negligible for typical BUSINESS_NAME workflows

⚠️ **Requires discipline**

- Developers must follow patterns
- Violations could break consistency
- Mitigation: PR reviews check idempotency

---

## Why This Over Alternatives?

### **Alternative 1: One-shot scripts**

**Why rejected**:

- Failed deployments require manual cleanup
- Duplicate data if re-run
- Risky in production
- No recovery path

### **Alternative 2: Rollback scripts**

**Why rejected**:

- Doubles maintenance burden (create + undo)
- Rollback scripts can fail too
- Requires manual orchestration
- Still doesn't solve re-execution safety

### **Alternative 3: Immutable infrastructure**

**Why rejected**:

- Overkill for BUSINESS_NAME scale
- Complex to implement
- High operational overhead
- Not suitable for frequent data updates

**Chosen approach** wins because:

- ✅ Simple to understand
- ✅ Low overhead
- ✅ Works with existing CI/CD
- ✅ Safe for data operations
- ✅ Team can implement immediately

---

## Implementation

### **Phase 1: Template Creation**

- ✅ Idempotent script template created
- ✅ Pattern examples documented
- ✅ Logging best practices defined
- ✅ Error handling template provided

### **Phase 2: Existing Scripts Migration** (In Progress)

- [ ] Audit existing scripts in BUSINESS_NAME
- [ ] Identify non-idempotent scripts
- [ ] Refactor to idempotent patterns
- [ ] Add logging and error handling

### **Phase 3: CI/CD Integration** (Pending)

- [ ] Add dry-run stage to GitHub Actions
- [ ] Enable auto-retry for transient failures
- [ ] Capture logs for audit trail
- [ ] Notify team on failure

### **Phase 4: Documentation** (Pending)

- [ ] Script library with examples
- [ ] Runbook for troubleshooting
- [ ] Training for new team members

---

## Metrics for Success

1. **Reliability**
   - 100% of operational scripts idempotent
   - Zero data corruption from duplicate runs
   - Failed deployments recoverable via re-run

2. **Auditability**
   - Every script run logged with timestamp
   - All changes traceable
   - Compliance audit ready

3. **Team adoption**
   - All new scripts follow pattern
   - Existing scripts migrated
   - Code reviews verify idempotency

4. **Operational improvements**
   - Reduced manual intervention
   - Faster deployment recovery
   - Increased team confidence

---

## Related ADRs

- **ADR-001**: Using Perplexity Spaces for Agentic Development
- **ADR-002**: Monorepo structure (BUSINESS_NAME-specific)
- **ADR-004**: Error recovery procedures (handling failures)

---

## Open Questions

1. **What about infrastructure provisioning?**
   - Answer: Terraform/CloudFormation handles infrastructure idempotently. Scripts focus on data/application level.

2. **How to handle scripts with external API calls?**
   - Answer: Idempotency achieved via state tracking (recorded what was done, don't repeat).

3. **Should dry-run be mandatory?**
   - Answer: Yes for production scripts, recommended for all.

4. **How to test idempotency?**
   - Answer: Run 3x in sequence on test environment, verify same outcome each time.

---

## Approval

- **Proposed by**: BUSINESS_NAME Development Team
- **Date**: 2026-01-12
- **Status**: Ready for implementation
- **Next step**: Phase 1 template creation and Phase 2 script migration

---

## References

- [Idempotence in System Administration](https://en.wikipedia.org/wiki/Idempotence#In_computer_science)
- `autonomy_boundaries.md` — Agent operational boundaries
- `operational_readiness.md` — System constraints
- GitHub Actions documentation on retries and error handling
