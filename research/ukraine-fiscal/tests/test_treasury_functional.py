"""Offline contracts for the NBU/Treasury functional spending research parser."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "probe_treasury_functional.py"
spec = importlib.util.spec_from_file_location("treasury_probe", P)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def sample(*, incorrect=None, exclude=None, duplicate=None):
    """Synthetic publisher-shape rows; only 2024 anchors are authentic."""
    rows = []
    for year in range(probe.START, probe.END + 1):
        for code in [*probe.FUNCTIONS, probe.TOTAL]:
            if exclude == (year, code):
                continue
            if year == 2024:
                v = {
                    "gf_budgtef_0100": 349119.2,
                    "gf_budgtef_0200": 2097621.9,
                    "gf_budgtef_0300": 591579.7,
                    "gf_budgtef_0400": 247579.3,
                    "gf_budgtef_0500": 6396,
                    "gf_budgtef_0600": 70400.5,
                    "gf_budgtef_0700": 217419.4,
                    "gf_budgtef_0800": 38473,
                    "gf_budgtef_0900": 308643.8,
                    "gf_budgtef_1000": 514131.8,
                    "gf_budgtef_Total_1": 4441364.6,
                }[code]
            else:
                v = 100.0 if code != probe.TOTAL else 1000.0
            item = {"dt": f"{year}0101",
                    "txten": probe.FUNCTIONS.get(code, "Expenditure excluding transfers"),
                    "id_api": code, "leveli": 1 if code == probe.TOTAL else 2,
                    "freq": "Y", "mcr200p": "CBU", "tzep": "F_M_VC", "value": v}
            if incorrect and incorrect[0] == (year, code):
                item.update(incorrect[1])
            rows.append(item)
            if duplicate == (year, code):
                rows.append(item)
        # State rows must not be included; they may contain similar values.
        rows.append({"dt": f"{year}0101", "txten": "Defence",
                     "id_api": "gf_budgtef_0200", "freq": "Y",
                     "mcr200p": "SBU", "tzep": "F_M_VC", "value": 999999})
    return json.dumps(rows).encode("utf-8")


class TreasuryFunctionalTests(unittest.TestCase):
    def test_exact_2024_defence_and_net_interbudget_total(self):
        rows = probe.parse(sample())
        r = {(int(v["year"]), v["nbu_code"]): v for v in rows}
        self.assertEqual(len(rows), 12 * 11)
        self.assertEqual(r[(2024, "gf_budgtef_0200")]["value_uah_million"], "2097621.9")
        self.assertEqual(r[(2024, probe.TOTAL)]["value_uah_million"], "4441364.6")
        self.assertEqual(r[(2024, probe.TOTAL)]["functional_category"],
                         "total_excluding_transfers")

    def test_cbu_not_state_and_annual_same_year_date(self):
        rows = probe.parse(sample())
        self.assertEqual({r["perimeter"] for r in rows}, {"CBU"})
        self.assertEqual({r["source_dt"] for r in rows if r["year"] == "2024"},
                         {"20240101"})
        self.assertTrue(all(int(r["source_dt"][:4]) == int(r["year"]) for r in rows))

    def test_duplicate_and_missing_groups_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            probe.parse(sample(duplicate=(2023, "gf_budgtef_0200")))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            probe.parse(sample(exclude=(2023, "gf_budgtef_0200")))

    def test_2024_reference_revision_requires_review(self):
        with self.assertRaisesRegex(ValueError, "2024 anchor"):
            probe.parse(sample(incorrect=((2024, "gf_budgtef_0200"), {"value": 1})))

    def test_bad_unit_or_date_is_rejected(self):
        for field in ({"tzep": "F_Y_V"}, {"dt": "20250101"}):
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.parse(sample(incorrect=((2024, "gf_budgtef_0200"), field)))

    def test_incoherent_components_and_unknown_format_fail(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            probe.parse(sample(incorrect=((2020, "gf_budgtef_0200"), {"value": 500})))
        with self.assertRaises(ValueError):
            probe.parse(b"<html>Forbidden</html>")
        with self.assertRaises(ValueError):
            probe.parse(b"[]")

    def test_csv_retains_identity_and_not_a_chart_input(self):
        data = probe.as_csv(probe.parse(sample()))
        self.assertTrue(data.startswith("year,nbu_code,publisher_category,"))
        self.assertIn("2024,gf_budgtef_0200,defence,defence,CBU,2097621.9,20240101", data)
        self.assertNotIn("general_government", data)


if __name__ == "__main__":
    unittest.main()
