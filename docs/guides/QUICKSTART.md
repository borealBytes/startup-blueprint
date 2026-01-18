# Quickstart Checklist ⚡

**Get your business legally and operationally ready in ~30 minutes.**

This checklist covers the absolute essentials. Full details are in the numbered guides.

---

## Phase 1: Naming & Availability (15 min)

**Goal**: Confirm your business name is unique and available across all critical channels.

### Checklist

- [ ] **Brainstorm names** that are:
  - Memorable and pronounceable
  - Relevant to your business
  - Room to expand (not too narrow)
  - Professional (no slang or inside jokes)

  **Examples**: `AlertShield`, `PeakCapital`, `StreamSync`

- [ ] **Check availability** (use [this tool](https://instantdomainsearch.com)):
  - [ ] `BUSINESSNAME.com` (domain)
  - [ ] `BUSINESSNAME` LLC (state registrar, e.g., [Michigan LARA](https://onecorp.lara.state.mi.us))
  - [ ] `@BUSINESSNAME` on Twitter/X
  - [ ] `BUSINESSNAME` on GitHub
  - [ ] Email: `founder@BUSINESSNAME.com` (will work after domain + Gmail setup)

- [ ] **Pick your final name** and move forward

---

## Phase 2: Legal Entity (20 min)

**Goal**: Register your LLC with the state.

### Checklist

- [ ] **Go to your state's business registration site**
  - Michigan: [LARA](https://onecorp.lara.state.mi.us)
  - California: [Secretary of State](https://bpd.sos.ca.gov/forms/llc/llm.pdf)
  - New York: [Department of State](https://www.dos.ny.gov/business-services/online-business-services)
  - (Find yours: Google `[STATE] LLC registration`)

- [ ] **File your Articles of Organization** with:
  - Business name: `BUSINESS NAME, LLC`
  - Registered agent: You (or your address)
  - Address: Your current address (can change later)
  - Member(s): You (sole proprietor)
  - Manager(s): Yourself

- [ ] **Pay the filing fee** (~$50-150 depending on state)

- [ ] **Get your confirmation**. You'll receive:
  - Certificate of Organization (save this)
  - State File Number (save this)

- [ ] **Apply for EIN** (Employer Identification Number) at [IRS.gov](https://www.irs.gov/ein)
  - Takes 5 minutes
  - You'll get your EIN immediately
  - This is your business's tax ID
  - Save it

---

## Phase 3: Domain & Email (15 min)

**Goal**: Own your domain and set up professional email.

### Checklist

- [ ] **Register domain at [Cloudflare](https://www.cloudflare.com/products/registrar/)**
  - Go to Registrar > Register domain
  - Search for `BUSINESSNAME.com`
  - 10-year registration (~$100 total, ~$10/year)
  - Add to your cart and checkout
  - Keep it open for next step

- [ ] **Set up email routing** (still in Cloudflare)
  - Go to Email Routing
  - Enable Email Routing
  - Create custom address: `founder@BUSINESSNAME.com` → `[your-personal-email]@gmail.com`
  - Test: Send an email to `founder@BUSINESSNAME.com` from personal email, confirm it arrives in your inbox

- [ ] **Create a free Gmail for your business** (if not already done)
  - Go to [Gmail](https://accounts.google.com/signup/v2/weblogin)
  - Create: `BUSINESSNAME.founder@gmail.com` or similar
  - Enable 2FA with authenticator app (not SMS)
  - Download recovery codes and save them somewhere secure

---

## Phase 4: GitHub Repo (10 min)

**Goal**: Version control for your business docs and code.

### Checklist

- [ ] **Create GitHub account** if you don't have one
  - Go to [GitHub](https://github.com)
  - Sign up with business Gmail from Phase 3
  - Enable 2FA

- [ ] **Create private repository**
  - Click "New"
  - Name: `BUSINESSNAME` or `BUSINESSNAME.com`
  - Description: "BUSINESS NAME | Docs, code, operations"
  - Private: Yes
  - Initialize with README
  - Create

- [ ] **Add `.gitignore`**
  - Click "Add file" → "Create new file"
  - Name: `.gitignore`
  - Paste:

    ```
    .env
    .env.local
    node_modules/
    dist/
    build/
    .DS_Store
    *.swp
    .secrets/
    ```

  - Commit

---

## Phase 5: Success Validation ✅

**You're done with the essentials if:**

- [ ] LLC is registered (you have certificate + file number + EIN)
- [ ] Domain is registered and pointing to Cloudflare
- [ ] Email forwarding works (`founder@BUSINESSNAME.com` → your Gmail)
- [ ] GitHub repo is created and private
- [ ] All critical accounts have 2FA enabled
- [ ] Recovery codes are saved somewhere secure

**Estimated time**: 1-2 hours (including waiting for confirmations)

**Next step**: Move to the full guides for deeper setup:

1. [Legal Foundation](./01-legal-foundation.md) — More legal details
2. [Domain & DNS](./02-domain-dns.md) — Advanced domain setup
3. [Email Infrastructure](./03-email-infrastructure.md) — Multi-user email
4. [Git & Repository](./04-git-repository.md) — CI/CD and Perplexity Spaces
5. [Financial Tools](./05-financial-tools.md) — Accounting and taxes
6. [Deployment & CI/CD](./06-deployment-cicd.md) — Website automation
7. [Operations Manual](./07-operations-manual.md) — Repeatable processes

---

## 💡 Pro Tips

- **Do this when focused** (no distractions). You'll make fewer mistakes.
- **Save everything** (certificates, EINs, passwords). Use a password manager.
- **Name your business like you'll keep it forever.** Rebranding later is expensive.
- **Don't overthink it.** Your first LLC structure isn't permanent. You can change it.
- **Use strong passwords** everywhere. This is your business's identity.
- **Set reminders** for annual renewals (LLC, domain).

---

## ❓ Common Questions

**Q: Do I need a lawyer?**
A: Not for basic LLC registration. Forms are straightforward. If you have complex IP, co-founder agreements, or regulatory issues, consult a lawyer.

**Q: Can I do this in a different state?**
A: Yes. Delaware and Nevada are popular for tax reasons, but any state works. Most costs are similar.

**Q: What if the domain name is taken?**
A: Choose a variation (e.g., add "get" prefix, change TLD to `.io`, `.co`, `.dev`). Make sure it still looks professional.

**Q: Can I change my LLC name later?**
A: Yes, but it's expensive and creates confusion. Choose carefully now.

**Q: When do I need an accountant?**
A: Not immediately, but hire one before your first tax filing (usually Q1 of next year). Wave (free) is good for now.

---

**Done?** → Welcome to business ownership! 🎉 Now head to [Guide #1: Legal Foundation](./01-legal-foundation.md) for the deeper details.
