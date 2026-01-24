# Startup Blueprint

A comprehensive, production-ready template for building on Cloudflare infrastructure.

## Features

- ✅ **Cloudflare Pages** - Static site hosting
- ✅ **Cloudflare Workers** - Serverless API functions
- ✅ **D1 Database** - SQLite storage on the edge
- ✅ **R2 Storage** - Object/file storage
- ✅ **KV Namespace** - Session management
- ✅ **Google OAuth** - Authentication
- ✅ **Tailwind CSS** - Responsive UI

## Directory Structure

```
apps/startup-blueprint/
├── src/
│   ├── pages/           # Cloudflare Pages static files
│   │   ├── index.html   # Landing page
│   │   ├── login.html   # OAuth login
│   │   └── dashboard.html # User dashboard
│   └── workers/         # Cloudflare Workers
│       ├── auth-worker.ts  # OAuth flow
│       └── api-worker.ts   # API endpoints
├── data/
│   └── schema.sql       # D1 database schema
├── scripts/
│   ├── setup-all.sh     # Complete setup
│   └── seed-demo-data.sh # Demo data
├── package.json
├── wrangler.toml        # Cloudflare configuration
└── tsconfig.json
```

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 8+
- wrangler CLI: `npm install -g wrangler`
- Cloudflare account
- Google OAuth credentials

### Local Development

```bash
# Install dependencies
cd apps/startup-blueprint
pnpm install

# Start local dev server
pnpm dev

# Open http://localhost:8788
```

### Deploy to Cloudflare

```bash
# Run complete setup (one command)
bash scripts/setup-all.sh

# Or manually:
bash scripts/setup-all.sh main
```

This will:

1. Create D1 database with schema
2. Create R2 storage bucket
3. Create KV namespace for sessions
4. Deploy Pages and Workers
5. Seed demo data

## Configuration

### Environment Variables

Create `.env.local` with:

```
CLOUDFLARE_API_TOKEN=your-token
CLOUDFLARE_ACCOUNT_ID=your-account-id
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain/auth/callback
```

### wrangler.toml

Update with your Cloudflare settings (done by setup script).

## Pages & Routes

- `/` - Landing page with email capture
- `/login` - Google OAuth login
- `/dashboard` - User dashboard (protected)

## API Endpoints

- `POST /api/contact` - Email submission
- `GET /api/user` - User profile (requires auth)
- `GET /api/activity` - User activity log (requires auth)
- `POST /api/upload` - Get presigned upload URL (requires auth)
- `GET /api/files` - List user files (requires auth)
- `POST /api/logout` - Logout (requires auth)

## Database Schema

- `users` - Google OAuth user profiles
- `activity` - User action log
- `contacts` - Email submissions

## Storage

- **R2 Bucket**: `startup-blueprint-assets`
  - User uploads stored at: `{user-id}/{timestamp}-{filename}`
- **KV Namespace**: `startup-blueprint-sessions`
  - Session tokens: `session:{token} -> {user-id}`

## Cleanup

```bash
bash ../../scripts/cloudflare/teardown-helper.sh startup-blueprint main
```

This will:

- Delete Pages deployment
- Delete D1 database
- Delete R2 bucket
- Delete KV namespace

## Testing

```bash
pnpm test         # Unit tests
pnpm test:e2e     # E2E tests
pnpm lint         # Linting
```

## License

MIT
