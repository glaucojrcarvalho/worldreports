"""Semantic tests for the reviewed national GDP growth CSV (2011–2024)."""
from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
import unittest

COUNTRY = Path(__file__).resolve().parents[1]
DATA = COUNTRY / "data" / "macro" / "gdp_growth.csv"
SOURCE_MANIFEST = COUNTRY / "SOURCES.yaml"

# One SSSU SDMX response/vintage; keep cross-year scope caveats in SOURCES.
VERIFIED_INDEX = {
    2011: "105.5", 2012: "100.2", 2013: "100.0", 2014: "93.4",
    2015: "90.2", 2016: "102.4", 2017: "102.4", 2018: "103.5",
    2019: "103.2", 2020: "96.2", 2021: "103.4", 2022: "71.2",
    2023: "105.5", 2024: "103.2",
}


def dataset():
    with DATA.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["year", "real_growth", "volume_index_py"]:
            raise ValueError("Unexpected accepted GDP CSV schema")
        return list(reader)


class CuratedGDPTests(unittest.TestCase):
    def test_single_verified_vintage_and_no_invented_years(self):
        rows = dataset()
        self.assertEqual([int(r["year"]) for r in rows], list(range(2011, 2025)))
        self.assertEqual(len(rows), 14)
        self.assertNotIn("2025", [r["year"] for r in rows])

    def test_exact_source_volume_indices(self):
        for row in dataset():
            year = int(row["year"])
            with self.subTest(year=year):
                self.assertEqual(Decimal(row["volume_index_py"]),
                                 Decimal(VERIFIED_INDEX[year]))

    def test_growth_is_volume_index_minus_100(self):
        for row in dataset():
            with self.subTest(year=row["year"]):
                self.assertEqual(Decimal(row["real_growth"]),
                                 Decimal(row["volume_index_py"]) - 100)

    def test_wartime_contraction_and_other_anchor_years(self):
        rows = {int(r["year"]): Decimal(r["real_growth"]) for r in dataset()}
        self.assertEqual(rows[2014], Decimal("-6.6"))
        self.assertEqual(rows[2015], Decimal("-9.8"))
        self.assertEqual(rows[2022], Decimal("-28.8"))
        self.assertEqual(rows[2023], Decimal("5.5"))
        self.assertEqual(rows[2024], Decimal("3.2"))

    def test_dataset_exceeds_current_shared_spine_and_requires_review(self):
        actual = min(Decimal(r["real_growth"]) for r in dataset())
        self.assertLess(actual, Decimal("-18"))

    def test_source_manifest_discloses_exact_vintage_and_territorial_scope(self):
        manifest = SOURCE_MANIFEST.read_text(encoding="utf-8")
        self.assertIn("gdp_growth.csv:", manifest)
        self.assertIn("DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)", manifest)
        self.assertIn("BREAKDOWN_CATEGORY=_T", manifest)
        self.assertIn("2011-2024", manifest)
        self.assertIn("occupied Crimea", manifest)
        self.assertIn("NO 2025 observation", manifest)


if __name__ == "__main__":
    unittest.main()
