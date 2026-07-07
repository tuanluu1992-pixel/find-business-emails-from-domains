"""Find verified business emails from a list of company domains.

Uses the Apify 'website-contact-enrichment' Actor: give it company domains,
get back verified emails, phones and social links (live SMTP check, no bounces
billed). Get a free API token at https://console.apify.com/account/integrations
"""
import os, requests

APIFY_TOKEN = os.environ["APIFY_TOKEN"]
ACTOR = "qualifyops~website-contact-enrichment"

domains = ["stripe.com", "notion.so", "linear.app"]

run = requests.post(
    f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={APIFY_TOKEN}",
    json={"domains": domains},
    timeout=300,
)
run.raise_for_status()
for row in run.json():
    print(row.get("domain"), "->", row.get("emails"), row.get("phones"))
