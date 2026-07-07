# Find business emails from a list of company domains (bulk, verified)

Turn a list of **company domains or websites** into **verified business emails**,
phone numbers, and social links — in bulk, via API. Live SMTP verification means
you only get (and pay for) deliverable emails, not bounces.

A pay-per-result **Hunter.io / Apollo.io / Clearbit alternative** you can call
from a script, a CRM automation, or an AI agent.

## Quick start

```bash
pip install -r requirements.txt
export APIFY_TOKEN=your_token   # free: https://console.apify.com/account/integrations
python find_emails.py
```

## What it does

| Input | Output per domain |
|---|---|
| `stripe.com` | verified emails, phone numbers, social/profile links |

- Bulk: pass hundreds of domains in one call.
- Verified: live email check, **no bounces billed**.
- API- and agent-friendly: one HTTP call, JSON out.

## Run it (no code)

▶️ **[Run on Apify →](https://apify.com/qualifyops/website-contact-enrichment)**

## Use cases

Lead-list enrichment · CRM hygiene · cold outbound · sales prospecting ·
recruiting · AI agent tools that need contact data from a domain.

---
Powered by the [Bulk Email Finder & Contact Enrichment](https://apify.com/qualifyops/website-contact-enrichment) Actor on Apify.
