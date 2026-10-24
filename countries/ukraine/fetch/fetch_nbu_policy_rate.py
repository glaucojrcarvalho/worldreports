#!/usr/bin/env python3
"""Review-only rebuild of Ukraine's 2006–2025 year-end NBU policy rate.

Computing publisher: National Bank of Ukraine, official historical decision
table https://bank.gov.ua/en/monetary/archive-rish

The archive is an EFFECTIVE-DATE event log, not an annual observation table.
For each calendar 31 December, select the last effective rate on or before
that date; a year with NO decision (2011) inherits the active 2010 rate.
That is a legitimate interest-rate step-function rule, not interpolation
of an unobserved survey. Do not confuse year-end rates with calendar-year
averages, especially when comparing with annual-average CPI.

Never replace the curated policy_rate.csv in-place. Only writes the staged
policy_rate_from_nbu.csv for human comparison.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from io import StringIO
import csv
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "markets" / "policy_rate_from_nbu.csv"
URL = "https://bank.gov.ua/en/monetary/archive-rish"
FIRST, LAST = 2006, 2025
ANCHORS = {
    2006: Decimal("8.50"),
    2010: Decimal("7.75"),
    2011: Decimal("7.75"),  # no 2011 policy change
    2015: Decimal("22.00"),
    2022: Decimal("25.00"),
    2023: Decimal("15.00"),
    2024: Decimal("13.50"),
    2025: Decimal("15.50"),
}
MAX_BYTES = 2_000_000


class NBUArchiveHTML(HTMLParser):
    """Extract the first HTML table as rows of visible cell text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active_table = False
        self.finished_table = False
        self.row = None
        self.cell = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "table" and not self.finished_table and not self.active_table:
            self.active_table = True
        elif self.active_table and tag == "tr":
            self.row = []
        elif self.active_table and tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if not self.active_table:
            return
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.active_table = False
            self.finished_table = True


def download() -> str:
    req = urllib.request.Request(URL, headers={
        "Accept": "text/html",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        mime = response.headers.get("Content-Type", "").lower()
        status = response.status
        raw = response.read(MAX_BYTES + 1)
    if status != 200 or not raw or len(raw) > MAX_BYTES or "html" not in mime:
        raise ValueError("NBU key rate archive did not return bounded HTML")
    return raw.decode("utf-8-sig")


def parse_events(html: str) -> list[tuple[date, Decimal]]:
    parser = NBUArchiveHTML()
    parser.feed(html)
    if not parser.finished_table:
        raise ValueError("NBU key-rate HTML table absent")
    events = []
    year = None
    seen = set()
    for row in parser.rows:
        # Publisher year header rows have no interest-rate cell.
        if len(row) == 1 and re.fullmatch(r"(19|20)\d{2}", row[0]):
            year = int(row[0])
            continue
        if len(row) < 2 or year is None:
            continue
        m = re.fullmatch(r"from\s+(\d{1,2})\.(\d{2})", row[0], re.I)
        if not m:
            continue
        try:
            effective = date(year, int(m.group(2)), int(m.group(1)))
            rate = Decimal(row[1].replace(",", "."))
        except (ValueError, TypeError, InvalidOperation) as exc:
            raise ValueError(f"Invalid NBU rate decision {year}: {row}") from exc
        if effective in seen:
            raise ValueError(f"Duplicate NBU effective date {effective}")
        if not rate.is_finite() or rate <= 0 or rate > Decimal(500):
            raise ValueError(f"Invalid NBU policy rate on {effective}")
        seen.add(effective)
        events.append((effective, rate))
    if len(events) < 80 or not any(y.year <= 2006 for y, _ in events):
        raise ValueError("NBU archive decisions are incomplete or wrong table")
    return sorted(events)


def annual_year_end(events: list[tuple[date, Decimal]]) -> list[dict[str,str]]:
    if sorted({d for d,_ in events}) != [d for d,_ in events]:
        raise ValueError("NBU events must be date-sorted and unique")
    out = []
    last_active = None
    for year in range(FIRST, LAST + 1):
        for effective, rate in events:
            if effective <= date(year, 12, 31):
                last_active = (effective, rate)
            else:
                break
        if last_active is None:
            raise ValueError(f"No policy rate in effect for {year}")
        effective, rate = last_active
        if year in ANCHORS and rate != ANCHORS[year]:
            raise ValueError(f"NBU {year} source rate was revised: {rate}")
        out.append({
            "year": str(year),
            "policy_rate_eoy_pct": f"{rate:.2f}",
            "last_change_date": effective.isoformat(),
        })
    return out


def to_csv(rows: list[dict[str,str]]) -> str:
    buf = StringIO()
    writer = csv.DictWriter(
        buf, ("year", "policy_rate_eoy_pct", "last_change_date"),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def main() -> None:
    staged = to_csv(annual_year_end(parse_events(download())))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(staged, encoding="utf-8")
    tmp.replace(OUTPUT)
    print("Staged 20 year-end NBU policy rates: 2006–2025")
    print(f"Review sidecar only: {OUTPUT}")


if __name__ == "__main__":
    main()
