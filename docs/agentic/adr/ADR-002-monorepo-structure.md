# ADR-002: Monorepo Structure and Organization

**Status**: Accepted  
**Date**: 2026-01-12  
**Decision Maker**: BUSINESS_NAME Development Team

---

## Problem Statement

BUSINESS_NAME is expanding from a single product (primary app) to multiple products and services:

- Primary app (current)
- Marketing website (future)
- Customer portal (future)
- Internal tools (future)
- Shared authentication and business logic

Without a monorepo structure, BUSINESS_NAME would face:

**Challenge 1: Code Duplication**

- ❌ Authentication logic replicated across apps
- ❌ Database schemas duplicated
- ❌ UI components redefined in each app
- ❌ Utility functions copied instead of shared

**Challenge 2: Deployment Complexity**

- ❌ Changes to shared code require manual coordination
- ❌ Unclear which apps need rebuilding
- ❌ Difficult to test changes across multiple products
- ❌ Risk of inconsistent versions

**Challenge 3: Scaling Bottlenecks**

- ❌ Can't quickly add new products
- ❌ Repository structure prevents independent deployment
- ❌ Difficult to organize team ownership
- ❌ Hard to extract products to separate repos later

**Challenge 4: Cloudflare Workers Complexity**

- ❌ Multiple `wrangler.toml` files scattered
- ❌ Unclear which deployables are where
- ❌ Configuration management becomes chaotic
- ❌ Each worker deployment impacts root

---

## Constraints

1. **BUSINESS_NAME Technology Stack**
   - Cloudflare Workers (serverless backends)
   - Cloudflare Pages (static/frontend hosting)
   - Cloudflare KV, R2, D1 (data storage)
   - TypeScript (type safety)
   - pnpm (efficient package manager)

2. **Team Structure**
   - Small team (1-2 developers initially)
   - Need to scale to multiple teams (future)
   - Clear product ownership required
   - Autonomous deployment capability needed

3. **Operational Requirements**
   - Multiple independent products
   - Shared authentication
   - Shared database schemas
   - Shared UI components (future)
   - Version independence (apps deploy separately)

4. **Business Constraints**
   - Primary app must deploy independently
   - Marketing website on separate timeline
   - Customer portal runs on different cadence
   - Cannot block one product for another

---

## Decision

**BUSINESS_NAME will adopt a product-based monorepo structure using:**

1. **Product-Based Organization** (not domain-based)
   - `apps/primary-app/` ← Product name
   - `apps/marketing-site/` ← Not `apps/business_name.com/`
   - `apps/customer-portal/` ← Resilient to domain changes

2. **Shared Code via Packages**
   - `packages/auth/` ← Authentication logic
   - `packages/database/` ← Database types & schemas
   - `packages/ui/` ← Shared components
   - `packages/utils/` ← Utility functions

3. **Build Orchestration with Turborepo**
   - Smart caching (only rebuild what changed)
   - Parallel execution (build multiple apps simultaneously)
   - Dependency graph awareness
   - Monorepo-wide commands from root

4. **Workspace Management with pnpm**
   - Efficient disk usage
   - Workspace hoisting
   - Automatic linking of local packages
   - Shared `node_modules` structure

5. **Independent Deployments**
   - Each app has own `wrangler.toml`
   - Own Cloudflare KV/R2/D1 resources
   - Own deployment pipeline
   - Can be deployed to own subdomain or domain
   - Can later be extracted to separate repository

---

## Directory Structure

```
BUSINESS_NAME/
├── apps/                                    # 🚀 Deployable applications
│   ├── primary-app/                         # Primary product (current)
│   │   ├── src/                            # Worker source code
│   │   │   ├── index.ts                    # Entry point
│   │   │   ├── routes/                     # API endpoints
│   │   │   ├── middleware/                 # Auth, CORS, etc.
│   │   │   ├── services/                   # Business logic
│   │   │   └── types/                      # TypeScript types
│   │   ├── wrangler.toml                   # Cloudflare config
│   │   ├── package.json                    # Dependencies
│   │   ├── tsconfig.json                   # TypeScript config
│   │   └── README.md                       # App documentation
│   │
│   ├── marketing-site/                     # Marketing site (future)
│   │   ├── src/
│   │   ├── wrangler.toml
│   │   └── package.json
│   │
│   └── customer-portal/                    # Customer portal (future)
│       ├── src/
│       ├── wrangler.toml
│       └── package.json
│
├── packages/                                # 📦 Shared code libraries
│   ├── auth/                               # Authentication logic
│   │   ├── src/
│   │   │   ├── index.ts                    # Public exports
│   │   │   ├── validate.ts                 # JWT validation
│   │   │   ├── session.ts                  # Session management
│   │   │   └── types.ts                    # Shared types
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── database/                           # Database schemas & types
│   │   ├── src/
│   │   │   ├── index.ts                    # Schema definitions
│   │   │   ├── migrations/                 # Database migrations
│   │   │   └── types.ts                    # TypeScript types
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── ui/                                 # Shared UI components (future)
│   │   ├── src/
│   │   └── package.json
│   │
│   ├── config/                             # Shared configuration
│   │   ├── src/
│   │   └── package.json
│   │
│   └── utils/                              # Utility functions
│       ├── src/
│       └── package.json
│
├── docs/                                   # 📝 Documentation
│   ├── SPEC_MONOREPO.md                    # Technical specification
│   ├── products/
│   │   └── primary-app/
│   │       ├── CLOUDFLARE_SETUP.md         # Infrastructure setup
│   │       ├── GMAIL_SMTP_SETUP.md         # Email configuration
│   │       ├── PRD.md                      # Product requirements
│   │       ├── TDD.md                      # Technical design
│   │       └── PROJECT_STATUS.md           # Implementation status
│   │
│   └── company/
│       ├── README.md
│       └── policies/
│
├── .github/                                # ⚙️ GitHub configuration
│   ├── workflows/
│   │   ├── deploy.yml                      # CI/CD deployment
│   │   ├── test.yml                        # Testing workflow
│   │   └── lint.yml                        # Code quality
│   │
│   └── ISSUE_TEMPLATE/
│
├── scripts/                                # 🔧 Automation scripts
│   ├── setup.sh                            # Initial setup
│   ├── deploy.sh                           # Manual deployment
│   └── migrate.sh                          # Database migrations
│
├── docs/agentic/                           # 🤖 AI agent configuration
│   ├── adr/                                # Architecture decision records
│   │   ├── ADR-001-perplexity-spaces.md
│   │   ├── ADR-002-monorepo-structure.md
│   │   ├── ADR-003-idempotent-scripts.md
│   │   └── ADR-004-error-recovery.md
│   │
│   └── instructions.md
│
├── .env.example                            # Environment variables template
├── turbo.json                              # Turborepo orchestration
├── pnpm-workspace.yaml                     # Workspace definition
├── package.json                            # Root dependencies & scripts
├── MONOREPO_STRUCTURE.md                   # User-friendly monorepo guide
├── .gitignore                              # Git ignore rules
├── CONTRIBUTING.md                         # Contribution guidelines
└── README.md                               # Project overview
```

---

## Design Principles

### **1. Product-Based Organization (Not Domain-Based)**

**Why product names?**

✅ **Domains change, products don't**

- If `api.business_name.com` moves to `api.example.com`, product folder stays `apps/primary-app/`
- Refactoring domains doesn't require restructuring

✅ **Ownership clarity**

- Teams own products, not domains
- Easy to say "Primary App team owns `apps/primary-app/`"
- Domains can be reassigned without confusion

✅ **Extraction friendly**

- If Primary App becomes separate company later, folder is already isolated
- Can move `apps/primary-app/` to `BUSINESS_NAME/primary-app` repo
- No refactoring needed

### **2. Independent Deployments**

**Each app deploys autonomously:**

✅ **Own Cloudflare resources**

- `primary-app` has own KV namespace
- `marketing-site` has own R2 bucket
- `customer-portal` has own D1 database
- No resource conflicts or contention

✅ **Own deployment pipeline**

- Changes to `apps/primary-app/` don't affect other apps
- Primary App can deploy multiple times per day
- Marketing site on separate release schedule
- Zero coupling between deployments

✅ **Version independence**

- Primary App can use Framework v2, Marketing site uses v3
- Each app pinned to dependency versions
- Upgrades don't block other products

### **3. Shared Code via Packages**

**DRY principle without duplication:**

✅ **Single source of truth**

- Authentication logic in `packages/auth/`
- All apps import same implementation
- Bug fix in auth library fixes all apps

✅ **Type-safe sharing**

- TypeScript types in `packages/database/`
- Apps use same types for database records
- Compile-time errors prevent mismatches

✅ **Workspace dependencies**

- Import like: `import { validateToken } from '@business_name/auth'`
- pnpm automatically links local package
- No build step needed during development
- Changes to package immediately visible

### **4. Scalability**

**Easy to grow:**

✅ **Add apps incrementally**

```bash
mkdir -p apps/new-product/src
cp -r apps/primary-app/{wrangler.toml,package.json,tsconfig.json} apps/new-product/
# Edit configs for new product
```

✅ **Extract to separate repos later**

```bash
git subtree split --prefix apps/primary-app -b primary-app-repo
# Push to new repository
```

✅ **Add teams with clear ownership**

- Platform team owns `packages/`
- Primary App team owns `apps/primary-app/`
- Marketing site team owns `apps/marketing-site/`
- Each team autonomously ships

---

## Implementation

### **Root-Level Scripts**

**`package.json` at monorepo root:**

```json
{
  "name": "@business_name/monorepo",
  "private": true,
  "description": "BUSINESS_NAME business monorepo",
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "deploy:prod": "turbo run deploy:prod",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "test": "turbo run test",
    "format": "prettier --write ."
  },
  "workspaces": ["apps/*", "packages/*"],
  "devDependencies": {
    "turbo": "latest",
    "prettier": "latest",
    "typescript": "latest"
  }
}
```

### **App Structure**

**Each app in `apps/` has:**

```json
{
  "name": "primary-app",
  "version": "0.1.0",
  "type": "module",
  "dependencies": {
    "@business_name/auth": "workspace:*",
    "@business_name/database": "workspace:*",
    "hono": "^4.0.0"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "latest",
    "wrangler": "latest",
    "typescript": "latest"
  },
  "scripts": {
    "dev": "wrangler dev",
    "deploy:prod": "wrangler deploy --env production",
    "build": "tsc",
    "typecheck": "tsc --noEmit"
  }
}
```

**`wrangler.toml` in each app:**

```toml
name = "primary-app"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[env.development]
route = "api.dev.business_name.com/*"
routes = []

kv_namespaces = [
  { binding = "KV", id = "<kv-id>", preview_id = "<preview-id>" }
]

[env.production]
route = "api.business_name.com/*"

kv_namespaces = [
  { binding = "KV", id = "<kv-id-prod>", preview_id = "<preview-id-prod>" }
]
```

### **Package Structure**

**Each package in `packages/` has:**

```json
{
  "name": "@business_name/auth",
  "version": "0.1.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts"
  },
  "dependencies": {
    "jsonwebtoken": "^9.0.0"
  }
}
```

### **Workspace Configuration**

**`pnpm-workspace.yaml` at root:**

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**`turbo.json` at root:**

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
  "tasks": {
    "dev": {
      "cache": false,
      "interactive": true
    },
    "build": {
      "outputs": ["dist/**", ".turbo/**"],
      "inputs": ["src/**", "package.json", "tsconfig.json"]
    },
    "deploy:prod": {
      "outputs": [],
      "cache": false
    },
    "test": {
      "outputs": ["coverage/**"]
    },
    "typecheck": {
      "outputs": []
    }
  }
}
```

---

## Consequences

### **Positive**

✅ **Shared Code**

- Auth logic defined once, used everywhere
- Bug fixes benefit all products
- Type-safe sharing prevents errors
- New products quickly inherit standards

✅ **Independent Deployments**

- Primary App ships without touching Marketing site
- Zero coupling between products
- Each team controls own release schedule
- Faster iteration on individual products

✅ **Scaling**

- Easy to add new products
- Clear ownership structure
- Teams autonomously ship
- Can extract products to separate repos later

✅ **Build Efficiency**

- Turborepo only rebuilds what changed
- Parallel builds (faster CI/CD)
- Shared caching across team
- Smaller cache size = faster CI/CD

✅ **Operational Clarity**

- Clear directory structure
- New developers quickly understand organization
- Products are discoverable
- Responsibility is obvious

✅ **Cloudflare Integration**

- Each app has own Worker
- Own KV/R2/D1 namespaces
- Independent configurations
- No resource conflicts

### **Negative / Trade-offs**

⚠️ **More complex initially**

- More files to manage upfront
- Setup takes longer than single app
- More boilerplate in early phase
- Mitigation: Templates provided for new apps

⚠️ **Workspace complexity**

- Need to understand pnpm workspaces
- Dependency resolution slightly complex
- monorepo-specific debugging skills needed
- Mitigation: Documentation provided, team trained

⚠️ **CI/CD coordination**

- Multiple deployments to orchestrate
- More complex GitHub Actions workflows
- Secrets management more complex (per-app secrets)
- Mitigation: Automation scripts handle complexity

⚠️ **Extraction overhead**

- If a product grows huge, extraction requires planning
- Shared packages need careful version management
- Mitigation: Clear versioning strategy documented

---

## Why This Over Alternatives?

### **Alternative 1: Multiple Repositories**

**Why rejected**:

- ❌ Shared code duplicated across repos
- ❌ Version mismatches across products
- ❌ Complex cross-repo dependency management
- ❌ Difficult to ensure consistency
- ❌ Team must manage multiple repos
- ❌ Type safety breaks across repo boundaries

### **Alternative 2: Single Repository with All Code at Root**

**Why rejected**:

- ❌ Unclear which code belongs to which product
- ❌ Products cannot deploy independently
- ❌ Scaling to 3+ products becomes chaotic
- ❌ No clear ownership
- ❌ Difficult to extract products later
- ❌ Difficult to reason about dependencies

### **Alternative 3: Domain-Based Naming**

**Why rejected**:

- ❌ `apps/api.business_name.com/` breaks if domain changes
- ❌ Requires refactoring when business needs change
- ❌ Ownership is about domain, not product
- ❌ Difficult to move domain to separate company
- ❌ Team organization unclear

**Chosen approach** wins because:

- ✅ Scalable to 10+ products
- ✅ Clear ownership per product
- ✅ Products deploy independently
- ✅ Shared code without duplication
- ✅ Easy extraction if needed
- ✅ Type-safe across apps
- ✅ Cloudflare-native workflow
- ✅ Team-friendly organization

---

## Managing Growth

### **Phase 1: Current (1-2 apps)**

- Single team maintains both apps
- Shared packages used by both
- Root-level scripts work smoothly

### **Phase 2: Scaling (3-5 apps)**

- Separate teams per major product
- Shared packages maintained by platform team
- Tighter dependency versioning
- More sophisticated CI/CD

### **Phase 3: Multiple Teams (5+ apps)**

- Clear API boundaries between packages
- Versioned package releases
- Cross-team dependency negotiation
- Possible monorepo split

### **Phase 4: Extraction (if needed)**

- High-value product extracted to separate repo
- Shared packages versioned and published internally
- Clear version contracts maintained
- Minimal coordination needed

---

## Extraction Path (Future Option)

If Primary App becomes huge and needs separate governance:

```bash
# Extract from monorepo to separate repository
git subtree split --prefix apps/primary-app -b primary-app-split
cd ../primary-app-repo
git pull ../BUSINESS_NAME primary-app-split

# Install shared packages from npm/registry
npm install @business_name/auth@1.0.0

# Update imports to use published packages
# Deploy independently
```

**No refactoring needed** — Product already isolated in `apps/primary-app/`.

---

## Related ADRs

- **ADR-001**: Using Perplexity Spaces for Agentic Development
- **ADR-003**: Idempotent Scripts and Operational Reliability
- **ADR-004**: Error Recovery Procedures (handling failures)

---

## Open Questions

1. **How to handle cross-app shared state?**
   - Answer: Use `packages/` for shared logic, each app owns own state

2. **How to version shared packages?**
   - Answer: Use semantic versioning, publish internally to private registry later if needed

3. **Can apps have different Node/TypeScript versions?**
   - Answer: Yes, but discouraged. Keep consistent in `engines` field in package.json

4. **How to handle database migrations across products?**
   - Answer: Migrations versioned in `packages/database/`, apps apply at deploy time

5. **What if an app needs a package that others don't?**
   - Answer: OK to add to app-specific dependencies. Keep packages generic and focused.

---

## Metrics for Success

1. **Development Velocity**
   - New app can be created in < 1 hour
   - New feature in any app ships in < 1 day
   - Zero blocking dependencies between products

2. **Code Reuse**
   - 80%+ of auth code shared via packages
   - Database types used across all apps
   - Common utilities in `packages/utils/`

3. **Deployment Independence**
   - Each app can deploy without affecting others
   - Primary App deploys multiple times per week
   - Marketing site deploys on separate schedule
   - Zero cross-app deployment failures

4. **Scalability**
   - CI/CD time < 5 minutes for full monorepo
   - No performance degradation with 5+ apps
   - Can add new app without reorganization

5. **Team Organization**
   - Clear ownership (who owns what)
   - New developers productive in < 1 day
   - Easy onboarding documentation

---

## Approval

- **Proposed by**: BUSINESS_NAME Development Team
- **Date**: 2026-01-12
- **Status**: Accepted and implemented
- **Next step**: Maintain structure as new products added

---

## References

- **Monorepo Documentation**: `MONOREPO_STRUCTURE.md` — User guide
- **Spec**: `docs/SPEC_MONOREPO.md` — Technical specification
- **PR #5**: Monorepo restructure (internal reference)
- **Turborepo**: <https://turbo.build/repo/docs>
- **pnpm Workspaces**: <https://pnpm.io/workspaces>
- **Cloudflare Workers**: <https://developers.cloudflare.com/workers/>
- **Cloudflare Pages Monorepos**: <https://developers.cloudflare.com/pages/configuration/monorepos/>
