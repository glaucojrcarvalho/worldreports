"""Offline data-shape and missingness tests for WDI review-only sidecars."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "fetch" / "fetch_worldbank.py"
spec = importlib.util.spec_from_file_location("ukraine_worldbank_fetch", SOURCE)
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


def sample(code: str, value=2.3):
    rows = [
        {"indicator": {"id": code}, "countryiso3code": "UKR", "date": str(y),
         "value": value if y != 2022 else None}
        for y in range(2006, 2026)
    ]
    return [{"pages": 1, "per_page": 100, "total": 20}, rows]


class WDIStageTests(unittest.TestCase):
    def test_url_scoped_to_ukraine_indicator_and_years(self):
        u = fetcher.indicator_url("NY.GDP.MKTP.KD.ZG")
        self.assertIn("/country/UKR/", u)
        self.assertIn("date=2006%3A2025", u)
        with self.assertRaises(ValueError):
            fetcher.indicator_url("made-up")

    def test_parse_preserves_missing_year_as_none(self):
        got = fetcher.parse_series(sample("NY.GDP.MKTP.KD.ZG"), "NY.GDP.MKTP.KD.ZG")
        self.assertIsNone(got[2022])
        self.assertEqual(got[2021], 2.3)

    def test_rejects_wrong_country_code_year_and_pagination(self):
        s = sample("NY.GDP.MKTP.KD.ZG")
        s[0]["pages"] = 2
        with self.assertRaisesRegex(ValueError, "pagination"):
            fetcher.parse_series(s, "NY.GDP.MKTP.KD.ZG")
        for edit, phrase in [
            (("countryiso3code", "RUS"), "country"),
            (("date", "2026"), "outside"),
            (("indicator", {"id": "SP.POP.TOTL"}), "indicator"),
        ]:
            bad = sample("NY.GDP.MKTP.KD.ZG")
            bad[1][0][edit[0]] = edit[1]
            with self.subTest(edit=edit), self.assertRaisesRegex(ValueError, phrase):
                fetcher.parse_series(bad, "NY.GDP.MKTP.KD.ZG")

    def test_rejects_duplicates_and_short_lists(self):
        bad = sample("NY.GDP.MKTP.KD.ZG")
        bad[1].append(dict(bad[1][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            fetcher.parse_series(bad, "NY.GDP.MKTP.KD.ZG")
        bad = sample("NY.GDP.MKTP.KD.ZG")
        bad[1] = bad[1][:2]
        with self.assertRaisesRegex(ValueError, "short"):
            fetcher.parse_series(bad, "NY.GDP.MKTP.KD.ZG")

    def test_sidecar_contains_empty_not_zero_for_missing(self):
        from io import StringIO
        import csv
        series = {name: {2021: 1.0, 2022: None, 2023: 2.0}
                  for name in fetcher.INDICATORS}
        table = list(csv.DictReader(StringIO(fetcher.to_csv_text(series))))
        row22 = next(r for r in table if r["year"] == "2022")
        self.assertTrue(all(row22[name] == "" for name in fetcher.INDICATORS))
        self.assertEqual(len(table), fetcher.LAST - fetcher.FIRST + 1)


if __name__ == "__main__":
    unittest.main()
