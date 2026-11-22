#!/usr/bin/env python3
"""Acquire FACTUAL Roma match lineups from cited AS Roma historical reports.

Only source link, Roma starting-XI name list, and explicitly written substitutions.
The original copyrighted reports are NOT redistributed. Historical material may
disagree with Wikipedia; source attribution is preserved. No inferred minutes.
"""
import concurrent.futures, datetime, html, json, pathlib, re, time, urllib.parse, urllib.request
from bs4 import BeautifulSoup
root=pathlib.Path("archive/wikitext")
base=pathlib.Path("lineup_acquisition");base.mkdir(exist_ok=True)
domain="www.asromaultras.org"
all_entries=[]
for f in sorted(root.glob("????-????.wikitext")):
  y=int(f.stem[:4])
  if not (1927<=y<=1937 or 2017<=y<=2025):continue
  urls=re.findall(r'https?://(?:www\.)?asromaultras\.org/[A-Za-z0-9_./%~-]+?\.html',f.read_text(encoding="utf-8"),re.I)
  for u in dict.fromkeys(urls):
    all_entries.append((f.stem,u))
# Limit request rate and source load. The tool can be re-run with a raised limit.
MAX=300
# Distribute selection across early and modern eras
early=[x for x in all_entries if int(x[0][:4])<1950]
modern=[x for x in all_entries if int(x[0][:4])>=2000]
sel=[]
for i in range(max(len(early),len(modern))):
 for group in (early,modern):
  if i<len(group) and len(sel)<MAX:sel.append(group[i])
 if len(sel)>=MAX:break
ua="RomaStatisticSourceResearch/0.9.3 (+https://github.com/AppInRome/PRAEVOL-2050-DATA)"
def parse(item):
 season,url=item
 try:
  req=urllib.request.Request(url,headers={"User-Agent":ua})
  with urllib.request.urlopen(req,timeout=19) as rsp:
   data=rsp.read(450000)
  soup=BeautifulSoup(data,"html.parser")
  for p in soup(["script","style","noscript"]):p.decompose()
  lines=[re.sub(r'\s+',' ',t).strip() for t in soup.get_text("\n",strip=True).splitlines()]
  # A Roma line is accepted only in the tabellino section near the top.
  starts=[i for i,t in enumerate(lines) if re.search(r"(?i)\btabellino\s+partita\b",t)]
  if not starts:return {"season":season,"url":url,"status":"no_match_report"}
  pattern=re.compile(r"(?i)^(?:a\.?s\.?\s*)?roma\s*(?:\([0-9][0-9 -]{2,15}\))?\s*:\s*(.+)$")
  spans=[]
  for idx in starts[:2]:
   for offset in range(idx+1,min(idx+48,len(lines))):
    hit=pattern.search(lines[offset])
    if hit:
     spans.append((offset,hit.group(1)));break
  if not spans:return {"season":season,"url":url,"status":"no_roma_line"}
  idx,whole=spans[0]
  # Archived pages often split a single XI at HTML line breaks. Join adjacent
  # name fragments only up to 11 entries, stopping before bench/coach/opponent.
  whole=whole.strip()
  def tokens(s):
   parts=[];part="";nest=0
   for ch in s:
    if ch=="(":nest+=1
    if ch==")":nest=max(0,nest-1)
    if ch in ",;" and nest==0:
     if part.strip():parts.append(part.strip())
     part=""
    else:part+=ch
   if part.strip():parts.append(part.strip())
   return parts
  for nextline in lines[idx+1:idx+16]:
   if len(tokens(whole))>=11:break
   if re.match(r"(?i)^(?:all(?:enatore)?\\.?|a\\s+disp\\.?|arbitro|riserve|panchina|lazio|inter|juventus|livorno|milan|note|marcatori|reti)\\s*[:.]",nextline):break
   if re.match(r"(?i)^.{0,28}\\s*\\([3-5]-[0-9]-[0-9-]+\\)\\s*:",nextline):break
   if len(nextline)>300 or not nextline.strip():break
   whole+=" "+nextline.strip()
  # Avoid parsing text containing an entire article or a table of scores.
  if len(whole)>550:return {"season":season,"url":url,"status":"long_line","sample":whole[:250]}
  # Parse semicolon/comma separators outside parenthetical substitutions.
  parts=[];part="";level=0
  for ch in whole:
   if ch=="(":level+=1
   if ch==")":level=max(0,level-1)
   if ch in ",;" and level==0:
    if part.strip():parts.append(part.strip())
    part=""
   else:part+=ch
  if part.strip():parts.append(part.strip())
  # Stop if header contains unrelated prose
  if len(parts)!=11:return {"season":season,"url":url,"status":"not_11","count":len(parts),"sample":whole[:250]}
  players=[];subs=[]
  for token in parts:
   token=re.sub(r"\s+"," ",token).strip()
   # Parenthesis may denote injury or other notes, NOT automatically substitutions.
   m=re.match(r"^(.+?)\s*\((\d{1,3})(?:[′'’]\s*|\s+)([^()]+)\)\s*$",token)
   if m:
    starter=m.group(1).strip();minute=int(m.group(2));on=m.group(3).strip()
    if minute>=1 and minute<=130 and len(on)<60:
     subs.append({"off":starter,"on":on,"minute":minute,"minute_display":str(minute),"confidence":"explicit_parenthetic_change"})
   else:
    starter=token
   players.append(starter)
  if any(len(p)>90 or len(p)<2 for p in players):return {"season":season,"url":url,"status":"invalid_name_length"}
  return {"season":season,"url":url,"status":"parsed_starting_xi","starters":players,"substitutions":subs,"formation":None}
 except Exception as ex:return {"season":season,"url":url,"status":"download_error","error":str(ex)[:200]}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures={}
 for n,item in enumerate(sel):
  futures[pool.submit(parse,item)]=item
  time.sleep(0.3)
 for n,fut in enumerate(concurrent.futures.as_completed(futures),1):
  results.append(fut.result())
  if n%25==0:print("Checked",n,"/",len(sel),flush=True)
summary={}
for result in results:summary[result["status"]]=summary.get(result["status"],0)+1
out={"generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"https://www.asromaultras.org/","scope":"Roma XI only, source-attributed; substitutes only if explicit name-minute pattern; no inferred minutes played","requested":len(sel),"counts":summary,"results":sorted(results,key=lambda x:(x["season"],x["url"]))}
(base/"roma_match_lineups.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUMMARY",json.dumps(summary),flush=True)
if summary.get("parsed_starting_xi",0)<25:raise SystemExit("Unexpectedly low parsed lineup coverage")
