# Startup Blueprint Website

## Overview

This is the landing page for the Startup Blueprint project. It serves as the main entrance for folks discovering the project, highlighting the AI-native approach and guiding them to the GitHub repository for getting started.

## Structure

```
website/
├── public/
│   ├── index.html      # Landing page
│   └── styles.css      # Styles
└── package.json        # Project config
```

## Development

```bash
# Install dependencies
pnpm install

# Run local development server
pnpm dev

# Access at http://localhost:8080
```

## Deployment

This site is automatically deployed to Cloudflare Pages on every commit to `main`.

**Custom Domain:** https://startup-blueprint.SuperiorByteWorks.com  
**Preview Deployments:** Enabled for PRs with the `Deploy: Website Preview` label

## Key Features

- **Clean, modern design** with dark theme
- **Cost breakdown** highlighting $150 total startup cost
- **Complete journey** from idea to deployed business
- **AI-native positioning** emphasizing Perplexity, OpenRouter, CrewAI
- **Clear CTAs** pointing to GitHub for getting started
- **Responsive** design for mobile and desktop

## Content Highlights

1. **Hero Section** - Value proposition and CTA
2. **Cost Breakdown** - Transparent pricing
3. **What You Get** - Feature grid
4. **The Journey** - 6-step timeline
5. **Why This Approach** - Benefits explained
6. **CTA Section** - Final call-to-action
7. **Footer** - Links to GitHub, docs, issues

## Tech Stack

- **HTML5** for structure
- **CSS3** with custom properties for styling
- **No build step** - static site
- **Deployed** via Cloudflare Pages
- **Font:** Inter (Google Fonts)

## Performance

- Zero JavaScript (static HTML/CSS only)
- Google Fonts preconnect for fast loading
- Optimized animations with CSS
- Semantic HTML for accessibility

## Future Enhancements

- [ ] Add social proof (testimonials, GitHub stars)
- [ ] Include video walkthrough
- [ ] Add interactive cost calculator
- [ ] Blog section for updates
- [ ] Newsletter signup
