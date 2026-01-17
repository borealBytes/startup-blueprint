# Quick Start Checklist

This is a 30-minute condensed version of the full blueprint. Use this when you need to move fast.

## Prerequisites

- [ ] Business name decided
- [ ] ~$500 budget for filing fees (varies by state)
- [ ] 1-2 hours of focused time

## 30-Minute Fast Track

### Step 1: Register Your LLC (10 min)

1. Go to your state's Secretary of State website
2. Search for "LLC formation" or "business registration"
3. Fill out the form with:
   - Business name
   - Registered agent (you can be your own)
   - Business address
4. Pay the filing fee (~$50-$500 depending on state)
5. Note your confirmation number

### Step 2: Get Your Domain (5 min)

1. Go to [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/)
2. Create account
3. Search for `BUSINESS-NAME.com`
4. Register for 10 years (~$140 total, ~$14/year)
5. Enable WHOIS privacy (free)

### Step 3: Setup Email Forwarding (10 min)

1. In Cloudflare, go to Email → Email Routing
2. Enable Email Routing for your domain
3. Add a custom address: `hello@BUSINESS-NAME.com` → forwards to your Gmail
4. Verify your Gmail address
5. Test by sending an email to `hello@BUSINESS-NAME.com`

### Step 4: Create GitHub Repo (5 min)

1. Go to [GitHub](https://github.com/new)
2. Create new repository: `BUSINESS-NAME`
3. Make it private
4. Initialize with README
5. Clone locally:

```bash
git clone https://github.com/YOUR-USERNAME/BUSINESS-NAME.git
cd BUSINESS-NAME
```

---

## Next Steps

You now have:

- ✅ Legal business entity
- ✅ Professional domain
- ✅ Email forwarding
- ✅ Version control

### What to do next

1. **Get EIN**: [Apply online](https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online) (free, takes 10 minutes)
2. **Open business bank account**: Use EIN + LLC certificate
3. **Set up accounting**: [Wave](https://www.waveapps.com/) (free) or [Stripe](https://stripe.com/) (paid)
4. **Build website**: Follow [Deployment Guide](./06-deployment-cicd.md)
5. **Document processes**: Use [Operations Manual](./07-operations-manual.md)

---

## Full Blueprint

For detailed instructions on each step, work through the full guides:

1. [Legal Foundation](./01-legal-foundation.md) - 2-3 hours
2. [Domain & DNS](./02-domain-dns.md) - 30 min
3. [Email Infrastructure](./03-email-infrastructure.md) - 1 hour
4. [Git & Repository](./04-git-repository.md) - 45 min
5. [Financial Tools](./05-financial-tools.md) - 1 hour
6. [Deployment & CI/CD](./06-deployment-cicd.md) - 1.5 hours
7. [Operations Manual](./07-operations-manual.md) - 2 hours

---

**Ready for the details?** → [Start with Guide #1](./01-legal-foundation.md)
