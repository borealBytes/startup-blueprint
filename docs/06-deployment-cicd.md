# 6. Deployment & CI/CD 🚀

**Executive Summary**: Deploy your website and set up automated CI/CD using GitHub Actions and Cloudflare Pages. Time: 1.5 hours.

---

## Why This Matters

### Always Up-to-Date

Every change you merge to `main` can trigger an automatic deployment.

### Professional Web Presence

A fast, secure site on your domain builds credibility for BUSINESS NAME.

### Low Maintenance

No manual FTP uploads. No "What version is live?" confusion.

---

## Architecture

```mermaid
graph LR
    A["GitHub Repo"] --> B["GitHub Actions"]
    B --> C["Build Website"]
    C --> D["Cloudflare Pages"]
    D --> E["https://BUSINESS-NAME.com"]

    style B fill:#e1f5ff
    style D fill:#c8e6c9
```

---

## Step 1: Choose Website Stack

### Options

| Stack           | Complexity | Use When            |
| --------------- | ---------- | ------------------- |
| Static HTML/CSS | Low        | Landing page only   |
| Next.js (React) | Medium     | Marketing + app     |
| Astro           | Medium     | Content-heavy sites |

**Recommendation**: If you're just starting, use **simple static HTML/CSS** for a landing page. You can upgrade later.

---

## Step 2: Create Website Folder

In your repo:

1. Create `website/` directory
2. Add basic files:

```text
website/
├─ index.html
├─ styles.css
└─ README.md
```

### Example `index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BUSINESS NAME</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <main>
      <h1>BUSINESS NAME</h1>
      <p>Short, clear description of what BUSINESS NAME does.</p>
      <a href="mailto:founder@BUSINESS-NAME.com">Contact</a>
    </main>
  </body>
</html>
```

---

## Step 3: Set Up Cloudflare Pages

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select **Pages**
3. Click **Create a project**
4. Connect to GitHub
5. Select your BUSINESS NAME repo
6. Configure build settings:
   - Framework: None (for static)
   - Build command: `npm run build` (or leave empty for pure static)
   - Output folder: `website`
7. Deploy

### Custom Domain

1. In Cloudflare Pages → Custom domains
2. Add `BUSINESS-NAME.com`
3. Cloudflare auto-configures DNS CNAME
4. Wait for SSL to be issued (few minutes)

---

## Step 4: GitHub Actions CI Workflow

### Basic Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install
        working-directory: ./website

      - name: Run build
        run: npm run build
        working-directory: ./website
```

This ensures your website builds successfully before merging.

---

## Step 5: Auto-Deploy with Cloudflare

Cloudflare Pages integrates directly with GitHub:

- On each push to `main`:
  - GitHub updates code
  - Cloudflare pulls the latest commit
  - Runs build (if configured)
  - Deploys to production URL

**No additional action needed** once integrated.

---

## Step 6: Smoke Tests

Once deployed:

- [ ] Visit `https://BUSINESS-NAME.com`
- [ ] Verify SSL (padlock icon) works
- [ ] Check that site loads quickly
- [ ] Test on mobile and desktop
- [ ] Click contact link (does it open your email client?)

---

## Checklist: Deployment & CI/CD Complete ✅

- [ ] `website/` folder created
- [ ] Basic `index.html` page committed
- [ ] Cloudflare Pages connected to GitHub
- [ ] Custom domain pointing to Cloudflare Pages
- [ ] GitHub Actions CI workflow created
- [ ] Site builds successfully on each push
- [ ] Production site loads correctly

---

## Dependencies

**Before this**:

- [Guide 2: Domain & DNS](./02-domain-dns.md)
- [Guide 4: Git & Repository](./04-git-repository.md)

**After this**: [Guide 7: Operations Manual](./07-operations-manual.md)

---

## Estimated Total Time: 1.5 hours

- Website folder and content: 30 min
- Cloudflare Pages setup: 30 min
- GitHub Actions: 15 min
- Testing: 15 min

---

## Next Steps

1. ✅ Complete this guide
2. ➡️ Move to [Guide 7: Operations Manual](./07-operations-manual.md)
