"""Guarded live audit of official NBM year-end bank-wide prudential NPL.

Each annual report is an independent publisher edition; do not interpolate
years, splice year-over-year reported changes, or overwrite curated data.
The four original ratios are bank-wide (not household and not IFRS NPL).
"""
from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data/credit/prudential_npl_from_nbm.csv"
EVIDENCE = ROOT / "data/credit/prudential_npl_source_evidence.json"

PAGES = {
    2022: "https://bnm.md/en/content/financial-situation-banking-sector-year-2022",
    2023: "https://bnm.md/ru/node/66762",
    2024: "https://bnm.md/en/content/financial-situation-banking-sector-2024",
    2025: "https://bnm.md/ro/node/69800",
}
EXPECTED = {2022: 6.4, 2023: 5.6, 2024: 4.1, 2025: 4.1}
MAX_BYTES = 2_500_000


class _VisibleHTML(HTMLParser):
    """Extract human-readable article prose; ignore scripts and styles."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.text_parts.append(data)


def visible_text(raw: bytes) -> str:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Empty or oversized NBM HTML body")
    html = raw.decode("utf-8-sig")
    parser = _VisibleHTML()
    parser.feed(html)
    return " ".join(" ".join(parser.text_parts).replace("\u00a0", " ").split())


def extract_npl(text: str, year: int) -> float:
    """Return a *single* December 31 prudential bank-wide NPL ratio."""
    if year not in EXPECTED:
        raise ValueError("Year is not among reviewed NBM releases")
    # 2022/23 wording: 'accounting for 6.4% on 31.12.2022'.
    # 2024 wording: 'accounting for 4,1% as of 31 December 2024'.
    # 2025 wording: 'as of 31 December 2025, was 4.1%'.
    pattern = re.compile(
        r"share\s+of\s+non-performing\s+loans\b.{0,520}?"
        r"(?:accounting\s+for|was)\s*(\d{1,2}[.,]\d)\s*%",
        re.IGNORECASE | re.DOTALL,
    )
    hits: list[tuple[str, float]] = []
    date = re.compile(
        r"(?:31\.12\." + str(year) + r"|31\s+December\s+" + str(year)
        + r"|December\s+31[,]?\s+" + str(year) + r")",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        segment = text[match.start():match.end() + 100]
        if date.search(segment):
            hits.append((segment, float(match.group(1).replace(",", "."))))
    if len(hits) != 1:
        raise ValueError(f"NBM {year}: expected one dated prudential NPL ratio, got {len(hits)}")
    value = hits[0][1]
    if not 0 < value <= 20:
        raise ValueError(f"NBM {year}: invalid NPL percent {value}")
    if value != EXPECTED[year]:
        raise ValueError(f"NBM {year}: publisher changed ratio to {value}; review before curating")
    return value


def _download(url: str) -> bytes:
    if not url.startswith("https://bnm.md/"):
        raise ValueError("NBM request outside approved publisher host")
    req = Request(url, headers={"User-Agent": "WorldReportsSourceAudit/1.0 (attributed research)"})
    with urlopen(req, timeout=40) as response:
        if response.status != 200:
            raise ValueError(f"NBM HTTP status {response.status}")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("NBM response exceeds maximum source size")
    return raw


def render_review(values: dict[int, float]) -> str:
    if values != EXPECTED:
        raise ValueError("Unreviewed NBM source change")
    stream = io.StringIO()
    stream.write("# Original NBM prudential NPL / all bank loans, December 31, source-verified.\n")
    stream.write("# Review sidecar ONLY: no replacement of curated CSV.\n")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["year", "release_2022_2023_pct", "release_2024_2025_pct"])
    for year in range(2006, 2026):
        writer.writerow([
            year,
            f"{values[year]:.1f}" if year in (2022, 2023) else "",
            f"{values[year]:.1f}" if year in (2024, 2025) else "",
        ])
    return stream.getvalue()


def main() -> None:
    results: dict[int, float] = {}
    evidence: list[dict[str, object]] = []
    for year, url in PAGES.items():
        raw = _download(url)
        results[year] = extract_npl(visible_text(raw), year)
        evidence.append({"year": year, "publisher_url": url,
                         "publisher_html_sha256": hashlib.sha256(raw).hexdigest(),
                         "prudential_npl_pct": results[year]})
        print(f"NBM {year}-12-31 bank-wide prudential NPL: {results[year]:.1f}%")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_review(results), encoding="utf-8")
    EVIDENCE.write_text(json.dumps({
        "publisher": "National Bank of Moldova",
        "scope": "all prudential bank loans, year-end",
        "source_release_evidence": evidence,
        "output": OUTPUT.name,
        "canonical_file_modified": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Official source audit passed; review sidecar only.")


if __name__ == "__main__":
    main()
