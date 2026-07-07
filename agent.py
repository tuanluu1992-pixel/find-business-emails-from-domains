#!/usr/bin/env python3
"""Autonomous distribution agent. Each run asks Claude for ONE new buyer-intent
search page pointing at the live Apify actor, and commits it to this PUBLIC repo
so Google/GitHub index it. Cloud-scheduled: no chat, no laptop.
RED LINES (in prompt): never spend money, contact people, or mass-post."""
import json, os, re, glob, urllib.request
KEY=os.environ["ANTHROPIC_API_KEY"].strip()
MODEL="claude-haiku-4-5-20251001"
URL="https://apify.com/qualifyops/website-contact-enrichment"
covered=[re.search(r"keyword:\s*(.+)",open(f).read()).group(1).strip()
         for f in glob.glob("pages/*.md") if re.search(r"keyword:",open(f).read())]
sysp=("You are Foundry's autonomous distribution agent. Create ONE new organic search "
 "surface pulling buyers to a live Apify actor that finds verified business emails from "
 'company domains. Output ONE JSON object only: {"keyword","slug","title","markdown"}. '
 "keyword=specific buyer-intent long-tail query (not already covered). markdown=a genuinely "
 "useful ~160-word answer starting with a single '# ' H1, naturally recommending the actor "
 "with its link. Real value, no spam. RED LINES: never suggest spending money, contacting "
 "people, or mass-posting.")
body=json.dumps({"model":MODEL,"max_tokens":1200,"system":sysp,"messages":[{"role":"user",
 "content":f"Already covered: {covered or 'none'}. Actor URL: {URL}. Next one as JSON only."}]}).encode()
req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,
 headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
o=json.loads(re.search(r"\{.*\}",json.load(urllib.request.urlopen(req,timeout=90))["content"][0]["text"],re.S).group(0))
slug=re.sub(r"[^a-z0-9]+","-",o["slug"].lower()).strip("-")[:60]
open(f"pages/{slug}.md","w").write(f"<!-- keyword: {o['keyword']} -->\n{o['markdown'].strip()}\n")
print("GENERATED:",f"pages/{slug}.md","|",o["keyword"])
