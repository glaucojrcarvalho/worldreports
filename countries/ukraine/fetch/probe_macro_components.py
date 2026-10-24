#!/usr/bin/env python3
"""Read-only discovery of four official Ukrstat national-accounts components.

No acceptance/publishing is implied: save exact SDMX-CSV responses into
ignored cache/ and record units, sign convention, years and sample values.
"""
from __future__ import annotations
import csv
from io import StringIO
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/"cache"
BASE=("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
      "sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*")
INDICATORS=("EXPORT_GOODS_SERV","IMPORT_GOODS_SERV","GRS_FIX_CAP_FOR","FIN_CON_GOV")
DIMENSIONS={"PRICE_TYPE":"CURR_PRICES","REGION":"UA00000000000000000",
            "BREAKDOWN_CATEGORY":"_T","BREAKDOWN":"_T",
            "SECTOR_ECONOMY":"S_1","FREQ":"A"}

def url(indicator:str)->str:
    if indicator not in INDICATORS:
        raise ValueError("Unknown macro indicator")
    q={"c[INDICATOR]":indicator}
    q.update({"c["+k+"]":v for k,v in DIMENSIONS.items()})
    return BASE+"?"+urllib.parse.urlencode(q)

def fetch(indicator:str)->tuple[str,bytes]:
    req=urllib.request.Request(url(indicator),headers={
        "Accept":"application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent":"WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req,timeout=50) as res:
        mime=res.headers.get("Content-Type","")
        payload=res.read(2_000_001)
        status=res.status
    if status!=200 or not payload or len(payload)>2_000_000 or "sdmx.data+csv" not in mime:
        raise ValueError("Invalid or oversized SSSU macro response")
    return mime,payload

def describe(raw:bytes,indicator:str)->dict:
    rows=list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
    if not rows or "OBS_VALUE" not in rows[0]:
        raise ValueError("No structured macro observations")
    for r in rows:
        if r["INDICATOR"]!=indicator or any(r.get(k)!=v for k,v in DIMENSIONS.items()):
            raise ValueError("Mixed unexpected national accounts dimensions")
    return {"status":"metadata_only_not_curated",
            "rows":len(rows),"columns":list(rows[0]),
            "first":[{k:r.get(k) for k in ("TIME_PERIOD","OBS_VALUE","UNITS_OF_MEASURE","SCALE","OBS_FLAG")} for r in rows[:4]],
            "last":[{k:r.get(k) for k in ("TIME_PERIOD","OBS_VALUE","UNITS_OF_MEASURE","SCALE","OBS_FLAG")} for r in rows[-4:]],
            "years":[r["TIME_PERIOD"] for r in rows]}

def main()->None:
    CACHE.mkdir(parents=True,exist_ok=True)
    out={}
    for indicator in INDICATORS:
        try:
            mime,raw=fetch(indicator)
            info=describe(raw,indicator)
            (CACHE/f"macro_{indicator.lower()}.csv").write_bytes(raw)
            out[indicator]={"mime":mime,"url":url(indicator),**info}
        except Exception as exc:
            out[indicator]={"status":"unverified","error":f"{type(exc).__name__}: {exc}"}
        print(indicator,out[indicator]["status"],out[indicator].get("rows",0))
    (CACHE/"macro_components_probe.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
