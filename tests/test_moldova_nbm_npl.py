"""Original NBM bank-wide prudential NPL year-end, not household-only credit."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent / "countries/moldova"


def test_official_year_end_rates_and_missing_years():
    raw = (ROOT / "data/credit/prudential_npl.csv").read_text("utf-8")
    rows = list(csv.DictReader(s for s in raw.splitlines() if s and not s.startswith("#")))
    assert list(rows[0]) == ["year", "release_2022_2023_pct",
                             "release_2024_2025_pct"]
    assert [int(row["year"]) for row in rows] == list(range(2006, 2026))
    early = {int(r["year"]): float(r["release_2022_2023_pct"])
             for r in rows if r["release_2022_2023_pct"]}
    late = {int(r["year"]): float(r["release_2024_2025_pct"])
            for r in rows if r["release_2024_2025_pct"]}
    assert early == {2022: 6.4, 2023: 5.6}
    assert late == {2024: 4.1, 2025: 4.1}
    assert not set(early) & set(late)
    assert "NOT household-only" in raw and "NOT IFRS" in raw
    for url in ("bnm.md/en/content/financial-situation-banking-sector-year-2022",
                "bnm.md/ru/node/66762",
                "bnm.md/en/content/financial-situation-banking-sector-2024",
                "bnm.md/ro/node/69800"):
        assert url in raw
    assert "1.4 pp" in raw and "1.5 pp" in raw


def test_npl_manifest_and_visual_scope_contract():
    src = yaml.safe_load((ROOT / "SOURCES.yaml").read_text("utf-8"))
    entry = src["credit"]["prudential_npl.csv"]
    assert entry["official"] is True
    assert "National Bank of Moldova" in entry["source"]
    assert "all" in entry["notes"].lower()
    assert "1.4 pp" in entry["notes"] and "1.5 pp" in entry["notes"]
    chart = (ROOT / "plates.py").read_text("utf-8")
    credit = chart.split("def plate_credit(", 1)[1].split("def plate_people(", 1)[0]
    for part in ('ig.slot("credit.npl"', '"credit/prudential_npl.csv"',
                 "release_2022_2023_pct", "release_2024_2025_pct",
                 "NOT household", '"credit/private_credit.csv"'):
        assert part in credit
    assert credit.count("_pending(ctx, ig, ax,") == 2


def test_ro_en_pt_npl_coverage_without_english_fallback():
    labels = json.loads((ROOT / "i18n.json").read_text("utf-8"))
    for caption in ("Bank-wide prudential non-performing loans (%)",
                    "NBM 2022–23 year-end reports",
                    "NBM 2024–25 year-end reports",
                    "NBM prudential bank-wide NPL; NOT household; release seam"):
        assert set(labels[caption]) == {"ro", "pt"}
        for lang in ("ro", "pt"):
            assert labels[caption][lang] != caption
            assert labels[caption][lang]
    ui = json.loads((ROOT / "ui.json").read_text("utf-8"))
    for lang in ("ro", "en", "pt"):
        assert any("2022" in x and "2025" in x and "2023" in x
                   for x in ui[lang]["notes"])
        assert any("2022" in x["detail"] and "2025" in x["detail"]
                   for x in ui[lang]["unavailable"])
