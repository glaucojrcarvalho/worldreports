"""Verify official Ukrstat SDMX GDP semantics without using network."""
from __future__ import annotations

import csv
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "fetch" / "fetch_sssu_gdp.py"
SPEC = spec_from_file_location("ukr_gdp_fetch", SCRIPT)
gdp = module_from_spec(SPEC)
SPEC.loader.exec_module(gdp)


def fixture(overrides=None, drop=None):
    """Use the observed year/volume index anchors, not made-up GDP growth."""
    indexes = {
        2011: "105.5", 2012: "100.2", 2013: "100.0", 2014: "93.4",
        2015: "90.2", 2016: "102.4", 2017: "102.4", 2018: "103.5",
        2019: "103.2", 2020: "96.2", 2021: "103.4", 2022: "71.2",
        2023: "105.5", 2024: "103.2",
    }
    columns = ["STRUCTURE[;]", "STRUCTURE_ID", "ACTION",
               *gdp.DIMENSIONS, "TIME_PERIOD", "OBS_VALUE",
               "UNITS_OF_MEASURE", "SCALE", "OBS_FLAG",
               "TERRITORIAL_COVERAGE"]
    buff = StringIO()
    wr = csv.DictWriter(buff, fieldnames=columns, lineterminator="\n")
    wr.writeheader()
    for year, value in indexes.items():
        if year == drop:
            continue
        row = {
            "STRUCTURE[;]": "dataflow",
            "STRUCTURE_ID": gdp.EXPECTED_STRUCTURE,
            "ACTION": "R",
            **gdp.DIMENSIONS,
            "TIME_PERIOD": str(year),
            "OBS_VALUE": value,
            "UNITS_OF_MEASURE": "1010",
            "SCALE": "0",
            "OBS_FLAG": "",
            "TERRITORIAL_COVERAGE": "Ukraine",
        }
        if year == 2022 and overrides:
            row.update(overrides)
        wr.writerow(row)
    return buff.getvalue().encode()


class GDPSourceTests(unittest.TestCase):
    def test_exact_url_filters_all_canonical_dimensions(self):
        u = gdp.data_url()
        self.assertIn("DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/", u)
        self.assertIn("GDP_CUR_PRC", u)
        self.assertIn("IDX_VOL_PY", u)
        self.assertIn("UA00000000000000000", u)

    def test_growth_derived_from_previous_year_volume_index(self):
        rows = gdp.parse_annual_growth(fixture())
        observed = {int(r["year"]): r for r in rows}
        self.assertEqual(len(rows), 14)
        self.assertEqual(observed[2022]["volume_index_py"], "71.2")
        self.assertEqual(observed[2022]["real_growth"], "-28.8")
        self.assertEqual(observed[2015]["real_growth"], "-9.8")
        self.assertEqual(observed[2023]["real_growth"], "5.5")
        self.assertNotIn(2025, observed)

    def test_curated_shape_and_year_order(self):
        text = gdp.render_csv(gdp.parse_annual_growth(fixture()))
        self.assertTrue(text.startswith("year,real_growth,volume_index_py\n"))
        self.assertIn("2022,-28.8,71.2\n", text)
        self.assertEqual(len(text.strip().splitlines()), 15)

    def test_wrong_dimension_or_wrong_vintage_rejected(self):
        for update in [
            {"REGION": "UA00000000000000001"},
            {"PRICE_TYPE": "CURR_PRICES"},
            {"STRUCTURE_ID": "SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(6.0.0)"},
            {"FREQ": "Q"},
        ]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                gdp.parse_annual_growth(fixture(update))

    def test_units_flags_and_anchor_revisions_require_review(self):
        for update in [
            {"SCALE": "3"},
            {"UNITS_OF_MEASURE": "999"},
            {"OBS_FLAG": "M"},
            {"OBS_VALUE": "72.2"},
            {"TERRITORIAL_COVERAGE": "Other"},
        ]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                gdp.parse_annual_growth(fixture(update))

    def test_missing_anchor_not_replaced_with_zero(self):
        with self.assertRaisesRegex(ValueError, "lacks control"):
            gdp.parse_annual_growth(fixture(drop=2022))

    def test_explicit_historical_gap_is_not_imputed(self):
        rows = gdp.parse_annual_growth(fixture(drop=2018))
        self.assertNotIn("2018", [r["year"] for r in rows])
        self.assertEqual(len(rows), 13)

    def test_empty_or_malformed_file_fails_closed(self):
        with self.assertRaises(ValueError):
            gdp.parse_annual_growth(b"oops\n")
        with self.assertRaises(ValueError):
            gdp.parse_annual_growth(b"\xff")


if __name__ == "__main__":
    unittest.main()
