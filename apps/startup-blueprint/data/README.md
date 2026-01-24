# Demo Data & Fixtures

This directory contains database schemas and demo data for the Startup Blueprint template.

## Files

- `schema.sql` - D1 database schema
- `demo-assets/` - Sample files for R2 upload testing

## Usage

Schema is automatically applied during setup:

```bash
bash scripts/setup-all.sh
```

To manually apply schema:

```bash
wrangler d1 execute startup_blueprint_db --file=data/schema.sql
```

## Database Structure

### users

Stores authenticated user information from Google OAuth.

### activity

Tracks user actions and events for the dashboard.

### contacts

Stores email submissions from the coming soon page.
