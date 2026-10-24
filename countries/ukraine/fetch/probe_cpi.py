#!/usr/bin/env python3
"""Inspect the official Ukrainian annual-average headline CPI series.

Purpose: discover the exact SDMX CSV schema and annual observation coverage,
without adding a chart-ready series or inferring a missing observation.
A consumer price INDEX versus the preceding YEAR is distinct from December
vs December, monthly changes, or a partial-year observation.

Run: python3 countries/ukraine/fetch/probe_cpi.py --live
"""
from __future__ import annotations
import argparse
import csv
from io import StringIO
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/"cache"
DATAFLOW="SSSU:DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE(27.2.0)"
URL=("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
     "sdmx/3.0/data/dataflow/SSSU/DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE/27.2.0/*")
DIMENSIONS={
    "INDICATOR":"INDEX_CONSUMPRICE",
    "BASE_PERIOD":"PREV_YEAR",
    "REGION":"UA00000000000000000",
    "GOODS_SERVICES_TYPE":"0",
    "FREQ":"A",
}

def query_url()->str:
    return URL+"?"+urllib.parse.urlencode({"c["+k+"]":v for k,v in DIMENSIONS.items()})

def fetch()->tuple[str,bytes]:
    req=urllib.request.Request(query_url(),headers={
        "Accept":"application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent":"WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req,timeout=50) as response:
        status=response.status
        mime=response.headers.get("Content-Type","")
        payload=response.read(2_000_001)
    if status!=200 or not payload or len(payload)>2_000_000:
        raise ValueError("CPI source responded with invalid status/size")
    if "sdmx.data+csv" not in mime.lower():
        raise ValueError("CPI source did not return SDMX CSV")
    return mime,payload

def inspect(payload:bytes)->dict:
    try:
        rows=list(csv.DictReader(StringIO(payload.decode("utf-8-sig"))))
    except (UnicodeError,csv.Error) as exc:
        raise ValueError("Malformed CPI SDMX-CSV") from exc
    if not rows:
        raise ValueError("No annual CPI observations returned")
    required=set(DIMENSIONS)|{"TIME_PERIOD","OBS_VALUE","STRUCTURE_ID"}
    if not required.issubset(rows[0]):
        raise ValueError("CPI source missing essential dimensions")
    for row in rows:
        if any(row[k]!=v for k,v in DIMENSIONS.items()):
            raise ValueError("CPI response mixed wrong dimensions")
    years=[row["TIME_PERIOD"] for row in rows]
    return {
        "status":"candidate_only_not_curated",
        "columns":list(rows[0]),
        "observations":len(rows),
        "years":years,
        "sample_first":rows[:4],
        "sample_last":rows[-4:],
        "source_dataflow":DATAFLOW,
    }

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args()
    if not args.live:
        print("CPI probe requires --live; no network calls were made")
        return
    CACHE.mkdir(exist_ok=True,parents=True)
    report={"url":query_url(),"status":"unverified"}
    try:
        mime,payload=fetch()
        report={"url":query_url(),"mime":mime,**inspect(payload)}
        (CACHE/"ukraine_cpi_raw.csv").write_bytes(payload)
    except Exception as exc:
        report["error"]=f"{type(exc).__name__}: {exc}"
    (CACHE/"ukraine_cpi_probe.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CPI discovery: "+report["status"]+", rows="+str(report.get("observations",0)))

if __name__=="__main__":
    main()
