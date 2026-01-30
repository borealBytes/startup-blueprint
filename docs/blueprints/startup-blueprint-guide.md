# Startup Blueprint Template Guide

## Overview

Startup Blueprint is a production-ready template demonstrating full-stack deployment on Cloudflare infrastructure. It showcases:

- **Cloudflare Pages** for static hosting
- **Cloudflare Workers** for serverless API functions
- **D1 Database** for SQLite storage
- **R2 Storage** for object/file storage
- **KV Namespace** for session management
- **Google OAuth** for authentication

## Quick Start (5 minutes)

### Prerequisites

1. Cloudflare account (free tier is fine)
2. Google OAuth credentials (Client ID, Client Secret, Redirect URI)
3. Node.js 18+ and pnpm 8+
4. wrangler CLI installed globally

```bash
npm install -g wrangler
```

### One-Command Setup

From the repo root:

```bash
cd apps/startup-blueprint
bash scripts/setup-all.sh
```

This will:

1. Provision D1, R2, and KV resources (if they don't exist)
2. Deploy Cloudflare Pages and Workers
3. Seed demo data
4. Print the preview URL (based on branch name)

## Branch-based Preview URLs

Preview URLs follow this pattern:

```text
{branch}.startup-blueprint.SuperiorByteWorks.com
```

Examples:

- `main.startup-blueprint.SuperiorByteWorks.com`
- `feat-startup-blueprint-monorepo-structure.startup-blueprint.SuperiorByteWorks.com`

## Infrastructure Components

### D1 Database

- Name: `startup_blueprint_db`
- Tables: `users`, `activity`, `contacts`
- Schema defined in `apps/startup-blueprint/data/schema.sql`

### R2 Storage

- Bucket: `startup-blueprint-assets`
- Used for user file uploads from the dashboard

### KV Namespace

- Name: `startup-blueprint-sessions`
- Stores session tokens mapping to user IDs

## Authentication Flow

1. User clicks "Sign in with Google" on `/login`
2. `auth-worker.ts` redirects to Google OAuth
3. Google redirects back to `/auth/callback`
4. Worker exchanges code for tokens and fetches user profile
5. User saved/updated in D1 `users` table
6. Session token stored in KV under `session:{token}`
7. Session cookie set and user redirected to `/dashboard`

## API Overview

All API routes are handled by `api-worker.ts`:

- `POST /api/contact` - Store email capture submissions
- `GET /api/user` - Return current user profile
- `GET /api/activity` - Return recent user activity
- `POST /api/upload` - Return upload URL for R2
- `GET /api/files` - List files in R2 for current user
- `POST /api/logout` - Clear session

## Local Development

```bash
pnpm install
pnpm dev
```

This starts `wrangler pages dev` for the Pages content at `http://localhost:8788`.

## Production Notes

- Use a dedicated Cloudflare account or project for this template in production
- Lock down Google OAuth credentials to your domain
- Configure proper CORS rules and security headers for Workers
- Consider adding error monitoring and logging via Cloudflare observability tools

## Next Steps

- Customize copy and branding in `src/pages/*.html`
- Extend database schema for your specific use case
- Add domain-specific Workers (billing, notifications, etc.)
- Integrate with your CI/CD pipeline using GitHub Actions
