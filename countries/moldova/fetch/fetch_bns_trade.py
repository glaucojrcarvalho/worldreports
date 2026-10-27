#!/usr/bin/env python3
"""Audit BNS EXT010200 customs-goods exports by partner, without publication.

Official PxWeb: exports by countries AND groups, 1997-2025, thousand USD.
The table excludes left-bank Nistru enterprises and Bender. Its categories
include overlapping groups/totals, so it is UNSAFE to sum all partner rows.
Ukraine's CIS/other grouping changes in reference year 2024. Data from this
table must never be treated as WDI exports of goods AND services.

This tool writes a sidecar + metadata for human/source review only. It never
changes a curated CSV, SOURCES.yaml, a chart, country.yaml, or the atlas site.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
API_ROOT = ("https://statbank.statistica.md/PxWeb/api/v1/en/"
            "40%20Statistica%20economica")
TABLE_ID = "EXT010200.px"
OUTPUT = ROOT / "data/trade/exports_partner_from_bns.csv"
EVIDENCE = ROOT / "data/trade/exports_partner_source_metadata.json"
YEARS = tuple(range(2006, 2026))
ANCHOR_2025_THOUSAND_USD = 3_782_700.0  # BNS 2025 release: US$3,782.7 million
MAX_CELLS = 10_000
MAX_BYTES = 5_000_000


def request_json(url: str, body: object | None = None):
    headers = {"Accept": "application/json", "User-Agent": "worldreports-moldova-source-audit/1.0"}
    content = None
    if body is not None:
        content = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    with urlopen(Request(url, data=content, headers=headers), timeout=45) as res:
        if res.status != 200:
            raise ValueError(f"BNS HTTP {res.status}")
        raw = res.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("BNS response exceeded 5MB")
    return json.loads(raw.decode("utf-8-sig"))


def _metadata(node: object) -> bool:
    return isinstance(node, dict) and isinstance(node.get("variables"), list)


def locate_table(fetch=request_json) -> tuple[str, dict]:
    """Probe official API tree. Candidate paths are not treated as proof."""
    candidates = [
        "21%20EXT/EXT010200.px",
        "21%20EXT/EXT010/serii%20anuale/EXT010200.px",
        "21%20EXT/EXT010__serii%20anuale/EXT010200.px",
        "40%20Statistica%20economica__21%20EXT__EXT010__serii%20anuale/EXT010200.px",
    ]
    for candidate in candidates:
        url = API_ROOT + "/" + candidate
        try:
            node = fetch(url)
        except (HTTPError, ValueError, OSError):
            continue
        if _metadata(node) and "EXT010200" in url:
            return url, node

    # PxWeb has changed its directory layout before. Traverse only the
    # external-trade subtree; every candidate is checked by its table ID.
    root = fetch(API_ROOT)
    if not isinstance(root, list):
        raise ValueError("BNS root API is not a PxWeb directory")
    queue = [(API_ROOT, root, 0)]
    visited = set()
    calls = 0
    while queue:
        path, listing, depth = queue.pop(0)
        for entry in listing:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ValueError("Malformed BNS directory entry")
            item = entry["id"]
            if depth == 0 and not ("EXT" in item.upper() or
                                   "external trade" in str(entry.get("text", "")).lower()):
                continue
            if "/" in item or ".." in item:
                raise ValueError("Unsafe PxWeb child path")
            url = path + "/" + quote(item, safe="")
            if url in visited:
                continue
            visited.add(url)
            calls += 1
            if calls > 90 or depth >= 5:
                raise ValueError("BNS external-trade API discovery exceeded bounded traversal")
            try:
                child = fetch(url)
            except (HTTPError, OSError):
                continue
            if item.casefold() == TABLE_ID.casefold() and _metadata(child):
                return url, child
            if isinstance(child, list):
                queue.append((url, child, depth + 1))
    raise ValueError("Could not locate official BNS EXT010200 table")


def metadata_codes(payload: dict) -> tuple[str, str, dict, dict]:
    """Read coded dimensions by publisher labels, never guessed array offsets."""
    variables = payload.get("variables")
    if not isinstance(variables, list) or len(variables) != 2:
        raise ValueError("EXT010200 expected exactly partner and year dimensions")
    found = {}
    for dim in variables:
        code = dim.get("code")
        name = str(dim.get("text", code)).strip().casefold()
        values, labels = dim.get("values"), dim.get("valueTexts")
        if (not isinstance(code, str) or not isinstance(values, list)
                or not isinstance(labels, list) or len(values) != len(labels)
                or len(values) != len(set(values)) or any(not isinstance(v, str) for v in values)):
            raise ValueError("Malformed coded BNS dimension")
        if name in {"countries", "country", "țări", "tari"}:
            found["partner"] = (code, dict(zip(values, labels)))
        elif name in {"years", "year", "ani"}:
            found["year"] = (code, dict(zip(values, labels)))
        else:
            raise ValueError("Unrecognized BNS external-trade dimension: " + name)
    if set(found) != {"partner", "year"}:
        raise ValueError("BNS trade dimensions do not cover countries and years")
    pcode, partners = found["partner"]
    ycode, years = found["year"]
    if len(partners) < 50 or len(partners) > 500:
        raise ValueError("Unexpected BNS partner dimension size")
    if list(partners.values()).count("Total") != 1:
        raise ValueError("Missing or ambiguous BNS all-partners Total category")
    if len(years) < 29 or not set(map(str, YEARS)).issubset(years.values()):
        raise ValueError("BNS missing historical export years 2006-2025")
    if "export" not in str(payload.get("title", "exports")).casefold():
        raise ValueError("BNS table title no longer describes exports")
    return pcode, ycode, partners, years


def query(pcode: str, ycode: str, partners: dict, years: dict) -> dict:
    chosen_years = [code for code, label in years.items() if label in set(map(str, YEARS))]
    if len(chosen_years) != len(YEARS) or len(partners) * len(chosen_years) > MAX_CELLS:
        raise ValueError("Invalid or oversized export query")
    return {
        "query": [
            {"code": pcode, "selection": {"filter": "item", "values": list(partners)}},
            {"code": ycode, "selection": {"filter": "item", "values": chosen_years}},
        ],
        "response": {"format": "json-stat2"},
    }


def _positions(dataset: dict, dim_code: str, size: int) -> dict[str, int]:
    idx = dataset["dimension"][dim_code]["category"]["index"]
    if isinstance(idx, list):
        pos = {str(code): i for i, code in enumerate(idx)}
    elif isinstance(idx, dict):
        pos = {str(code): int(value) for code, value in idx.items()}
    else:
        raise ValueError("Malformed BNS JSON-stat category index")
    if sorted(pos.values()) != list(range(size)):
        raise ValueError("BNS JSON-stat dimension positions not a bijection")
    return pos


def decode(payload: dict, pcode: str, ycode: str, partners: dict, years: dict) -> dict:
    """Decode independent of JSON-stat dimension ordering; preserve null cells."""
    ids = payload.get("id")
    sizes = payload.get("size")
    values = payload.get("value")
    if (payload.get("class") != "dataset" or not isinstance(ids, list)
            or set(ids) != {pcode, ycode} or len(ids) != 2
            or not isinstance(sizes, list) or len(sizes) != 2
            or not all(isinstance(n, int) and n > 0 for n in sizes)
            or math.prod(sizes) > MAX_CELLS
            or not isinstance(payload.get("dimension"), dict)
            or not isinstance(values, (list, dict))):
        raise ValueError("Malformed BNS partner JSON-stat dataset")
    count = math.prod(sizes)
    if isinstance(values, list) and len(values) != count:
        raise ValueError("Truncated BNS export array")
    if isinstance(values, dict) and any(not str(k).isdigit() or int(k) >= count for k in values):
        raise ValueError("Invalid sparse BNS export array")
    indexes = {dim: _positions(payload, dim, n) for dim, n in zip(ids, sizes)}
    if set(indexes[pcode]) != set(partners):
        raise ValueError("BNS returned incomplete partner category set")
    selected_years = {code for code, value in years.items() if value in set(map(str, YEARS))}
    if set(indexes[ycode]) != selected_years:
        raise ValueError("BNS returned incorrect year selection")
    rows = {}
    for pc, name in partners.items():
        for yc in selected_years:
            coordinates = {pcode: pc, ycode: yc}
            offset = 0
            for dim, n in zip(ids, sizes):
                offset = offset * n + indexes[dim][coordinates[dim]]
            raw = values[offset] if isinstance(values, list) else values.get(str(offset))
            if raw is not None:
                if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw) or raw < 0:
                    raise ValueError("Negative, nonfinite or nonnumeric BNS goods exports")
                raw = float(raw)
            rows[(int(years[yc]), pc)] = (str(name), raw)
    if len(rows) != len(partners) * len(YEARS):
        raise ValueError("Missing BNS country-year coordinates")
    return rows


def verify(rows: dict, partners: dict) -> None:
    totals = [code for code, label in partners.items() if label == "Total"]
    if len(totals) != 1:
        raise ValueError("No unique BNS Total category")
    total = rows[(2025, totals[0])][1]
    if total is None or abs(total - ANCHOR_2025_THOUSAND_USD) > 2_000:
        raise ValueError(f"BNS exports 2025 vs publisher press release diverge: {total}")
    if any(rows[(year, totals[0])][1] is None for year in YEARS):
        raise ValueError("BNS total exports have gaps in completed years")


def render(rows: dict, partners: dict) -> str:
    stream = io.StringIO()
    stream.write("# BNS EXT010200; customs GOODS exports, thousand USD; country/group categories overlap.\n")
    stream.write("# Excludes firms on the left bank of the Nistru and municipality Bender.\n")
    stream.write("# Ukraine changes CIS/other grouping in 2024 (Geonomenclature 2024).\n")
    stream.write("# NO country shares or sums should be published until category taxonomy audit.\n")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("year", "publisher_partner_code", "publisher_partner_label", "exports_thousand_usd"))
    for year in YEARS:
        for code in partners:
            label, number = rows[(year, code)]
            writer.writerow((year, code, label, "" if number is None else f"{number:.1f}"))
    return stream.getvalue()



# These codes are BNS's own declared INDIVIDUAL countries. Category codes
# 1, 13 and 42 are overlapping country groups, NOT eligible country totals.
DESTINATION_CODES = {
    "romania_pct": ("35", "..Romania"),
    "turkey_pct": ("86", "..Turkey"),
    "italy_pct": ("27", "..Italy"),
    "czechia_pct": ("17", "..Czechia"),
}
UKRAINE_CODES = {"old": ("11", "..Ukraine (CSI)"),
                 "new": ("87", "..Ukraine")}
DESTINATIONS_SIDECAR = ROOT / "data/trade/destinations_from_bns.csv"
PARTNER_GROUPS = {"1": "CIS countries", "13": "European Union countries",
                  "42": "The other countries of the world"}


def verify_destination_taxonomy(rows: dict, partners: dict) -> None:
    """Fail closed on source taxonomy revisions, double-count or coverage gaps."""
    expected = {**PARTNER_GROUPS,
                **{code: label for code, label in DESTINATION_CODES.values()},
                **{code: label for code, label in UKRAINE_CODES.values()}}
    for code, label in expected.items():
        if partners.get(code) != label:
            raise ValueError(f"BNS changed partner code {code}: {partners.get(code)}")
    for year in YEARS:
        total = rows[(year, "0")][1]
        if total is None or total <= 0:
            raise ValueError(f"Missing BNS all-partners Total {year}")
        groups = [rows[(year, code)][1] for code in PARTNER_GROUPS]
        if any(value is None for value in groups) or abs(sum(groups) - total) > 0.3:
            raise ValueError(f"BNS country group partition mismatch {year}")
        ukraine_code = "11" if year <= 2023 else "87"
        opposite = "87" if ukraine_code == "11" else "11"
        if (rows[(year, ukraine_code)][1] is None or
                rows[(year, opposite)][1] is not None):
            raise ValueError(f"BNS Ukraine changed year-group split {year}")
        for code, _ in DESTINATION_CODES.values():
            val = rows[(year, code)][1]
            if val is None or val > total:
                raise ValueError(f"Missing/out-of-scope country {year}/{code}")
    ranked = sorted(
        ((value, code) for code, label in partners.items()
         if label.startswith("..")
         for value in [rows[(2025, code)][1]] if value is not None),
        reverse=True)[:5]
    if [code for _, code in ranked] != ["35", "86", "27", "17", "87"]:
        raise ValueError(f"2025 top individual export partners changed: {ranked}")


def render_destinations(rows: dict, partners: dict, response_sha: str,
                        metadata_sha: str) -> str:
    """Produce reproducible same-year customs-goods shares for review only."""
    verify_destination_taxonomy(rows, partners)
    stream = io.StringIO()
    for line in (
        "# BNS EXT010200.px — customs GOODS exports (not WDI goods and services).",
        "# Share in % of SAME-year ALL-PARTNERS goods exports, 2006–2025.",
        "# 2025 TOP FIVE INDIVIDUAL country destinations, based on current Statbank release.",
        "# Raw BNS source JSON-stat2 SHA256 " + response_sha + ".",
        "# BNS source metadata SHA256 " + metadata_sha + ".",
        "# Codes: Total=0; Romania=35, Turkey=86, Italy=27, Czechia=17; Ukraine=11 until 2023, 87 from 2024.",
        "# Ukraine changed from CIS to other-country GROUP in 2024; individual country remains Ukraine.",
        "# National customs universe excludes left-bank Nistru/Bender exporters; groups/totals never double-counted.",
        "# Full BNS Statbank 2025 total 3,780,863.9 thousand USD; BNS preliminary 2025 release 3,782.7m USD (different editions).",
        "# Missing source values remain blank; do not synthesize or interpolate.",
    ):
        stream.write(line + "\n")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("year", *DESTINATION_CODES.keys(), "ukraine_pct"))
    for year in YEARS:
        total = rows[(year, "0")][1]
        codes = [code for code, _ in DESTINATION_CODES.values()]
        codes.append("11" if year <= 2023 else "87")
        writer.writerow((year, *(f"{rows[(year, code)][1] / total * 100:.6f}"
                                 for code in codes)))
    return stream.getvalue()


def main() -> None:
    url, metadata = locate_table()
    pcode, ycode, partners, years = metadata_codes(metadata)
    request = query(pcode, ycode, partners, years)
    payload = request_json(url, request)
    rows = decode(payload, pcode, ycode, partners, years)
    verify(rows, partners)
    verify_destination_taxonomy(rows, partners)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(rows, partners), encoding="utf-8")
    response_sha = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    metadata_sha = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    DESTINATIONS_SIDECAR.write_text(
        render_destinations(rows, partners, response_sha, metadata_sha),
        encoding="utf-8")
    provenance = {
        "status": "publisher_verified_sidecar_not_curated_or_published",
        "api_url": url, "table": TABLE_ID, "publisher": "National Bureau of Statistics of Moldova",
        "publisher_ui": "https://statbank.statistica.md/PxWeb/pxweb/en/40%20Statistica%20economica/40%20Statistica%20economica__21%20EXT__EXT010__serii%20anuale/EXT010200.px",
        "press_release": "https://statistica.gov.md/index.php/en/international-trade-of-goods-of-the-republic-of-moldova-in-december-2025-9539_62323.html",
        "unit": "thousand USD", "years": [YEARS[0], YEARS[-1]],
        "codes": {"partner": pcode, "year": ycode},
        "partner_codebook": partners, "year_codebook": years,
        "metadata_sha256": hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
        "response_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "warnings": [
            "Customs GOODS, not national-accounts goods-and-services exports",
            "Groups, totals and constituent countries overlap: do not sum all categories",
            "Left-bank Nistru and Bender organizations excluded",
            "Ukraine group classification changes at 2024; do not splice group shares",
            "BNS latest table may differ from early 2025 preliminary release",
        ],
    }
    EVIDENCE.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Official BNS {TABLE_ID} audited via {url}: "
          f"{len(partners)} partner/group codes × {len(YEARS)} years = {len(rows)} cells")
    print("2025 total (million USD):", rows[(2025, next(k for k, v in partners.items() if v == "Total"))][1] / 1000)
    print("BNS partner destination shares verified against source: 20 years × 5 individual countries.")
    print("Research sidecars only. No canonical plate or registry changed.")


if __name__ == "__main__":
    main()
