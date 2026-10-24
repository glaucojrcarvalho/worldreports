#!/usr/bin/env python3
"""Stage annual Ukrainian goods+services trade and whole-economy GFCF ratios.

Source: SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0). Three current-price
components are paired with the ALREADY CURATED nominal GDP denominator,
all in UAH million on identical annual and territorial definitions.

The source indicator named "imports (−)" returns a POSITIVE magnitude.
The balance is exports MINUS imports. These are national-accounts goods
AND services; customs merchandise trade is a different measurement.

The script only stages *_from_sssu.csv sidecars for manual review.
"""
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE=("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
      "sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*")
STRUCTURE="SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)"
DIMENSIONS={
    "PRICE_TYPE":"CURR_PRICES","REGION":"UA00000000000000000",
    "BREAKDOWN_CATEGORY":"_T","BREAKDOWN":"_T",
    "SECTOR_ECONOMY":"S_1","FREQ":"A",
}
INDICATORS={"exports":"EXPORT_GOODS_SERV","imports":"IMPORT_GOODS_SERV",
            "gfcf":"GRS_FIX_CAP_FOR"}
ANCHORS={
    "exports":{2010:507869,2022:1857010,2024:2273580},
    "imports":{2010:551402,2022:2721793,2024:3832450},
    "gfcf":{2010:183867,2022:621856,2024:1414286},
}
FIRST,LAST=2010,2024
GDP=ROOT/"data"/"macro"/"gdp_nominal.csv"
TRADE=ROOT/"data"/"trade"/"trade_na_from_sssu.csv"
INVEST=ROOT/"data"/"spending"/"investment_from_sssu.csv"

def source_url(name:str)->str:
    if name not in INDICATORS:
        raise ValueError(f"Unknown SSSU macro component {name!r}")
    params={"c[INDICATOR]":INDICATORS[name]}
    params.update({"c["+k+"]":v for k,v in DIMENSIONS.items()})
    return BASE+"?"+urllib.parse.urlencode(params)

def get_response(name:str)->bytes:
    req=urllib.request.Request(source_url(name),headers={
        "Accept":"application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent":"WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req,timeout=45) as response:
        mime=response.headers.get("Content-Type","").lower()
        status=response.status
        raw=response.read(2_000_001)
    if status!=200 or not raw or len(raw)>2_000_000 or "sdmx.data+csv" not in mime:
        raise ValueError(f"{name}: invalid official CSV response")
    return raw

def parse_component(raw:bytes,name:str)->dict[int,int]:
    if name not in INDICATORS:
        raise ValueError("Unrecognized macro component")
    try:
        rd=csv.DictReader(StringIO(raw.decode("utf-8-sig")))
    except UnicodeError as exc:
        raise ValueError("Invalid SSSU CSV encoding") from exc
    required=set(DIMENSIONS)|{"INDICATOR","STRUCTURE_ID","ACTION",
                               "TIME_PERIOD","OBS_VALUE",
                               "UNITS_OF_MEASURE","SCALE","OBS_FLAG"}
    if not rd.fieldnames or not required.issubset(rd.fieldnames):
        raise ValueError(f"{name}: SDMX column schema drift")
    result={}
    for row in rd:
        if row["STRUCTURE_ID"]!=STRUCTURE or row["ACTION"]!="R":
            raise ValueError(f"{name}: dataflow revision/action changed")
        if row["INDICATOR"]!=INDICATORS[name] or any(
            row[k]!=v for k,v in DIMENSIONS.items()
        ):
            raise ValueError(f"{name}: unexpected dimension selection")
        if row["UNITS_OF_MEASURE"]!="1090" or row["SCALE"]!="6" or row["OBS_FLAG"]:
            raise ValueError(f"{name}: unit, scaling or observation flag changed")
        if row.get("TERRITORIAL_COVERAGE")!="Ukraine":
            raise ValueError(f"{name}: source territory label requires review")
        try:
            year=int(row["TIME_PERIOD"])
            amount=Decimal(row["OBS_VALUE"])
        except (TypeError,ValueError,InvalidOperation) as exc:
            raise ValueError(f"{name}: invalid annual observation") from exc
        if year in result:
            raise ValueError(f"{name}: duplicate observation {year}")
        if not amount.is_finite() or amount<=0 or amount!=amount.to_integral_value():
            raise ValueError(f"{name}: invalid positive million-UAH amount")
        if FIRST<=year<=LAST:
            if year in ANCHORS[name] and int(amount)!=ANCHORS[name][year]:
                raise ValueError(f"{name}: {year} value changed; review new vintage")
            result[year]=int(amount)
    if set(result)!=set(range(FIRST,LAST+1)):
        raise ValueError(f"{name}: incomplete 2010–2024 annual series")
    return result

def read_curated_gdp()->dict[int,int]:
    with GDP.open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=["year","nominal_uah_mn"]:
            raise ValueError("Curated GDP denominator columns changed")
        rows=list(reader)
    years={}
    for row in rows:
        year=int(row["year"])
        if year in years:
            raise ValueError("Duplicate nominal GDP year")
        amount=int(row["nominal_uah_mn"])
        if amount<=0:
            raise ValueError("Invalid GDP denominator")
        years[year]=amount
    if set(years)!=set(range(FIRST,LAST+1)) or years[2024]!=7662376:
        raise ValueError("GDP denominator vintage or coverage changed")
    return years

def pct(numerator:int,denominator:int)->str:
    return f"{Decimal(numerator)*100/Decimal(denominator):.4f}"

def to_csv(fieldnames:list[str],rows:list[dict])->str:
    dest=StringIO()
    writer=csv.DictWriter(dest,fieldnames=fieldnames,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return dest.getvalue()

def transform(raw_by_name:dict[str,bytes],gdp:dict[int,int])->tuple[str,str]:
    if set(raw_by_name)!=set(INDICATORS):
        raise ValueError("Need all three official component responses")
    x={name:parse_component(raw_by_name[name],name) for name in INDICATORS}
    trade=[]
    investment=[]
    for y in range(FIRST,LAST+1):
        gd=gdp[y];exp=x["exports"][y];imp=x["imports"][y];cap=x["gfcf"][y]
        trade.append({"year":y,"exports_pct_gdp":pct(exp,gd),
                      "imports_pct_gdp":pct(imp,gd),
                      "balance_pct_gdp":pct(exp-imp,gd),
                      "exports_uah_mn":exp,"imports_uah_mn":imp})
        investment.append({"year":y,"gfcf_pct_gdp":pct(cap,gd),
                           "gfcf_uah_mn":cap})
    return (
        to_csv(["year","exports_pct_gdp","imports_pct_gdp","balance_pct_gdp",
                "exports_uah_mn","imports_uah_mn"],trade),
        to_csv(["year","gfcf_pct_gdp","gfcf_uah_mn"],investment),
    )

def main()->None:
    gdp=read_curated_gdp()
    payloads={name:get_response(name) for name in INDICATORS}
    trade,investment=transform(payloads,gdp)
    for path,body in ((TRADE,trade),(INVEST,investment)):
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix(".tmp")
        tmp.write_text(body,encoding="utf-8")
        tmp.replace(path)
        print("Review-only sidecar:",path)

if __name__=="__main__":
    main()
