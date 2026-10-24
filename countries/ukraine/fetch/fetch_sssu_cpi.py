#!/usr/bin/env python3
"""Refresh Ukrainian headline CPI annual-average percentage via official SDMX.

Source SSSU:DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE(27.2.0)
  INDICATOR=INDEX_CONSUMPRICE
  BASE_PERIOD=PREV_YEAR (annual index, NOT December/December)
  REGION=UA00000000000000000 (publisher's Ukraine aggregate)
  GOODS_SERVICES_TYPE=0 (headline total)
  FREQ=A

2006-2025 are complete calendar years in the reviewed 2026-10-24 vintage.
Index 120.2 means annual-average CPI inflation of 20.2%, not 120.2%.
This fetcher never changes the curated cpi.csv; it only stages a review
sidecar cpi_from_sssu.csv after entire response has been checked.
"""
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SIDE_CAR=ROOT/"data"/"macro"/"cpi_from_sssu.csv"
DATAFLOW="SSSU:DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE(27.2.0)"
BASE=("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
      "sdmx/3.0/data/dataflow/SSSU/DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE/27.2.0/*")
FILTERS={
    "INDICATOR":"INDEX_CONSUMPRICE",
    "BASE_PERIOD":"PREV_YEAR",
    "REGION":"UA00000000000000000",
    "GOODS_SERVICES_TYPE":"0",
    "FREQ":"A",
}
FIRST,LAST=2006,2025
INDEX_ANCHORS={2008:Decimal("125.2"),2015:Decimal("148.7"),
               2022:Decimal("120.2"),2024:Decimal("106.5"),
               2025:Decimal("112.7")}
COLS=("year","annual_inflation_pct","cpi_index_prev_year")

def source_url()->str:
    return BASE+"?"+urllib.parse.urlencode({"c["+k+"]":v for k,v in FILTERS.items()})

def download()->bytes:
    request=urllib.request.Request(source_url(),headers={
        "Accept":"application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent":"WorldReports-Ukraine-Fetch/0.1",
    })
    with urllib.request.urlopen(request,timeout=50) as res:
        status=res.status
        ctype=res.headers.get("Content-Type","").lower()
        data=res.read(2_000_001)
    if status!=200 or not data or len(data)>2_000_000:
        raise ValueError("Ukrstat CPI response absent, truncated, or invalid")
    if "sdmx.data+csv" not in ctype or data.lstrip().lower().startswith((b"<html",b"<!doctype")):
        raise ValueError("Ukrstat CPI endpoint did not return SDMX-CSV")
    return data

def parse_cpi(raw:bytes)->list[dict[str,str]]:
    try:
        reader=csv.DictReader(StringIO(raw.decode("utf-8-sig")))
    except UnicodeError as exc:
        raise ValueError("Ukrstat CPI must use UTF-8 CSV") from exc
    required=set(FILTERS)|{"STRUCTURE_ID","ACTION","TIME_PERIOD","OBS_VALUE",
                           "UNITS_OF_MEASURE","SCALE","OBS_FLAG"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("Ukrstat CPI schema missing required SDMX fields")
    observations={}
    for row in reader:
        if row["STRUCTURE_ID"]!=DATAFLOW or row["ACTION"]!="R":
            raise ValueError("CPI dataflow revision/action mismatch")
        for dim,expected in FILTERS.items():
            if row[dim]!=expected:
                raise ValueError(f"Unexpected CPI selection {dim}={row[dim]}")
        if row["UNITS_OF_MEASURE"]!="1010" or row["SCALE"]!="0":
            raise ValueError("Unexpected CPI index unit or scale")
        if row["OBS_FLAG"]:
            raise ValueError("Suppressed or flagged CPI index needs manual review")
        try:
            year=int(row["TIME_PERIOD"])
            idx=Decimal(row["OBS_VALUE"])
        except (ValueError,TypeError,InvalidOperation) as exc:
            raise ValueError("Malformed CPI observation") from exc
        if year in observations:
            raise ValueError(f"Duplicate CPI year {year}")
        if not idx.is_finite() or not Decimal("1")<idx<Decimal("1000"):
            raise ValueError(f"Implausible CPI index for {year}")
        if year in INDEX_ANCHORS and idx!=INDEX_ANCHORS[year]:
            raise ValueError(f"CPI reference {year} changed: {idx}")
        # An incomplete current year cannot be treated as a full-year average.
        if year<LAST+1 and year>=FIRST:
            observations[year]=idx
    if set(observations)!=set(range(FIRST,LAST+1)):
        missing=sorted(set(range(FIRST,LAST+1))-set(observations))
        raise ValueError(f"CPI missing complete observations: {missing}")
    return [{"year":str(y),
             "annual_inflation_pct":f"{observations[y]-100:.1f}",
             "cpi_index_prev_year":f"{observations[y]:.1f}"}
             for y in range(FIRST,LAST+1)]

def render_csv(rows:list[dict[str,str]])->str:
    buf=StringIO()
    writer=csv.DictWriter(buf,fieldnames=COLS,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

def main()->None:
    staged=render_csv(parse_cpi(download()))
    SIDE_CAR.parent.mkdir(parents=True,exist_ok=True)
    tmp=SIDE_CAR.with_suffix(".tmp")
    tmp.write_text(staged,encoding="utf-8")
    tmp.replace(SIDE_CAR)
    print(f"Reviewed {FIRST}-{LAST} annual headline CPI observations into {SIDE_CAR}")
    print("Sidecar only; cpi.csv remains curated until manual revision acceptance")

if __name__=="__main__":
    main()
