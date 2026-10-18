#!/usr/bin/env python3
"""Audit migrated content without modifying posts or inventing locations."""
import csv, json, re, sys, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote

ROOT=Path("content")
OUT=Path("audit-results")
OUT.mkdir(exist_ok=True)
COUNTRIES=set("""Argentina Australia Austria Bangladesh Belize Bolivia Brazil Bulgaria Cambodia Canada Chile China Colombia Costa Rica Croatia Ecuador Egypt Fiji France Germany Greece India Indonesia Ireland Italy Japan Kenya Laos Malaysia Mexico Morocco Myanmar Nepal Panama Paraguay Peru Philippines Portugal Singapore Spain Sri_Lanka South_Africa Switzerland Tanzania Thailand Turkey United_Kingdom United_States Vietnam New_Zealand Czechia Czech_Republic England""".split())
ALIASES={"UK":"United_Kingdom","USA":"United_States","U.S.A.":"United_States","Brasil":"Brazil","Czech":"Czech_Republic","United States of America":"United_States"}
PHOTO_HOST="photos.offonourown.co.uk"
img_re=re.compile(r"""(?:src|href|data-src|data-lazy-src|poster)\s*=\s*["']([^"']+\.(?:jpe?g|png|gif|webp|avif)(?:\?[^"']*)?)["']|https?://[^\s"'<>]+\.(?:jpe?g|png|gif|webp|avif)(?:\?[^\s"'<>]*)?""",re.I)
url_re=re.compile(r'https?://[^\s"\'<>),]+',re.I)
def frontmatter(text):
    if not text.startswith("---\n"):return {},text
    end=text.find("\n---",4)
    if end<0:return {},text
    block=text[4:end].splitlines()
    data={};key=None
    for line in block:
        m=re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$',line)
        if m:
            key=m.group(1);value=m.group(2).strip().strip("'\"")
            data[key]=[] if not value else value
        elif key and re.match(r'^\s*-\s+',line):
            if not isinstance(data[key],list):data[key]=[]
            data[key].append(re.sub(r'^\s*-\s+','',line).strip().strip("'\""))
    return data,text[end+4:]
def norm(x):return re.sub(r'\s+','_',x.strip()).replace("-","_")
rows=[];images=[];urls=set()
for p in sorted(ROOT.rglob("*")):
    if p.suffix.lower() not in (".html",".md",".markdown") or not p.is_file():continue
    data,body=frontmatter(p.read_text(encoding="utf-8"))
    labels=(data.get("categories",[]) or [])+(data.get("destinations",[]) or [])
    if isinstance(labels,str):labels=[labels]
    valid=sorted(set(ALIASES.get(x,norm(x)) for x in labels)&COUNTRIES)
    section=p.relative_to(ROOT).parts[0]
    if section in ("stories","travel"):
        rows.append({"file":str(p),"title":data.get("title",""),"section":section,"countries":"; ".join(x.replace("_"," ") for x in valid),"categories":"; ".join(labels),"status":"mapped_from_category" if valid else "needs_review","reason":"" if valid else "No recognised country category; review article location evidence"})
    found=set()
    for m in img_re.finditer(body):
        val=m.group(1) if m.group(1) else m.group(0)
        val=val.replace("&amp;","&").strip()
        for u in url_re.findall(val):
            u=u.rstrip(".,;")
            if u not in found:
                found.add(u);urls.add(u)
                host=urlparse(u).hostname or ""
                kind="cloudflare" if host==PHOTO_HOST else ("old_wordpress" if "offonourown.co.uk" in host and "/wp-content/uploads/" in u else "external")
                images.append({"file":str(p),"url":u,"host":host,"type":kind,"http_status":"","note":""})
def check(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"OffOnOurOwn-MediaAudit/1.0","Range":"bytes=0-0"},method="GET")
        with urllib.request.urlopen(req,timeout=12) as resp:return str(resp.status),""
    except urllib.error.HTTPError as e:return str(e.code),str(e.reason)
    except Exception as e:return "ERROR",str(e)[:100]
# Network tests only for Cloudflare media; legacy external assets are reported for manual review.
targets=sorted(u for u in urls if (urlparse(u).hostname or "")==PHOTO_HOST)
status={}
with ThreadPoolExecutor(max_workers=6) as pool:
    futures={pool.submit(check,u):u for u in targets}
    for f in as_completed(futures):status[futures[f]]=f.result()
for item in images:
    if item["url"] in status:item["http_status"],item["note"]=status[item["url"]]
    elif item["type"]=="external":item["note"]="Legacy external asset; requires independent verification"
    elif item["type"]=="old_wordpress":item["note"]="Still points at WordPress uploads"
for name,records,cols in [
    ("post-country-audit.csv",rows,["file","title","section","countries","categories","status","reason"]),
    ("image-audit.csv",images,["file","url","host","type","http_status","note"])]:
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(records)
summary={"posts_checked":len(rows),"posts_with_recognised_country":sum(bool(r["countries"]) for r in rows),"posts_needing_country_review":sum(not r["countries"] for r in rows),"image_references":len(images),"unique_cloudflare_urls_tested":len(targets),"cloudflare_url_failures":sum(s not in ("200","206") for s,_ in status.values()),"wordpress_image_references":sum(i["type"]=="old_wordpress" for i in images),"external_image_references":sum(i["type"]=="external" for i in images)}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
print("Reports written to audit-results/")
