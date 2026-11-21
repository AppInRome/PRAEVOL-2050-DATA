#!/usr/bin/env python3
"""Roma Statistic: collect manager stats, source page and chronology from Wikipedia.
This is one source snapshot: malformed sums are marked pending, never silently fixed.
"""
import json,datetime,re,sys,urllib.parse,urllib.request,time,pathlib
from html import unescape
try:from bs4 import BeautifulSoup
except Exception as e:sys.exit("beautifulsoup4 required")
out=pathlib.Path("coach_acquisition");out.mkdir(exist_ok=True)
title="Allenatori_e_presidenti_dell'Associazione_Sportiva_Roma"
url="https://it.wikipedia.org/wiki/"+urllib.parse.quote(title)
api="https://it.wikipedia.org/w/api.php"
ua="RomaStatisticCoachArchive/0.9 (+https://github.com/AppInRome/PRAEVOL-2050-DATA)"
query={"action":"parse","page":title,"format":"json","formatversion":2,"prop":"text|wikitext|revid"}
for step in range(4):
 try:
  req=urllib.request.Request(api+"?"+urllib.parse.urlencode(query),headers={"User-Agent":ua,"Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=50) as resp:data=json.loads(resp.read())
  break
 except Exception as e:
  if step==3:raise
  time.sleep(2+step*3)
page=data.get("parse",{})
if not page:raise RuntimeError(str(data)[:800])
html=page.get("text",None)
if isinstance(html,dict):html=html.get("*")
raw=page.get("wikitext",None)
if isinstance(raw,dict):raw=raw.get("*")
if not html:raise RuntimeError("missing parsed HTML")
soup=BeautifulSoup(html,"html.parser")
(out/"page.wikitext").write_text(raw or "",encoding="utf-8")
def cell(c):
 for sup in c.find_all("sup"):sup.decompose()
 for br in c.find_all("br"):br.replace_with(" ")
 return re.sub(r"\s+"," ",c.get_text(" ",strip=True)).strip()
tables=[]
for tbl in soup.find_all("table"):
 trs=tbl.find_all("tr")
 if not trs:continue
 head=" | ".join(cell(c) for c in trs[0].find_all(["th","td"]))
 if ("Percentuale" in head and "Incontri" in head) or ("Vittorie" in head and "Pareggi" in head and "Sconfitte" in head):
  tables.append(tbl)
if not tables:raise RuntimeError("no manager table found "+str([cell(t.find("tr"))[:120] for t in soup.find_all("table")][:30]))
tbl=tables[0]
rows=[]
for tr in tbl.find_all("tr")[1:]:
 cells=tr.find_all(["th","td"],recursive=False)
 cols=[cell(c) for c in cells]
 if len(cols)<9:continue
 # name, nationality, seasons, periods, games, win, draw, loss, pct
 name=cols[0]
 if not name or name.lower() in ("totale","nome"):continue
 def val(x):
  m=re.search(r"\b\d+\b",x.replace(".",""))
  return int(m.group(0)) if m else None
 gp,w,d,l=map(val,cols[4:8])
 if None in (gp,w,d,l):continue
 source_url=url
 raw_percentage=cols[8].replace(",",".").strip()
 try:pct=float(re.search(r"\d+(?:\.\d+)?",raw_percentage).group())
 except:pct=None
 valid=(w+d+l==gp)
 pct_valid=pct is None or abs(100*w/gp-pct)<0.11 if gp else False
 rows.append({"name":name,"nationality":cols[1],"seasons_label":cols[2],"periods":cols[3],"games":gp,"wins":w,"draws":d,"losses":l,"wins_pct_published":pct,"arithmetic_valid":valid,"percentage_valid":pct_valid,"quality":"wikipedia_validated_arithmetic" if valid and pct_valid else "source_inconsistent_review","source_url":source_url})
(out/"manager_table.json").write_text(json.dumps({"source":url,"revision":page.get("revid"),"downloaded_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"rows":rows},ensure_ascii=False,indent=2),encoding="utf-8")
for i,x in enumerate(rows):
 if not x["arithmetic_valid"]:print("BAD",x,flush=True)
print("MANAGERS",len(rows),"VALID",sum(x["quality"]=="wikipedia_validated_arithmetic" for x in rows),flush=True)
if len(rows)<40:raise RuntimeError("Unexpected manager table row count: "+str(len(rows)))
