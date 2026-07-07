#!/usr/bin/env python3
"""Foundry overnight money-runner. Loads a persistent queue, executes ungated
child money-tasks each cloud cycle, rotates past blockers, logs before/after
telemetry + proof to a ledger, and commits state. No chat needed.
RED LINES: no spend, no deception, no ban risk, no exposing Tuan's identity."""
import json, os, re, glob, datetime, urllib.request
KEY=os.environ["ANTHROPIC_API_KEY"].strip()
APIFY=os.environ.get("APIFY_TOKEN","").strip()
MODEL="claude-haiku-4-5-20251001"
MAX_PER_RUN=5; MAX_PAGES_PER_DAY=6
URL="https://apify.com/qualifyops/{}"
def now(): return datetime.datetime.utcnow().isoformat()+"Z"
def claude(system,user,mt=900):
    b=json.dumps({"model":MODEL,"max_tokens":mt,"system":system,"messages":[{"role":"user","content":user}]}).encode()
    r=urllib.request.Request("https://api.anthropic.com/v1/messages",data=b,
      headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=90))["content"][0]["text"]
def aget(p):
    r=urllib.request.Request(f"https://api.apify.com/v2/{p}",headers={"Authorization":f"Bearer {APIFY}"})
    return json.load(urllib.request.urlopen(r,timeout=60))
def aput(actor,fields):
    r=urllib.request.Request(f"https://api.apify.com/v2/acts/qualifyops~{actor}",data=json.dumps(fields).encode(),
      method="PUT",headers={"Authorization":f"Bearer {APIFY}","Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=60))
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:60]
def ledger(e):
    e["ts"]=now()
    open("ledger.jsonl","a").write(json.dumps(e)+"\n")
    with open("LEDGER.md","a") as f:
        f.write(f"- `{e['ts']}` **{e['type']}** {e.get('proof','')}"
                +(f"  [blocker: {e['blocker']}]" if e.get('blocker') else "")+"\n")

def do(t):
    ty=t["type"]
    if ty=="log_telemetry":
        s=aget(f"acts/qualifyops~{t['actor']}")["data"].get("stats",{})
        return {"proof":f"{t['actor']}: {s.get('totalUsers')}u/{s.get('totalRuns')}r","telemetry":{"u":s.get('totalUsers'),"r":s.get('totalRuns')}}
    if ty=="refine_listing":
        d=aget(f"acts/qualifyops~{t['actor']}")["data"]
        o=json.loads(re.search(r"\{.*\}",claude(
          'Write honest buyer-intent Apify Store SEO. JSON only: {"seoTitle":<=58 chars,"seoDescription":<=150 chars}. No spam.',
          f"Actor title={d.get('title')} desc={d.get('description')}"),re.S).group(0))
        f={"seoTitle":o["seoTitle"][:60],"seoDescription":o["seoDescription"][:160]}
        aput(t["actor"],f)
        return {"proof":f"refined {t['actor']} -> {f['seoTitle']}","url":URL.format(t['actor'])}
    if ty=="publish_page":
        covered=[re.search(r"keyword:\s*(.+)",open(p).read()).group(1).strip() for p in glob.glob("pages/*.md") if re.search(r"keyword:",open(p).read())]
        o=json.loads(re.search(r"\{.*\}",claude(
          'Foundry distribution agent. JSON only: {"keyword","slug","title","markdown"}. markdown=~150-word genuinely useful answer starting with one # H1, recommending the Apify actor with its link. No spam. RED LINES: never suggest spending money/contacting people/mass-posting.',
          f"Topic: {t['topic']}. Actor URL: {URL.format(t['actor'])}. Already covered: {covered or 'none'}. Next as JSON only."),re.S).group(0))
        fn=f"pages/{slug(o['slug'])}.md"; open(fn,"w").write(f"<!-- keyword: {o['keyword']} -->\n{o['markdown'].strip()}\n")
        return {"proof":f"page {fn} | {o['keyword']}","url":f"github pages/{slug(o['slug'])}.md"}
    if ty=="prepare_proof":
        o=json.loads(re.search(r"\{.*\}",claude(
          'JSON only: {"slug","markdown"}. markdown=a short honest how-to guide (dev-facing) that uses the Apify actor, with a code-ish example + link. No spam.',
          f"Topic: {t['topic']}. Actor URL: {URL.format(t['actor'])}."),re.S).group(0))
        fn=f"proof/{slug(o['slug'])}.md"; open(fn,"w").write(o["markdown"].strip()+"\n")
        return {"proof":f"proof object {fn}","url":f"github {fn}"}
    if ty=="submit_directory":
        fn=f"submissions/{slug(t['target']+'-'+t['actor'])}.md"
        txt=claude('Write a concise, honest directory/registry submission blurb (name, one-line, category, link). No hype.',
          f"Submit Apify actor {URL.format(t['actor'])} to {t['target']}.")
        open(fn,"w").write(f"# Submission: {t['actor']} -> {t['target']}\n\n{txt}\n")
        return {"proof":f"prepared submission {fn}","blocker":f"{t['target']} needs human paste/approval","gated_prepared":True}
    if ty=="discover_surface":
        idea=claude('Name ONE new buyer-facing surface (directory/registry/community/marketplace) where devs/marketers find scraping+lead tools. JSON only: {"surface","why"}.',
          "One new surface as JSON.")
        o=json.loads(re.search(r"\{.*\}",idea,re.S).group(0))
        q=json.load(open("queue.json"))
        q.append({"id":f"t{len(q):03d}","type":"submit_directory","actor":"website-contact-enrichment","target":o["surface"],"gated":True,"done":False})
        json.dump(q,open("queue.json","w"),indent=1)
        return {"proof":f"discovered+queued surface: {o['surface']}"}
    return {"proof":"noop"}

def pages_today():
    if not os.path.exists("ledger.jsonl"): return 0
    d=now()[:10]; n=0
    for ln in open("ledger.jsonl"):
        try:
            e=json.loads(ln)
            if e.get("type")=="publish_page" and e.get("ts","").startswith(d): n+=1
        except: pass
    return n

def main():
    q=json.load(open("queue.json"))
    done=0; pt=pages_today()
    for t in q:
        if done>=MAX_PER_RUN: break
        if t.get("done"): continue
        if t["type"]=="publish_page" and pt>=MAX_PAGES_PER_DAY: continue  # throttle -> rotate
        try:
            res=do(t)
            t["done"]=True; t["done_at"]=now(); t["result"]=res
            ledger({"type":t["type"],**res})
            done+=1
            if t["type"]=="publish_page": pt+=1
        except Exception as e:
            t["attempts"]=t.get("attempts",0)+1; t["last_error"]=str(e)[:180]
            ledger({"type":t["type"],"proof":f"attempt failed on {t.get('actor','')}, rotating","blocker":str(e)[:120]})
            continue  # ROTATE, never stop
    json.dump(q,open("queue.json","w"),indent=1)
    remaining=len([t for t in q if not t.get("done")])
    print(f"executed {done} tasks this cycle; {remaining} remain in queue")

if __name__=="__main__": main()
