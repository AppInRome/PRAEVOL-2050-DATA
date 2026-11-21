#!/usr/bin/env python3
"""Scarica tutte le 100 voci stagionali AS Roma da Wikipedia in originale."""
from __future__ import annotations
import csv,datetime,hashlib,json,os,pathlib,re,sys,time,urllib.error,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path("archive")
RAW=ROOT/"wikitext"
META=ROOT/"schede"
RAW.mkdir(parents=True,exist_ok=True)
META.mkdir(parents=True,exist_ok=True)
UA="RomaStatisticHistoricalArchive/0.6 (+https://github.com/AppInRome/PRAEVOL-2050-DATA; noncommercial research)"
HEADERS={"User-Agent":UA,"Accept":"application/json, text/plain, */*"}
HEAD=re.compile(r"(?m)^\s*(={2,6})\s*([^\n=]+?)\s*\1\s*$")
def request(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=60) as r:return r.read(12000000).decode("utf-8")
def fetch(title):
    api="https://it.wikipedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","formatversion":2,"prop":"revisions","rvslots":"main","rvprop":"ids|timestamp|content","redirects":1,"titles":title.replace("_"," ")})
    rest="https://it.wikipedia.org/w/rest.php/v1/page/"+urllib.parse.quote(title)+"/source"
    raw="https://it.wikipedia.org/w/index.php?"+urllib.parse.urlencode({"title":title,"action":"raw"})
    errors=[]
    for tag,url in [("MediaWiki Action API",api),("MediaWiki REST API",rest),("Wikipedia action=raw",raw)]:
        for attempt in range(3):
            try:
                body=request(url);rev=None;timestamp=None
                if tag=="MediaWiki Action API":
                    obj=json.loads(body);p=obj["query"]["pages"][0]
                    if p.get("missing"):return None,{"missing":True,"error":"Pagina assente"}
                    v=p["revisions"][0];rev=v.get("revid");timestamp=v.get("timestamp");body=v["slots"]["main"]["content"]
                elif tag=="MediaWiki REST API":
                    obj=json.loads(body);rev=obj.get("latest",{}).get("id");body=obj["source"]
                if not body or len(body)<100:raise ValueError("Risposta senza wikitext")
                return body,{"method":tag,"revision":rev,"revisionTimestamp":timestamp}
            except Exception as e:
                errors.append(f"{tag}/{attempt+1}: {type(e).__name__}: {str(e)[:180]}")
                time.sleep(min(2+attempt*3,9))
    return None,{"error":"; ".join(errors[-8:])}
def split_top(txt):
    fields=[];start=0;tpl=0;link=0;i=0
    while i<len(txt)-1:
        two=txt[i:i+2]
        if two=="{{":tpl+=1;i+=2;continue
        if two=="}}":tpl-=1;i+=2;continue
        if two=="[[":link+=1;i+=2;continue
        if two=="]]":link-=1;i+=2;continue
        if txt[i]=="|" and tpl==0 and link==0:
            fields.append(txt[start:i]);start=i+1
        i+=1
    fields.append(txt[start:]);return fields
def matches(wikitext):
    output=[]
    for m in re.finditer(r"\{\{\s*Incontro\s+di\s+club\b",wikitext,re.I):
        i=m.start();depth=0;end=None
        while i<len(wikitext)-1:
            two=wikitext[i:i+2]
            if two=="{{":depth+=1;i+=2;continue
            if two=="}}":
                depth-=1;i+=2
                if depth==0:end=i;break
                continue
            i+=1
        if end is None:continue
        parts=split_top(wikitext[m.start()+2:end-2]);p={}
        for part in parts[1:]:
            if "=" in part:
                k,v=part.split("=",1);p[k.strip().casefold()]=v.strip()
        output.append(p)
    return output
def main():
    manifest=[];nparsed=0
    for y in range(1927,2027):
        season=f"{y}-{y+1}";name=f"Associazione_Sportiva_Roma_{season}"
        source="https://it.wikipedia.org/wiki/"+name
        path=RAW/(season+".wikitext")
        if path.exists() and path.stat().st_size>100:
            txt=path.read_text(encoding="utf-8");meta={"method":"cache"}
        else:
            txt,meta=fetch(name)
        record={"season":season,"title":name.replace("_"," "),"source":source,"downloaded":bool(txt),**meta}
        if txt:
            path.write_text(txt,encoding="utf-8")
            groups=[{"level":len(m.group(1)),"title":m.group(2).strip()} for m in HEAD.finditer(txt)]
            games=matches(txt);nparsed+=len(games)
            (META/(season+".json")).write_text(json.dumps({"season":season,"source":source,"revision":meta.get("revision"),"headings":groups,"incontroDiClubTemplates":games},ensure_ascii=False,indent=2),encoding="utf-8")
            record.update({"bytes":len(txt.encode("utf-8")),"sha256":hashlib.sha256(txt.encode("utf-8")).hexdigest(),"sections":len(groups),"incontroDiClubTemplates":len(games)})
        manifest.append(record)
        print(f"{season}: {'OK' if txt else 'ERRORE'}; incontri-template={record.get('incontroDiClubTemplates',0)}",flush=True)
        time.sleep(1.0)
    good=sum(x["downloaded"] for x in manifest)
    report={"asOfUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"period":"1927-2026","pagesRequested":100,"pagesDownloaded":good,"pagesMissingOrBlocked":100-good,"templatesIncontroDiClub":nparsed,"quality":"Le pagine wikitext sono dati grezzi; template non equivale a partite verificate; assist non necessariamente documentati.","license":"Wikipedia CC BY-SA, con attribuzione e obblighi di riutilizzo","source":"https://it.wikipedia.org"}
    (ROOT/"manifest.json").write_text(json.dumps({"summary":report,"pages":manifest},ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"stato_stagioni.csv").open("w",encoding="utf-8-sig",newline="") as f:
        cols=["season","downloaded","revision","revisionTimestamp","bytes","sha256","sections","incontroDiClubTemplates","source","error"];w=csv.DictWriter(f,fieldnames=cols,delimiter=";",extrasaction="ignore");w.writeheader();w.writerows(manifest)
    (ROOT/"LEGGIMI.txt").write_text("ROMA STATISTIC - FONTE WIKIPEDIA STAGIONI 1927-2026\nTutti i file *.wikitext rappresentano testi originali di pagine Wikipedia, NON database validato.\nGli incontri in schede/*.json sono parametri grezzi dei template. Assist, minutaggi, arbitri e altre statistiche non sono presenti uniformemente.\nFonte e licenza: Wikipedia italiana, CC BY-SA (attribuire gli autori e la versione storica; verificare pagina licenza).\nConsulta manifest.json e stato_stagioni.csv per pagine mancanti o bloccate.\n",encoding="utf-8")
    output=pathlib.Path("ROMA_STATISTIC_WIKIPEDIA_1927_2026.zip")
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for p in sorted(ROOT.rglob("*")):
            if p.is_file():z.write(p,arcname=p.as_posix())
    print("RISULTATO",json.dumps(report,ensure_ascii=False),flush=True)
    if good==0:raise SystemExit("Download fallito: nessuna pagina ottenuta.")
if __name__=="__main__":main()
