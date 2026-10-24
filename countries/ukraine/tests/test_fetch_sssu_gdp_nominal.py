"""Offline contract and semantic tests for nominal SSSU GDP 2010–2024."""
from __future__ import annotations

import csv
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

COUNTRY = Path(__file__).resolve().parents[1]
SCRIPT = COUNTRY / "fetch" / "fetch_sssu_gdp_nominal.py"
spec = spec_from_file_location("ukr_nominal_gdp", SCRIPT)
source = module_from_spec(spec)
spec.loader.exec_module(source)
CURATED = COUNTRY / "data" / "macro" / "gdp_nominal.csv"

VALUES = {
    2010: 1079346, 2011: 1299991, 2012: 1404669, 2013: 1465198,
    2014: 1586915, 2015: 1988544, 2016: 2385367, 2017: 2981227,
    2018: 3560302, 2019: 3977198, 2020: 4222026, 2021: 5450849,
    2022: 5239114, 2023: 6627961, 2024: 7662376,
}


def fixture(modify=None, drop=None):
    fields = ["STRUCTURE_ID", "ACTION", *source.DIMENSIONS,
              "TIME_PERIOD", "OBS_VALUE", "UNITS_OF_MEASURE", "SCALE",
              "OBS_FLAG", "TERRITORIAL_COVERAGE"]
    out = StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for y, value in VALUES.items():
        if y == drop:
            continue
        row = {
            "STRUCTURE_ID": source.STRUCTURE,
            "ACTION": "R",
            **source.DIMENSIONS,
            "TIME_PERIOD": str(y),
            "OBS_VALUE": str(value),
            "UNITS_OF_MEASURE": "1090",
            "SCALE": "6",
            "OBS_FLAG": "",
            "TERRITORIAL_COVERAGE": "Ukraine",
        }
        if y == 2024 and modify:
            row.update(modify)
        w.writerow(row)
    return out.getvalue().encode()


class NominalGDPTests(unittest.TestCase):
    def test_exact_publisher_series_dimensions(self):
        url = source.source_url()
        self.assertIn("DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0", url)
        self.assertIn("CURR_PRICES", url)
        self.assertIn("UA00000000000000000", url)

    def test_extract_15_full_year_observations(self):
        rows = source.parse_nominal_gdp(fixture())
        self.assertEqual(len(rows), 15)
        self.assertEqual(rows[0], {"year": "2010", "nominal_uah_mn": "1079346"})
        self.assertEqual(rows[-1], {"year": "2024", "nominal_uah_mn": "7662376"})
        self.assertNotIn("2025", [row["year"] for row in rows])

    def test_reject_wrong_unit_precision_dimension_and_scope(self):
        for change in (
            {"SCALE": "0"},
            {"UNITS_OF_MEASURE": "1010"},
            {"PRICE_TYPE": "IDX_VOL_PY"},
            {"SECTOR_ECONOMY": "S_11"},
            {"REGION": "OTHER"},
            {"OBS_VALUE": "7662376.12"},
            {"OBS_VALUE": "7662377"},
            {"OBS_FLAG": "M"},
            {"TERRITORIAL_COVERAGE": "Other"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                source.parse_nominal_gdp(fixture(change))

    def test_missing_anchor_must_fail_not_zero_fill(self):
        with self.assertRaisesRegex(ValueError, "missing anchors"):
            source.parse_nominal_gdp(fixture(drop=2024))

    def test_a_non_anchor_gap_remains_missing(self):
        rows = source.parse_nominal_gdp(fixture(drop=2017))
        self.assertNotIn("2017", [row["year"] for row in rows])

    def test_checked_curated_csv_matches_same_vintage(self):
        with CURATED.open(encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            self.assertEqual(rd.fieldnames, ["year", "nominal_uah_mn"])
            entries = list(rd)
        self.assertEqual(len(entries), len(VALUES))
        for row in entries:
            self.assertEqual(Decimal(row["nominal_uah_mn"]), VALUES[int(row["year"])])
        self.assertEqual([int(x["year"]) for x in entries], list(range(2010, 2025)))

    def test_csv_sidecar_content_matches_curated_snapshot(self):
        from_api = source.to_csv(source.parse_nominal_gdp(fixture()))
        self.assertEqual(from_api, CURATED.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
