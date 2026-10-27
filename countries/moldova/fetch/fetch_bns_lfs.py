#!/usr/bin/env python3
"""Read-only discovery of BNS unemployment-survey table and methodology.

This is a SOURCE CODEBOOK audit, not a curated annual unemployment series.
The publisher identifies a 2019 labour-force-survey break and a second
2025 change (EMDOS 3, 2024-census weights and revised LFS methodology).
Never silently append those levels to discontinued pre-2019 series, or
equate them with WDI's ILO-modelled national rate.

Only original BNS PxWeb metadata is fetched; no chart, atlas CSV,
country.yaml, deployment or upstream repository is modified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

COUNTRY = Path(__file__).resolve().parents[1]
API = "https://statbank.statistica.md/PxWeb/api/v1/en/30%20Statistica%20sociala"
TABLE = "MUN160100_2025.px"
YEARS = tuple(range(2019, 2026))
OUT = COUNTRY / "data/macro/lfs_source_codebook_from_bns.json"
MAX_BYTES = 1_000_000
MAX_VISITS = 90


def get_json(url: str) -> tuple[object, str]:
    if not url.startswith(API + "/") and url != API:
        raise ValueError("Only the official BNS social-statistics API is allowed")
    req = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "worldreports-moldova-bns-lfs-source-audit/1.0",
    })
    with urlopen(req, timeout=35) as response:
        if response.status != 200:
            raise ValueError("BNS LFS metadata non-200 response")
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("BNS LFS response is not JSON")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("BNS LFS metadata unexpectedly exceeds 1MB")
    return json.loads(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def validate_metadata(node: object) -> list[dict]:
    if not isinstance(node, dict) or not isinstance(node.get("variables"), list):
        raise ValueError("Expected a BNS PxWeb variable codebook")
    variables = node["variables"]
    if len(variables) != 4:
        raise ValueError("BNS unemployment table dimensions revised")
    parsed = []
    for variable in variables:
        if not isinstance(variable, dict):
            raise ValueError("Malformed BNS dimension")
        ident = variable.get("code")
        values = variable.get("values")
        labels = variable.get("valueTexts")
        if (not isinstance(ident, str) or not ident
                or not isinstance(values, list) or not isinstance(labels, list)
                or len(values) != len(labels) or not values
                or any(not isinstance(s, str) for s in values + labels)
                or len(set(values)) != len(values)):
            raise ValueError("Malformed or ambiguous BNS category codebook")
        parsed.append({
            "code": ident, "name": str(variable.get("text", ident)),
            "categories": [{"code": code, "label": label}
                           for code, label in zip(values, labels)],
        })
    if len({v["code"] for v in parsed}) != 4:
        raise ValueError("Duplicate BNS dimension codes")
    expected = set(map(str, YEARS))
    candidates = [v for v in parsed if expected.issubset(
        {item["label"] for item in v["categories"]})]
    if len(candidates) != 1:
        raise ValueError("Expected one 2019–2025 annual reference dimension")
    year_dim = candidates[0]
    if any(item["label"].isdecimal() and len(item["label"]) == 4
           and int(item["label"]) > 2025 for item in year_dim["categories"]):
        raise ValueError("A 2026 series was mixed with 2019–2025 table")
    others = [v for v in parsed if v is not year_dim]
    # Require ALL three categorical axes, not an annual-only or
    # territory-mismatched table masquerading as an unemployment series.
    tokens = " ".join(v["name"].casefold() for v in others)
    if not (("sex" in tokens) and ("area" in tokens)
            and ("quarter" in tokens)):
        raise ValueError("BNS LFS must contain sex, area and quarter axes")
    title = str(node.get("title", "")).casefold()
    if title and not any(w in title for w in ("unemployment", "somaj", "șomaj")):
        raise ValueError("BNS codebook does not describe unemployment")
    return parsed


def discover(fetch=get_json) -> tuple[str, list[dict], str]:
    """Find TABLE by verified publisher ID, never guess category codes."""
    candidates = (
        "30%20Statistica%20sociala__03%20FM__03%20MUN__MUN060/" + TABLE,
        "03%20FM/03%20MUN/MUN060/" + TABLE,
        "03%20FM/03%20MUN/" + TABLE,
    )
    for suffix in candidates:
        url = API + "/" + suffix
        try:
            node, digest = fetch(url)
            return url, validate_metadata(node), digest
        except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
            continue
    listing, _ = fetch(API)
    if not isinstance(listing, list):
        raise ValueError("BNS social-statistics root is not a directory")
    queue = [(API, listing, 0)]
    visited = set()
    while queue:
        base, entries, depth = queue.pop(0)
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ValueError("Invalid BNS API directory entry")
            name = entry["id"]
            if (not name or name in (".", "..") or "/" in name
                    or "\\" in name):
                raise ValueError("Unsafe BNS directory segment")
            if depth == 0 and not (
                "fm" in name.casefold() or
                "labour" in str(entry.get("text", "")).casefold()
            ):
                continue
            url = base + "/" + quote(name, safe="")
            if url in visited:
                continue
            visited.add(url)
            if len(visited) > MAX_VISITS or depth > 6:
                raise ValueError("BNS labour API traversal exceeded safe limit")
            if name.casefold() == TABLE.casefold():
                payload, digest = fetch(url)
                return url, validate_metadata(payload), digest
            if entry.get("type") == "l":
                try:
                    child, _ = fetch(url)
                except (HTTPError, URLError, OSError):
                    continue
                if isinstance(child, list):
                    queue.append((url, child, depth + 1))
    raise ValueError("Official MUN160100_2025 table was not discovered")


def main() -> None:
    url, vars_, digest = discover()
    result = {
        "status": "review_only_unemployment_codebook_not_a_curated_series",
        "table": TABLE,
        "api_url": url,
        "original_metadata_sha256": digest,
        "years_verified_in_metadata": list(YEARS),
        "dimensions": vars_,
        "breaks_to_review": [
            "2019: BNS LFS new survey/sample and revised employment definition",
            "2025: EMDOS 3 sample, 2024 census-based weights and methods changed",
            "2026: separate new EU-aligned methodology; not part of this table",
        ],
        "publisher_methodology_url":
            "https://statistica.gov.md/ro/metodologii-statistice-104.html",
        "publisher_table_url":
            "https://statbank.statistica.md/PxWeb/pxweb/en/"
            "30%20Statistica%20sociala/"
            "30%20Statistica%20sociala__03%20FM__03%20MUN__MUN060/"
            "MUN160100_2025.px",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("BNS LFS 2019–2025 official coded metadata PASS")
    print("SHA256:", digest, "dim count:", len(vars_), "sidecar:", OUT)
    print("No national unemployment observations promoted; 2025 method break pending.")


if __name__ == "__main__":
    main()
