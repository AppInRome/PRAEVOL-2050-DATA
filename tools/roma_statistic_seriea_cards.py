#!/usr/bin/env python3
"""Download public Serie A historical match-level team cards for Roma only.
Fields HY AY HR AR in Football-Data match-level CSV. No player attribution.
Season end no newer than 2026 and 2026-27 excluded pending source completion.
"""
import csv,datetime,io,json,pathlib,time,urllib.request,urllib.error
out=pathlib.Path("seriea_cards_import");out.mkdir(exist_ok=True)
source="https://www.football-data.co.uk/mmz4281/{code}/I1.csv"
fallback="https://raw.githubusercontent.com/qhtexas/football-dataset/main/datasets/serie-a/season-{code}.csv"
headers={"User-Agent":"Mozilla/5.0 RomaStatisticResearch/0.9.1"}
rows=[];summary=[]
for year in range(2005,2026):
 code=f"{year%100:02d}{(year+1)%100:02d}"
 urls=[source.format(code=code),fallback.format(code=code)]
 status={"season":f"{year}/{str(year+1)[-2:]}","source":None,"downloaded":False,"roma_matches":0,"with_cards":0,"failed":""}
 for url in urls:
  try:
   req=urllib.request.Request(url,headers=headers)
   with urllib.request.urlopen(req,timeout=30) as resp:
    txt=resp.read(2_000_000).decode("utf-8-sig",errors="replace")
   parsed=list(csv.DictReader(io.StringIO(txt)))
   if not parsed or "HomeTeam" not in parsed[0]:raise ValueError("Missing HomeTeam column")
   status["downloaded"]=True;status["source"]=url
   break
  except Exception as e:
   status["failed"]=repr(e)[:200]
   parsed=[]
 if parsed:
  for raw in parsed:
   home=(raw.get("HomeTeam") or "").strip();away=(raw.get("AwayTeam") or "").strip()
   if home.lower() not in ("roma","as roma") and away.lower() not in ("roma","as roma"):continue
   status["roma_matches"]+=1
   def card_int(key):
    v=(raw.get(key) or "").strip()
    try:
     n=int(float(v))
     if n<0 or n>20:return None
     return n
    except ValueError:return None
   hy,ay,hr,ar=map(card_int,("HY","AY","HR","AR"))
   if all(v is None for v in (hy,ay,hr,ar)):continue
   status["with_cards"]+=1
   def goals(key):
    try:return int(float((raw.get(key) or "").strip()))
    except:return None
   is_home=home.lower() in ("roma","as roma")
   date=(raw.get("Date") or "").strip()
   if "/" in date:
    parts=date.split("/")
    try:date=datetime.date(int(parts[2])+2000 if len(parts[2])==2 and int(parts[2])<50 else int(parts[2])+1900 if len(parts[2])==2 else int(parts[2]),int(parts[1]),int(parts[0])).isoformat()
    except:date=None
   else:
    try:date=datetime.date.fromisoformat(date[:10]).isoformat()
    except:date=None
   record={"season":status["season"],"date":date,"home":home,"away":away,"home_goals":goals("FTHG"),"away_goals":goals("FTAG"),"yellow_roma":hy if is_home else ay,"yellow_opponent":ay if is_home else hy,"red_roma":hr if is_home else ar,"red_opponent":ar if is_home else hr,"source_url":url,"competition":"Serie A","scope":"team_match","quality":"source_observation_unmatched"}
   rows.append(record)
 summary.append(status)
 print(status["season"],status["roma_matches"],status["with_cards"],flush=True)
 time.sleep(0.4)
(out/"roma_match_card_observations.json").write_text(json.dumps({"summary":summary,"rows":rows,"note":"Football-Data team match yellow/red counts, not disciplinary player identities."},ensure_ascii=False,indent=2))
print("TOTAL",len(rows),"SEASONS",sum(x["with_cards"]>0 for x in summary))
if len(rows)<300:raise SystemExit("Insufficient coverage; review sources")
