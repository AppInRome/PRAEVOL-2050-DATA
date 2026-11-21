#!/usr/bin/env python3
"""Roma Statistic: roster-linked Wikidata biographies, sourced and quality filtered.
Run on GitHub Actions. This script only extracts public source data; it never
infers an exact debut or farewell match from a season roster.
"""
from __future__ import annotations
import collections, datetime, json, pathlib, re, time, urllib.parse, urllib.request, urllib.error, sys
ROOT=pathlib.Path("archive/wikitext")
OUT=pathlib.Path("biography")
OUT.mkdir(exist_ok=True)
UA="RomaStatisticData/0.8.1 (historical AS Roma project; https://github.com/AppInRome/PRAEVOL-2050-DATA)"
def get(url, tries=5):
    error=None
    for attempt in range(tries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=35) as resp:
                return json.load(resp)
        except Exception as e:
            error=e
            time.sleep(2*(attempt+1))
    raise error
def action(base,**params):
    params.update({"action":params.get("action","query"),"format":"json","formatversion":2})
    return get(base+"?"+urllib.parse.urlencode(params))
def groups(xs,n):
    for i in range(0,len(xs),n):yield xs[i:i+n]
def norm(x):
    return str(x).replace("_"," ").strip().casefold()
def parse():
    people={}
    rawrows=0
    for p in sorted(ROOT.glob("????-????.wikitext")):
        season=p.stem
        raw=p.read_text(encoding="utf-8")
        for mt in re.finditer(r"\{\{\s*Calciatore\s+in\s+rosa\s*\|",raw,re.I):
            snippet=raw[mt.end():mt.end()+600].split("}}",1)[0]
            nm=re.search(r"(?:^|\|)\s*nome\s*=\s*\[\[([^\]]{2,220})\]\]",snippet,re.I)
            if not nm:continue
            wikilink=nm.group(1)
            target=wikilink.split("|",1)[0].strip()
            shown=wikilink.split("|",1)[-1].strip()
            if not target or any(c in target for c in "[{}<>"):continue
            key=norm(target)
            if key not in people:people[key]={"target":target,"label":shown,"seasons":[]}
            if season not in people[key]["seasons"]:people[key]["seasons"].append(season)
            rawrows+=1
    return list(people.values()),rawrows
def wiki_id_map(entries):
    ap="https://it.wikipedia.org/w/api.php"
    output={};errors=[]
    for i,batch in enumerate(groups(entries,35)):
        titles=[e["target"] for e in batch]
        try:
            result=action(ap,action="query",prop="pageprops",ppprop="wikibase_item",redirects=1,titles="|".join(titles))
            renames={}
            for entry in result.get("query",{}).get("normalized",[]):renames[norm(entry["from"])]=entry["to"]
            for entry in result.get("query",{}).get("redirects",[]):renames[norm(entry["from"])]=entry["to"]
            pages={norm(page["title"]):page for page in result["query"]["pages"]}
            for e in batch:
                name=e["target"];visited=set()
                while norm(name) in renames and norm(name) not in visited:
                    visited.add(norm(name));name=renames[norm(name)]
                page=pages.get(norm(name))
                data={"target":e["target"],"label":e["label"],"seasons":e["seasons"],"wiki_resolved":name}
                if page:
                    data["wikidata"]=page.get("pageprops",{}).get("wikibase_item")
                    data["wiki_url"]="https://it.wikipedia.org/wiki/"+urllib.parse.quote(page["title"].replace(" ","_"))
                    if page.get("pageprops",{}).get("disambiguation") is not None:data["disambiguation"]=True
                output[norm(e["target"])]=data
        except Exception as ex:
            errors.append(f"batch {i}: {ex}")
            for e in batch:output[norm(e["target"])]=dict(e,error=str(ex))
        print(f"Wikipedia title matching {min((i+1)*35,len(entries))}/{len(entries)}",flush=True)
        time.sleep(0.65)
    return list(output.values()),errors
def property_date(entity, prop):
    claims=[x for x in entity.get("claims",{}).get(prop,[]) if x.get("rank")!="deprecated" and x.get("mainsnak",{}).get("snaktype")=="value"]
    selected=[]
    for x in claims:
        v=x["mainsnak"].get("datavalue",{}).get("value",{})
        if not isinstance(v,dict):continue
        try:
            dt=v["time"];precision=v["precision"]
            m=re.match(r"^[+-](\d{4,})-(\d\d)-(\d\d)T",dt)
            if not m:continue
            year,month,day=map(int,m.groups())
            if year<1800 or year>2100:continue
            if precision>=11:date=f"{year:04d}-{month:02d}-{day:02d}"
            elif precision==10:date=f"{year:04d}-{month:02d}"
            elif precision==9:date=f"{year:04d}"
            else:continue
            selected.append((date,precision,x.get("rank")=="preferred",len(x.get("references",[]))))
        except (KeyError,ValueError,TypeError):continue
    # Unresolved conflicting dates are not published as facts.
    days={date for date,precision,_,_ in selected if precision==11}
    if len(days)>1:return None,0,"conflict"
    selected.sort(key=lambda x:(x[2],x[1],x[3]),reverse=True)
    if not selected:return None,0,"absent"
    date,precision,*_=selected[0]
    return date,precision,"exact" if precision==11 else "partial"
def enrich(items):
    ids=sorted(set(e["wikidata"] for e in items if e.get("wikidata") and not e.get("disambiguation")))
    known={};errors=[]
    for idx,batch in enumerate(groups(ids,35)):
        try:
            obj=action("https://www.wikidata.org/w/api.php",action="wbgetentities",ids="|".join(batch),props="claims|descriptions",languages="it|en")
            for key,entity in obj.get("entities",{}).items():
                dob,precision,status=property_date(entity,"P569")
                dead,dead_precision,dead_status=property_date(entity,"P570")
                occ={s.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id") for s in entity.get("claims",{}).get("P106",[]) if isinstance(s.get("mainsnak",{}).get("datavalue",{}).get("value"),dict)}
                descr=" ".join(v.get("value","") for v in entity.get("descriptions",{}).values()).lower()
                football=bool(occ & {"Q937857","Q615798","Q2066131"}) or any(x in descr for x in ("calciator","footballer","football player","portiere","soccer player"))
                known[key]={"birth_date":dob,"birth_precision":precision,"birth_status":status,"death_date":dead,"death_precision":dead_precision,"death_status":dead_status,"football_entity":football}
        except Exception as ex:
            errors.append(f"wikidata batch {idx}: {ex}")
        print(f"Wikidata entity acquisition {min((idx+1)*35,len(ids))}/{len(ids)}",flush=True)
        time.sleep(0.6)
    for item in items:
        e=known.get(item.get("wikidata"),{})
        item.update(e)
        item["source_url"]="https://www.wikidata.org/wiki/"+item["wikidata"] if item.get("wikidata") else item.get("wiki_url")
        item["quality"]="linked_roster_wikidata_footballer" if item.get("wikidata") and e.get("football_entity") and item.get("birth_status")=="exact" else "review_or_missing"
    return errors
def main():
    entries,rawrows=parse()
    items,errors=wiki_id_map(entries)
    errors+=enrich(items)
    summary={"downloaded_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"wiki_roster_links_raw":rawrows,"distinct_wikilinks":len(entries),"wikipedia_entities":sum(bool(i.get("wikidata")) for i in items),"football_entities":sum(bool(i.get("football_entity")) for i in items),"birth_dates_day_precision":sum(i.get("birth_status")=="exact" for i in items),"birth_dates_reliable":sum(i.get("quality")=="linked_roster_wikidata_footballer" for i in items),"death_dates_day_precision":sum(i.get("death_status")=="exact" for i in items),"errors":errors[:30],"statement":"Date with Wikidata precision below day, conflicts or ambiguous identity are excluded from daily anniversaries; exact Roma debuts and farewells are not inferred."}
    (OUT/"player_biographies.json").write_text(json.dumps({"summary":summary,"players":items},ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUMMARY "+json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
