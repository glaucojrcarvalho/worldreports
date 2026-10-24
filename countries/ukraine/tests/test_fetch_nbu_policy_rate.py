"""Fail-closed tests of the official NBU effective-date policy rate archive."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import csv
from io import StringIO
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("ukraine_nbu_policy", ROOT / "fetch" / "fetch_nbu_policy_rate.py")
policy = module_from_spec(SPEC)
SPEC.loader.exec_module(policy)

ANNUAL = {
    2006: "8.50", 2007: "8.00", 2008: "12.00", 2009: "10.25",
    2010: "7.75", 2011: "7.75", 2012: "7.50", 2013: "6.50",
    2014: "14.00", 2015: "22.00", 2016: "14.00", 2017: "14.50",
    2018: "18.00", 2019: "13.50", 2020: "6.00", 2021: "9.00",
    2022: "25.00", 2023: "15.00", 2024: "13.50", 2025: "15.50",
}


def mock_html() -> str:
    # Test parser with enough independent change points to satisfy the
    # archive completeness gate. This is synthetic *parser input*, not
    # a substitute for any curated observation or publisher history.
    rows = ["<table><tr><th>Period</th><th>Rate</th></tr>"]
    for year in range(2026, 2004, -1):
        if year == 2011:
            continue  # official archive shows no decisions in 2011
        rows.append(f"<tr><th><p><strong>{year}</strong></p></th></tr>")
        for month in (12, 10, 8, 6, 3):
            value = ANNUAL.get(year, "8.50").replace(".", ",")
            rows.append(
                f"<tr><td><p>from 01.{month:02d}</p></td>"
                f"<td>{value}</td><td>Decisions</td></tr>"
            )
    rows.append("</table>")
    return "\n".join(rows)


class NBUPolicyRateTests(unittest.TestCase):
    def test_official_archive_is_change_points_not_one_row_per_year(self):
        history = policy.parse_events(mock_html())
        self.assertGreaterEqual(len(history), 90)
        self.assertEqual(history, sorted(history))
        self.assertNotIn(2011, [dt.year for dt, _ in history])

    def test_explicit_year_end_rule_carries_forward_rate_with_no_decision(self):
        annual = policy.annual_year_end(policy.parse_events(mock_html()))
        self.assertEqual(len(annual), 20)
        by_year = {int(row["year"]): row for row in annual}
        self.assertEqual(by_year[2011]["policy_rate_eoy_pct"], "7.75")
        self.assertTrue(by_year[2011]["last_change_date"].startswith("2010-"))
        self.assertEqual(by_year[2022]["policy_rate_eoy_pct"], "25.00")
        self.assertEqual(by_year[2025]["policy_rate_eoy_pct"], "15.50")
        self.assertNotIn(2026, by_year)

    def test_wrong_rate_anchor_fails_closed(self):
        history = policy.parse_events(mock_html())
        changed = [(dt, Decimal("24.00") if dt.year == 2022 else rate)
                   for dt, rate in history]
        with self.assertRaisesRegex(ValueError, "2022"):
            policy.annual_year_end(changed)

    def test_duplicate_change_date_is_rejected(self):
        html = mock_html().replace(
            "<tr><td><p>from 01.12</p></td>",
            "<tr><td><p>from 01.03</p></td>", 1
        )
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            policy.parse_events(html)

    def test_html_error_is_not_interpreted_as_interest_rate_data(self):
        with self.assertRaisesRegex(ValueError, "table absent"):
            policy.parse_events("<html><h1>Access denied</h1></html>")

    def test_curated_annual_snapshot_has_observed_rates_and_2011_seam(self):
        with (ROOT / "data" / "markets" / "policy_rate.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames,
                             ["year", "policy_rate_eoy_pct", "last_change_date"])
            rows = list(reader)
        self.assertEqual([int(r["year"]) for r in rows], list(range(2006, 2026)))
        for row in rows:
            self.assertEqual(Decimal(row["policy_rate_eoy_pct"]),
                             Decimal(ANNUAL[int(row["year"])]))
        p = {int(row["year"]): row for row in rows}
        self.assertEqual(p[2011]["last_change_date"], "2010-08-10")
        self.assertEqual(p[2025]["last_change_date"], "2025-12-12")

    def test_correct_output_csv_has_explicit_rate_unit_and_source_date(self):
        historical = policy.parse_events(mock_html())
        csv_data = policy.to_csv(policy.annual_year_end(historical))
        self.assertTrue(csv_data.startswith("year,policy_rate_eoy_pct,last_change_date\n"))
        self.assertEqual(len(list(csv.DictReader(StringIO(csv_data)))), 20)


if __name__ == "__main__":
    unittest.main()
