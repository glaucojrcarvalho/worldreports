#!/usr/bin/env python3
"""Guarded publisher fetch of a SINGLE 2024 Moldova census foreign-born share.

Review-only sidecar: never overwrite curated data, plates or country.yaml.
The census snapshot is NOT UN migrant stock, NOT a full-year series and
NOT an immigrant arrival flow. Original publisher: BNS 2025-08-25.
"""
from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import io
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = ("https://statistica.gov.md/en/final-results-of-the-2024-population-"
       "and-housing-census-migration-10121_61958.html")
OUTPUT = ROOT / "data" / "migration" / "foreign_born_census_from_bns.csv"
YEAR = 2024
SHARE = 4.4
ROUNDED_COUNT_THOUSAND = 106.7


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag: str):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, value: str):
        if not self.hidden:
            self.parts.append(value)


def parse_official_page(content: bytes) -> tuple[int, float]:
    if len(content) > 3_000_000:
        raise ValueError("BNS census page unexpectedly large")
    page = VisibleText()
    page.feed(content.decode("utf-8", errors="strict"))
    text = re.sub(r"\s+", " ", " ".join(page.parts).replace("\u00a0", " ")).strip()
    if not text or "National Bureau of Statistics" not in text:
        raise ValueError("Not the BNS official English publication")
    if "25.08.2025" not in text or "April 8, 2024" not in text:
        raise ValueError("Publisher release/census reference date was revised")
    # The actual text links COUNTRY OF BIRTH (not citizenship) to both
    # original publisher measurements in the same sentence.
    pattern = (
        r"persons born in other countries\s*[—–:-]?\s*"
        r"(?P<count>\d{2,3}[.,]\d)\s*thousand persons"
        r"\s*\(or\s*(?P<share>\d{1,2}[.,]\d)%\s+of the population\)"
    )
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    if len(matches) != 1:
        raise ValueError("Ambiguous/missing BNS country-of-birth census statement")
    count = float(matches[0]["count"].replace(",", "."))
    share = float(matches[0]["share"].replace(",", "."))
    if count != ROUNDED_COUNT_THOUSAND or share != SHARE:
        raise ValueError("BNS foreign-born census original values changed")
    return YEAR, share


def review_csv(year: int, share: float, raw_sha: str) -> str:
    if year != YEAR or share != SHARE or not re.fullmatch(r"[a-f0-9]{64}", raw_sha):
        raise ValueError("Unreviewed census share/year or digest")
    out = io.StringIO()
    out.write("# REVIEW ONLY: exact observed BNS census snapshot, not an annual migration series.\n")
    out.write("# Original publisher 2025-08-25; reference date 2024-04-08, 4.4% born abroad.\n")
    out.write("# Original HTML SHA256: " + raw_sha + "\n")
    out.write("# Source: " + URL + "\n")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["year", "foreign_born_pct"])
    for y in range(2006, 2026):
        writer.writerow([y, f"{share:.1f}" if y == year else ""])
    return out.getvalue()


def main() -> None:
    with urlopen(Request(URL, headers={
        "User-Agent": "worldreports-moldova-bns-census-audit/1.0",
        "Accept": "text/html"}), timeout=45) as response:
        if response.status != 200 or "html" not in response.headers.get(
                "Content-Type", "").lower():
            raise ValueError("BNS census publication not served as HTML")
        content = response.read(3_000_001)
    year, share = parse_official_page(content)
    digest = hashlib.sha256(content).hexdigest()
    OUTPUT.write_text(review_csv(year, share, digest), encoding="utf-8")
    print(f"BNS census {year} foreign-born {share:.1f}%; original HTML SHA256 {digest}")
    print(f"Review-only sidecar: {OUTPUT}")


if __name__ == "__main__":
    main()
