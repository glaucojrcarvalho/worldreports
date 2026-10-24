"""Offline semantic assertions for the accepted 2006–2025 NBU FX CSV.

These check publisher-documented spot normalization indirectly via the
independent NBU API extractor tests; published annual values are pinned.
"""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "data" / "markets" / "fx.csv"
FIRST_YEAR, LAST_YEAR = 2006, 2025
YEAR_ANCHORS = {
    2006: Decimal("5.05000000"),
    2014: Decimal("11.90953827"),
    2022: Decimal("32.36835123"),
    2025: Decimal("41.69015205"),
}


def read_dataset():
    with FILE.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    if not records:
        raise ValueError("Empty curated NBU FX data")
    expected = {"year", "avg_uah_per_usd", "daily_observations"}
    if set(records[0]) != expected:
        raise ValueError(f"Unexpected curated FX columns: {list(records[0])}")
    return {int(row["year"]): row for row in records}


class CuratedFxTests(unittest.TestCase):
    def test_years_are_complete_and_unique(self):
        with FILE.open(encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        self.assertEqual(len(records), 20)
        self.assertEqual(len({int(r["year"]) for r in records}), 20)
        self.assertEqual(set(map(int, (r["year"] for r in records))),
                         set(range(FIRST_YEAR, LAST_YEAR + 1)))

    def test_every_year_has_full_daily_observation_count(self):
        for year, row in read_dataset().items():
            expected = (date(year + 1, 1, 1) - date(year, 1, 1)).days
            self.assertEqual(int(row["daily_observations"]), expected, year)
            self.assertGreater(Decimal(row["avg_uah_per_usd"]), 0)

    def test_annual_values_are_pinned_to_checked_nbu_archive(self):
        rows = read_dataset()
        for year, expected in YEAR_ANCHORS.items():
            with self.subTest(year=year):
                self.assertEqual(Decimal(rows[year]["avg_uah_per_usd"]), expected)

    def test_2006_base_year_for_spine_fx_index(self):
        rows = read_dataset()
        base = Decimal(rows[2006]["avg_uah_per_usd"])
        self.assertEqual(base, Decimal("5.05000000"))
        self.assertEqual(base / base * 100, 100)
        # A rising UAH-per-USD rate means a WEAKER hryvnia, so index falls.
        idx_2022 = base / Decimal(rows[2022]["avg_uah_per_usd"]) * 100
        self.assertLess(idx_2022, 100)

    def test_not_mistaken_for_stock_or_partial_current_year(self):
        rows = read_dataset()
        self.assertNotIn(2026, rows)
        self.assertTrue(all(int(y) <= LAST_YEAR for y in rows))


if __name__ == "__main__":
    unittest.main()
