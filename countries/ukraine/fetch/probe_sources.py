#!/usr/bin/env python3
"""Read-only SSSU and NBU discovery; never creates curated chart datasets.

Run with network access:
    python3 countries/ukraine/fetch/probe_sources.py --live

All reports go into countries/ukraine/cache/ (gitignored). HTTP failures are
recorded as unverified; they are never converted to empty/zero observations.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "cache" / "source_probe.json"
SSSU_DATAFLOWS = (
    "https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
    "sdmx/2.1/dataflow?detail=full"
)
SSSU_DSD_ROOT = (
    "https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
    "sdmx/2.1/datastructure/SSSU"
)
SSSU_PRIORITY_DSD = {
    "national_accounts": "DSD_ANNUAL_NATIONAL_ACCOUNTS",
    "consumer_prices": "DSD_PRICE_CHANGE_CONSUMER_GOODS_SERVICE",
    "population": "DSD_POPULATION_STR",
    "labour_force_annual": "DSD_LABOR_FORCE_A",
    "goods_trade": "DSD_EXTERNAL_TRADE_OF_GOODS",
    "deaths_by_cause": "DSD_POPULATION_DEATH_CAUSE",
}
NBU_FX = "https://bank.gov.ua/NBU_Exchange/exchange_site"
GDP_2022_OFFICIAL = -28.8
GDP_SHARED_SCALE = (-18.0, 18.0)
OFFICIAL_GINI_2021 = 0.244
GINI_MISSING_YEARS = tuple(range(2022, 2026))


def download(url: str, *, accept: str, limit: int = 8_000_000) -> bytes:
    """Read bounded official API bytes, rejecting HTML disguised as success."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "WorldReports-Ukraine-Research/0.1 (+https://github.com/akitaonrails/worldreports/issues/1)",
        "Accept": accept,
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        code = response.getcode()
        content_type = response.headers.get("Content-Type", "").lower()
        payload = response.read(limit + 1)
    if code != 200:
        raise ValueError(f"Unexpected API HTTP status {code}")
    if not payload or len(payload) > limit:
        raise ValueError("Empty or oversized API response")
    if "text/html" in content_type or re.match(br"\s*(<!doctype html|<html)", payload, re.I):
        raise ValueError("HTML/error page returned instead of structured data")
    return payload


def parse_dataflows(payload: bytes) -> list[dict[str, str]]:
    """Parse SSSU SDMX 2.1 structures without assuming any series availability."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("Invalid SSSU dataflow XML") from exc
    flows = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] != "Dataflow":
            continue
        code = item.attrib.get("id")
        if not code:
            continue
        names = {}
        dsd = ""
        for el in item.iter():
            short = el.tag.rsplit("}", 1)[-1]
            if short == "Name" and el.text:
                lang = el.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "und")
                names[lang] = el.text.strip()
            if short == "Ref" and el.attrib.get("class") == "DataStructure":
                dsd = el.attrib.get("id", "")
        flows.append({
            "id": code,
            "version": item.attrib.get("version", ""),
            "name_en": names.get("en", ""),
            "name_uk": names.get("uk", ""),
            "dsd": dsd,
        })
    if not flows:
        raise ValueError("No SDMX Dataflow records: endpoint or schema must be reviewed")
    return flows



def make_sssu_dsd_url(dsd_id: str) -> str:
    """Only query recognized SDMX structural identifiers, not arbitrary paths."""
    if not re.fullmatch(r"[A-Z0-9_]+", dsd_id):
        raise ValueError("Invalid SDMX DSD identifier")
    return f"{SSSU_DSD_ROOT}/{dsd_id}/latest?references=none"


def parse_dsd_dimensions(payload: bytes) -> list[dict]:
    """Return the dimensions' exact code identifiers in declared order.

    Dimensions by themselves are not evidence that an individual GDP series
    is comparable or complete; the code lists must be inspected next.
    """
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("Invalid SSSU DSD XML") from exc
    names = {"Dimension", "TimeDimension", "MeasureDimension"}
    result = []
    for item in root.iter():
        short = item.tag.rsplit("}", 1)[-1]
        if short not in names:
            continue
        code = item.attrib.get("id")
        if not code:
            continue
        ref = next((el.attrib for el in item.iter()
                    if el.tag.rsplit("}", 1)[-1] == "Ref"), {})
        enumeration = next(
            (el for el in item.iter() if el.tag.rsplit("}", 1)[-1] == "Enumeration"),
            None,
        )
        codelist_ref = ""
        if enumeration is not None:
            codelist_ref = next(
                (el.attrib.get("id", "") for el in enumeration.iter()
                 if el.tag.rsplit("}", 1)[-1] == "Ref"), ""
            )
        result.append({
            "dimension": code,
            "position": item.attrib.get("position", ""),
            "concept_ref": ref.get("id", ""),
            "codelist_ref": codelist_ref,
            "local_name": short,
        })
    if not result:
        raise ValueError("No SDMX dimensions were found in DSD response")
    return result



def make_sssu_codelist_url(codelist_id: str) -> str:
    if not re.fullmatch(r"[A-Z0-9_]+", codelist_id):
        raise ValueError("Invalid SDMX codelist ID")
    base = SSSU_DSD_ROOT.rsplit("/datastructure/", 1)[0]
    return f"{base}/codelist/SSSU/{codelist_id}/latest?references=none"


def parse_sssu_codelist(payload: bytes) -> list[dict]:
    """Extract official SDMX code IDs and English/Ukrainian labels."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("Invalid SSSU codelist XML") from exc
    results = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] != "Code":
            continue
        code = item.attrib.get("id")
        if not code:
            continue
        names = {}
        for node in item:
            if node.tag.rsplit("}", 1)[-1] == "Name" and node.text:
                lang = node.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "und")
                names[lang] = node.text.strip()
        results.append({"code": code, "name_en": names.get("en", ""),
                        "name_uk": names.get("uk", "")})
    if not results:
        raise ValueError("No SDMX codelist Code elements in response")
    return results


def make_fx_url(start: str = "20220104", end: str = "20220110", currency: str = "USD") -> str:
    for value in (start, end):
        datetime.strptime(value, "%Y%m%d")
    if start > end:
        raise ValueError("FX start is after end")
    if not re.fullmatch(r"[A-Za-z]{3}", currency):
        raise ValueError("Currency code must be three letters")
    params = urllib.parse.urlencode({
        "start": start,
        "end": end,
        "valcode": currency.lower(),
        "sort": "exchangedate",
        "order": "asc",
    })
    return f"{NBU_FX}?{params}&json"


def parse_fx(payload: bytes, currency: str = "USD", *,
             start: str | None = None, end: str | None = None) -> list[dict]:
    """Validate bounded NBU FX rows; never implicitly rescale units."""
    try:
        rows = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed NBU JSON") from exc
    if not isinstance(rows, list) or not rows:
        raise ValueError("NBU response must be a nonempty JSON array")
    cleaned = []
    for row in rows:
        if not isinstance(row, dict) or row.get("cc", "").upper() != currency.upper():
            raise ValueError("Unexpected currency in NBU FX response")
        published = datetime.strptime(row["exchangedate"], "%d.%m.%Y").date()
        units = int(row.get("units", 1))
        if units <= 0:
            raise ValueError("Invalid NBU currency units")
        # NBU documents rate_per_unit separately; if missing, rate is for 'units'.
        per_unit = float(row["rate_per_unit"]) if "rate_per_unit" in row else float(row["rate"]) / units
        if not (0 < per_unit < 1000):
            raise ValueError("Implausible rate; inspect units, currency or endpoint")
        stamp = published.strftime("%Y%m%d")
        if (start and stamp < start) or (end and stamp > end):
            raise ValueError("Date outside requested NBU FX interval")
        cleaned.append({"date": published.isoformat(), "currency": currency.upper(),
                        "uah_per_unit": per_unit})
    if len({row["date"] for row in cleaned}) != len(cleaned):
        raise ValueError("Duplicate NBU exchange dates")
    return sorted(cleaned, key=lambda row: row["date"])


def validate_gini(series: dict[int, float | None]) -> None:
    if series.get(2021) != OFFICIAL_GINI_2021:
        raise ValueError("2021 Gini differs from official published anchor")
    for year in GINI_MISSING_YEARS:
        if year not in series or series[year] is not None:
            raise ValueError(f"{year} Gini is missing, not zero/estimated")


def growth_requires_shared_scale_review() -> bool:
    low, high = GDP_SHARED_SCALE
    return not (low <= GDP_2022_OFFICIAL <= high)


def run_live() -> dict:
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "discovery_only_not_accepted_data",
        "source_probes": {},
    }
    probes = report["source_probes"]
    try:
        catalog = parse_dataflows(download(SSSU_DATAFLOWS, accept="application/xml"))
        regex = re.compile("GDP|PRICE|CPI|POPULATION|EMPLOY|TRADE|NATIONAL ACCOUNT|ВВП|ЦІН|НАСЕЛЕН", re.I)
        candidates = [r for r in catalog if regex.search(" ".join(map(str, r.values())))]
        probes["sssu_dataflow_catalog"] = {
            "result": "parsed_metadata_only",
            "endpoint": SSSU_DATAFLOWS,
            "dataflows_count": len(catalog),
            "candidate_dataflows": candidates[:60],
            "all_dataflows": catalog,
            "caution": "A name is not proof of units, geography, coverage or actual time-series data.",
        }
    except Exception as exc:
        probes["sssu_dataflow_catalog"] = {
            "result": "unverified",
            "endpoint": SSSU_DATAFLOWS,
            "error": f"{type(exc).__name__}: {exc}",
        }
    structures = {}
    for topic, dsd_id in SSSU_PRIORITY_DSD.items():
        dsd_url = make_sssu_dsd_url(dsd_id)
        try:
            raw_structure = download(dsd_url, accept="application/xml")
            if topic in {"national_accounts", "consumer_prices", "population"}:
                cache = ROOT / "cache"
                cache.mkdir(parents=True, exist_ok=True)
                (cache / f"sssu_dsd_{topic}.xml").write_bytes(raw_structure)
            dimensions = parse_dsd_dimensions(raw_structure)
            structures[topic] = {
                "result": "parsed_structure_only",
                "endpoint": dsd_url,
                "dsd": dsd_id,
                "dimensions": dimensions,
                "caution": "Dimension codes require verified codelists and observation selection.",
            }
        except Exception as exc:
            structures[topic] = {
                "result": "unverified",
                "endpoint": dsd_url,
                "error": f"{type(exc).__name__}: {exc}",
            }
    probes["sssu_priority_dsd"] = structures
    # Inspect official code values for national accounts only; still no
    # assumption about which combination is valid or comparable.
    na_codes = {}
    target = structures.get("national_accounts", {})
    for dimension in target.get("dimensions", []):
        if dimension["dimension"] not in {"INDICATOR", "PRICE_TYPE", "REGION", "FREQ"}:
            continue
        code_id = dimension.get("codelist_ref")
        if not code_id:
            na_codes[dimension["dimension"]] = {
                "result": "unverified", "reason": "DSD lacks direct codelist reference"}
            continue
        catalog_url = make_sssu_codelist_url(code_id)
        try:
            values = parse_sssu_codelist(download(catalog_url, accept="application/xml"))
            na_codes[dimension["dimension"]] = {
                "result": "parsed_codes_only",
                "endpoint": catalog_url,
                "codelist": code_id,
                "count": len(values),
                "values": values[:200],
            }
        except Exception as exc:
            na_codes[dimension["dimension"]] = {
                "result": "unverified",
                "endpoint": catalog_url,
                "error": f"{type(exc).__name__}: {exc}",
            }
    probes["sssu_national_accounts_codelists"] = na_codes
    url = make_fx_url()
    try:
        points = parse_fx(download(url, accept="application/json"),
                          start="20220104", end="20220110")
        probes["nbu_usd_fx"] = {
            "result": "bounded_daily_schema_parsed",
            "endpoint": url,
            "count": len(points),
            "sample": points[:5],
            "caution": "Not an annual average, a complete historical series or an accepted CSV.",
        }
    except Exception as exc:
        probes["nbu_usd_fx"] = {
            "result": "unverified", "endpoint": url,
            "error": f"{type(exc).__name__}: {exc}",
        }
    probes["gdp_anchor"] = {
        "result": "official_publication_anchor_only",
        "year": 2022, "growth_pct": GDP_2022_OFFICIAL,
        "spine_bounds_pct": list(GDP_SHARED_SCALE),
        "shared_scale_review_required": growth_requires_shared_scale_review(),
        "source": "https://stat.gov.ua/uk/news/valovyy-vnutrishniy-produkt-ukrayiny-u-2022-2025-rokakh-dynamika-struktura-ta-chynnyky-zmin",
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicit opt-in to read-only API calls")
    options = parser.parse_args()
    if not options.live:
        print("Ukraine SDMX/NBU discovery: skipped (run with --live to query official APIs)")
        return
    result = run_live()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovery report written to {REPORT}")
    for name, value in result["source_probes"].items():
        if "result" in value:
            print(f"{name}: {value['result']}")
        else:
            for topic, item in value.items():
                print(f"{name}.{topic}: {item.get('result', 'not_processed')}")


if __name__ == "__main__":
    main()
