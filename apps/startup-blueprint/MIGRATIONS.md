# Database Migrations Guide

## Overview

This guide explains the database schema, migration procedures, and best practices for managing database changes in the Startup Blueprint application.

## Database Technology

**Production:** Cloudflare D1 (SQLite-based)
**Local Development:** SQLite (compatible with D1)

Cloudflare D1 is a SQLite-based serverless database that runs on Cloudflare's global network. It provides:

- Automatic replication across Cloudflare's edge locations
- Serverless execution (no servers to manage)
- SQLite compatibility (use standard SQLite syntax)
- Low latency reads from edge locations

## Current Schema

### Tasks Table

```sql
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed')),
  priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries by status
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Index for faster queries by created_at
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
```

**Columns:**

- `id` - Auto-incrementing primary key
- `title` - Task title (required, max 255 chars recommended)
- `description` - Task description (optional, TEXT type for longer content)
- `status` - Task status: pending, in_progress, completed (default: pending)
- `priority` - Task priority: low, medium, high (default: medium)
- `created_at` - Timestamp when task was created
- `updated_at` - Timestamp when task was last modified

**Constraints:**

- `status` must be one of: pending, in_progress, completed
- `priority` must be one of: low, medium, high

**Indexes:**

- `idx_tasks_status` - Optimizes queries filtering by status
- `idx_tasks_created_at` - Optimizes queries ordering by creation date

## Migration Workflow

### 1. Local Development Migrations

When developing locally, apply migrations to your local SQLite database:

```bash
# Create a new migration file
cd apps/startup-blueprint
mkdir -p migrations
touch migrations/$(date +%Y%m%d_%H%M%S)_migration_name.sql
```

**Migration file naming convention:**

- `YYYYMMDD_HHMMSS_description.sql`
- Example: `20260123_180000_add_tasks_table.sql`

**Example migration file:**

```sql
-- Migration: Add tasks table
-- Date: 2026-01-23
-- Author: Dev Team

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Always use IF NOT EXISTS to make migrations idempotent
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

### 2. Apply Migration Locally

```bash
# Using wrangler for local D1
wrangler d1 execute startup-blueprint-db --local --file=migrations/20260123_180000_add_tasks_table.sql

# Or using sqlite3 directly
sqlite3 .wrangler/state/v3/d1/miniflare-D1DatabaseObject/startup-blueprint-db.sqlite < migrations/20260123_180000_add_tasks_table.sql
```

### 3. Test Migration

```bash
# Start local dev server
pnpm run dev

# Test API endpoints
curl http://localhost:8787/api/tasks

# Run integration tests
pnpm test
```

### 4. Deploy to Production

```bash
# Apply migration to production D1 database
wrangler d1 execute startup-blueprint-db --remote --file=migrations/20260123_180000_add_tasks_table.sql

# Deploy application
pnpm run deploy
```

## Best Practices

### ✅ DO

1. **Make migrations idempotent** - Use `IF NOT EXISTS`, `IF EXISTS` clauses

   ```sql
   CREATE TABLE IF NOT EXISTS users (...);
   ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority TEXT;
   ```

2. **Test migrations locally first** - Always test on local database before production
3. **Create indexes for frequently queried columns**

   ```sql
   CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
   ```

4. **Use CHECK constraints for enums** - Enforce valid values at database level

   ```sql
   status TEXT CHECK(status IN ('pending', 'in_progress', 'completed'))
   ```

5. **Include migration metadata** - Add comments with date, author, description
6. **Backup before major changes** - Export D1 database before schema changes
7. **Version control migrations** - Commit migration files to git

### ❌ DON'T

1. **Don't modify existing migrations** - Create new migration files for changes
2. **Don't use features not supported by SQLite** - D1 is SQLite-based
3. **Don't forget to update both local and production** - Keep environments in sync
4. **Don't skip testing** - Broken migrations can corrupt data
5. **Don't use reserved keywords** - Avoid SQL keywords as column names

## Common Migration Patterns

### Adding a Column

```sql
-- Add new column with default value
ALTER TABLE tasks ADD COLUMN assigned_to INTEGER;

-- Add column with constraint
ALTER TABLE tasks ADD COLUMN due_date DATETIME CHECK(due_date > created_at);
```

### Dropping a Column

**⚠️ SQLite Limitation:** SQLite doesn't support `DROP COLUMN` directly.

**Workaround:**

```sql
-- 1. Create new table without the column
CREATE TABLE tasks_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  -- priority column removed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Copy data
INSERT INTO tasks_new SELECT id, title, description, status, created_at FROM tasks;

-- 3. Drop old table
DROP TABLE tasks;

-- 4. Rename new table
ALTER TABLE tasks_new RENAME TO tasks;

-- 5. Recreate indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

### Adding an Index

```sql
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
```

### Modifying Data

```sql
-- Update existing records
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL;

-- Migrate data format
UPDATE tasks SET status = 'in_progress' WHERE status = 'active';
```

## Cloudflare D1 Specific Commands

### List Databases

```bash
wrangler d1 list
```

### Execute SQL Command

```bash
# Local
wrangler d1 execute startup-blueprint-db --local --command="SELECT * FROM tasks LIMIT 5"

# Production
wrangler d1 execute startup-blueprint-db --remote --command="SELECT * FROM tasks LIMIT 5"
```

### Export Database

```bash
# Export production database to SQL file
wrangler d1 export startup-blueprint-db --remote --output=backup-$(date +%Y%m%d).sql
```

### Create Backup

```bash
# Before major migration, create backup
wrangler d1 export startup-blueprint-db --remote --output=backup-before-migration.sql
```

## Rollback Procedures

### If Migration Fails

1. **Identify the issue**

   ```bash
   # Check D1 logs
   wrangler tail
   ```

2. **Export current state (if possible)**

   ```bash
   wrangler d1 export startup-blueprint-db --remote --output=failed-migration-backup.sql
   ```

3. **Restore from backup**

   ```bash
   # Drop affected tables
   wrangler d1 execute startup-blueprint-db --remote --command="DROP TABLE IF EXISTS tasks"

   # Restore from backup
   wrangler d1 execute startup-blueprint-db --remote --file=backup-before-migration.sql
   ```

4. **Fix migration and retry**

### Creating Rollback Migrations

Always create a rollback migration file alongside your forward migration:

**Forward: `20260123_180000_add_priority_column.sql`**

```sql
ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium';
```

**Rollback: `20260123_180000_rollback_add_priority_column.sql`**

```sql
-- Since SQLite doesn't support DROP COLUMN, we recreate the table
CREATE TABLE tasks_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tasks_new SELECT id, title, description, status, created_at FROM tasks;
DROP TABLE tasks;
ALTER TABLE tasks_new RENAME TO tasks;
```

## SQLite vs PostgreSQL Differences

Since D1 uses SQLite, be aware of these differences from PostgreSQL:

### Feature Comparison

| Feature             | SQLite/D1        | PostgreSQL      |
| ------------------- | ---------------- | --------------- |
| `DROP COLUMN`       | ❌ Not supported | ✅ Supported    |
| `AUTOINCREMENT`     | ✅ Supported     | ❌ Use SERIAL   |
| `CHECK` constraints | ✅ Supported     | ✅ Supported    |
| JSON functions      | ⚠️ Limited       | ✅ Full support |
| Full-text search    | ⚠️ Basic         | ✅ Advanced     |
| `SERIAL` type       | ❌ Not supported | ✅ Supported    |

### SQLFluff Configuration

Our CI uses SQLFluff with `sqlite` dialect to lint SQL files:

```yaml
# .github/workflows/format-lint-reusable.yml
sqlfluff fix --dialect sqlite --force .
```

**Why SQLite dialect:**

- D1 is SQLite-based
- Ensures SQL files are compatible with production database
- Catches SQLite-specific syntax issues during CI

## Monitoring & Troubleshooting

### Check Database Size

```bash
wrangler d1 info startup-blueprint-db --remote
```

### Query Slow Queries

```sql
-- Enable query logging
PRAGMA query_only = ON;

-- Analyze query performance
EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE status = 'pending';
```

### Common Issues

**Issue:** Migration fails with "table already exists"
**Solution:** Use `CREATE TABLE IF NOT EXISTS`

**Issue:** Data lost after migration
**Solution:** Always backup before migrations, test locally first

**Issue:** Slow queries after adding data
**Solution:** Add appropriate indexes on frequently queried columns

## Resources

- [Cloudflare D1 Documentation](https://developers.cloudflare.com/d1/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQLite vs PostgreSQL](https://www.sqlite.org/different.html)
- [Wrangler CLI Reference](https://developers.cloudflare.com/workers/wrangler/)

## Migration Checklist

Before deploying a migration:

- [ ] Migration file created with timestamp prefix
- [ ] Migration is idempotent (uses `IF EXISTS` / `IF NOT EXISTS`)
- [ ] Migration tested locally
- [ ] Integration tests pass
- [ ] Rollback migration created
- [ ] Database backup taken (production only)
- [ ] Migration applied to local D1 database
- [ ] Migration applied to production D1 database
- [ ] Application deployed
- [ ] Smoke tests performed on production

## Support

For migration issues:

- Review Cloudflare D1 logs: `wrangler tail`
- Check SQLite compatibility: [SQLite Features](https://www.sqlite.org/features.html)
- Open an issue: [startup-blueprint/issues](https://github.com/borealBytes/startup-blueprint/issues)
