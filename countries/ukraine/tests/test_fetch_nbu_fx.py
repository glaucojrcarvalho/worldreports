"""Deterministic tests for daily NBU FX to annual review-only staging."""
from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import json
import unittest
from urllib.parse import urlparse, parse_qs

SOURCE = Path(__file__).resolve().parents[1] / "fetch" / "fetch_nbu_fx.py"
spec = importlib.util.spec_from_file_location("ukraine_nbu_fx", SOURCE)
fx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fx)


def year_rows(year: int, *, units: int = 1, per_one: float = 8.0):
    first, last = date(year, 1, 1), date(year, 12, 31)
    rows = []
    for i in range((last - first).days + 1):
        d = first + timedelta(days=i)
        normalized = per_one
        if d.isoformat() in fx.ANCHORS:
            normalized = float(fx.ANCHORS[d.isoformat()])
        rows.append({
            "exchangedate": d.strftime("%d.%m.%Y"), "r030": 840, "cc": "USD",
            "rate": normalized * units, "units": units,
            "rate_per_unit": normalized,
        })
    return rows


def payload(year, **kwargs):
    return json.dumps(year_rows(year, **kwargs)).encode("utf-8")


class NBUFxTests(unittest.TestCase):
    def test_nbu_archive_year_and_currency_query(self):
        u = fx.make_url(2006)
        self.assertIn("start=20060101", u)
        self.assertIn("end=20061231", u)
        self.assertIn("valcode=usd", u)
        with self.assertRaises(ValueError):
            fx.make_url(2026)

    def test_2006_quote_for_one_hundred_usd(self):
        rows = fx.read_daily_rates(payload(2006, units=100, per_one=5.05), 2006)
        self.assertEqual(rows[date(2006, 1, 1)], Decimal("5.05"))
        self.assertEqual(len(rows), 365)
        self.assertEqual(fx.annual_average(rows), Decimal("5.05"))

    def test_leap_year_has_366_daily_values(self):
        rows = fx.read_daily_rates(payload(2008), 2008)
        self.assertEqual(len(rows), 366)
        self.assertIn(date(2008, 2, 29), rows)

    def test_known_2014_and_2022_values(self):
        r14 = fx.read_daily_rates(payload(2014, units=100, per_one=7.993), 2014)
        self.assertEqual(r14[date(2014, 1, 1)], Decimal("7.993"))
        r22 = fx.read_daily_rates(payload(2022, per_one=27.2782), 2022)
        self.assertEqual(r22[date(2022, 1, 4)], Decimal("27.2782"))

    def test_rejects_missing_day_no_interpolation(self):
        rows = year_rows(2019)
        del rows[22]
        with self.assertRaisesRegex(ValueError, "incomplete daily"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2019)

    def test_rejects_duplicate_days(self):
        rows = year_rows(2019)
        rows.append(dict(rows[1]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2019)

    def test_rejects_incorrect_quote_units(self):
        rows = year_rows(2006, units=100, per_one=5.05)
        rows[0]["rate_per_unit"] = 505.0
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2006)

    def test_rejects_official_known_value_mismatch(self):
        rows = year_rows(2022, per_one=27.2782)
        rows[3]["rate"] = 20
        rows[3]["rate_per_unit"] = 20
        with self.assertRaisesRegex(ValueError, "official reference"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2022)

    def test_rejects_wrong_currency_and_date(self):
        rows = year_rows(2016)
        rows[7]["cc"] = "EUR"
        with self.assertRaisesRegex(ValueError, "wrong currency"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2016)
        rows = year_rows(2016)
        rows[7]["exchangedate"] = "08.01.2017"
        with self.assertRaisesRegex(ValueError, "off-year"):
            fx.read_daily_rates(json.dumps(rows).encode("utf-8"), 2016)

    def test_only_complete_verified_years_are_staged(self):
        def fake_fetch(url: str) -> bytes:
            year = int(parse_qs(urlparse(url).query)["start"][0][:4])
            return payload(year, units=100 if year == 2006 else 1, per_one=5.05 if year == 2006 else 8.0)
        out = fx.stage_all(range(2006, 2008), fetch=fake_fetch)
        self.assertIn("2006,5.05000000,365", out)
        self.assertIn("2007,8.00000000,365", out)
        self.assertEqual(len(out.splitlines()), 3)

    def test_no_sidecar_on_error(self):
        def fail_later(url: str) -> bytes:
            year = int(parse_qs(urlparse(url).query)["start"][0][:4])
            if year == 2007:
                return b"[]"
            return payload(year, units=100, per_one=5.05)
        with self.assertRaises(ValueError):
            fx.stage_all(range(2006, 2008), fetch=fail_later)


if __name__ == "__main__":
    unittest.main()
