"""Offline source and curated checks for official NBU year-end reserves."""
from __future__ import annotations

import csv
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("ukraine_reserves", ROOT / "fetch" / "fetch_nbu_reserves.py")
nbu = module_from_spec(spec)
spec.loader.exec_module(nbu)

SNAPSHOT = ROOT / "data" / "macro" / "reserves.csv"
VERIFIED_USD_MN = {
    2006: "22358.10", 2007: "32479.06", 2008: "31543.20",
    2009: "26505.11", 2010: "34576.40", 2011: "31794.61",
    2012: "24546.19", 2013: "20415.71", 2014: "7533.33",
    2015: "13299.99", 2016: "15539.33", 2017: "18808.45",
    2018: "20820.43", 2019: "25302.16", 2020: "29132.89",
    2021: "30940.95", 2022: "28494.46", 2023: "40514.43",
    2024: "43795.35", 2025: "57302.41",
}


def fixture(year=2024, **change):
    dt = f"{year + 1}0101"
    rows = [
        {"dt": dt, "txten": "Official reserve assets",
         "id_api": "RES_OffReserveAssets", "leveli": 1,
         "tzep": "T071USD_7", "freq": "M", "value": float(VERIFIED_USD_MN[year])},
        {"dt": dt, "txten": "Foreign currency reserves",
         "id_api": "RES_ForCurrencyAssets", "leveli": 2,
         "tzep": "T071USD_7", "freq": "M", "value": 37000.0},
    ]
    rows[0].update(change)
    return json.dumps(rows).encode("utf-8")


class NBUReserveTests(unittest.TestCase):
    def test_labeled_first_of_next_month_not_december_first(self):
        self.assertEqual(nbu.snapshot_date(2024), "20250101")
        self.assertEqual(nbu.source_url(2024),
                         "https://bank.gov.ua/NBUStatService/v1/statdirectory/res?date=20250101&json")
        self.assertEqual(nbu.snapshot_date(2006), "20070101")
        with self.assertRaises(ValueError):
            nbu.snapshot_date(2026)

    def test_extracts_2024_official_total_not_component_as_billion(self):
        item = nbu.parse_annual_record(2024, fixture())
        self.assertEqual(item, {"year": "2024", "usd_bn": "43.79535",
                                "source_snapshot_dt": "20250101"})

    def test_next_january_2026_is_year_end_2025(self):
        row = nbu.parse_annual_record(2025, fixture(2025))
        self.assertEqual(row["usd_bn"], "57.30241")
        self.assertEqual(row["source_snapshot_dt"], "20260101")

    def test_off_by_one_december_observation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "date changed"):
            nbu.parse_annual_record(2024, fixture(dt="20241201"))

    def test_unit_frequency_and_total_identity_cannot_drift(self):
        bad = [
            {"tzep": "T071UAH_7"}, {"freq": "Y"},
            {"id_api": "RES_ForCurrencyAssets"},
            {"leveli": 2}, {"txten": "Net international reserves"},
            {"value": -5}, {"value": None}, {"value": "NaN"},
            {"value": 43700.25},
        ]
        for case in bad:
            with self.subTest(case=case), self.assertRaises(ValueError):
                nbu.parse_annual_record(2024, fixture(**case))

    def test_non_json_or_html_error_fails_closed(self):
        with self.assertRaises(ValueError):
            nbu.parse_annual_record(2024, b"<html>403 forbidden</html>")
        with self.assertRaises(ValueError):
            nbu.parse_annual_record(2024, b"{}")

    def test_all_curated_years_have_full_dates_and_source_unit(self):
        with SNAPSHOT.open(encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            self.assertEqual(rd.fieldnames,
                ["year", "usd_bn", "source_snapshot_dt"])
            rows = list(rd)
        self.assertEqual(len(rows), 20)
        self.assertEqual([int(x["year"]) for x in rows],
                         list(range(2006, 2026)))
        for row in rows:
            y = int(row["year"])
            self.assertEqual(row["source_snapshot_dt"], f"{y + 1}0101")
            self.assertEqual(Decimal(row["usd_bn"]) * 1000,
                             Decimal(VERIFIED_USD_MN[y]))

    def test_render_refuses_missing_years_not_zero_filled(self):
        rows = [nbu.parse_annual_record(y, fixture(y)) for y in range(2006, 2026)]
        self.assertEqual(nbu.render(rows), SNAPSHOT.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            nbu.render(rows[:-1])


if __name__ == "__main__":
    unittest.main()
