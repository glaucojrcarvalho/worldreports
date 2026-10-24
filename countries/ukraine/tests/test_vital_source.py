"""Offline fail-closed tests for Ukraine's five official vital-statistics series.

Source codelist SSSU:CL_POPULATION_INDICATOR(6.0.1), as verified 2026-10-24.
Rates are publisher observations, NEVER birth/death counts divided by a
different geographic population estimate.
"""
from __future__ import annotations

import csv
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "fetch" / "fetch_vital_sdmx.py"
spec = spec_from_file_location("ukraine_vital_review", MODULE)
vital = module_from_spec(spec)
spec.loader.exec_module(vital)
ACCEPTED = ROOT / "data" / "demography" / "vital_ukrstat.csv"

with ACCEPTED.open(encoding="utf-8", newline="") as fh:
    ACCEPTED_ROWS = {int(r["year"]): r for r in csv.DictReader(fh)}


def source_rows(name, *, override_year=None, override=None):
    """Synthetic source records for parser tests, never curated raw history."""
    flow, code, unit, dims = vital.SPECS[name]
    buf = StringIO()
    header = [
        "STRUCTURE_ID", "ACTION", "INDICATOR", *dims,
        "TIME_PERIOD", "OBS_VALUE", "OBS_FLAG", "NOTES_OBS",
        "UNITS_OF_MEASURE", "SCALE", "TERRITORIAL_COVERAGE",
    ]
    writer = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    flag_name = {
        "birth_rate_per_1000": "birth_rate_flag",
        "death_rate_per_1000": "death_rate_flag",
        "total_fertility": "fertility_flag",
    }.get(name)
    for year in vital.YEARS:
        r = ACCEPTED_ROWS[year]
        flagged = r.get(flag_name, "") if flag_name else ""
        row = {
            "STRUCTURE_ID": "SSSU:" + flow.replace("/", "(") + ")",
            "ACTION": "R", "INDICATOR": code, **dims,
            "TIME_PERIOD": str(year), "OBS_VALUE": r[name],
            "OBS_FLAG": flagged,
            "NOTES_OBS": "Data are not released under martial law"
                         if flagged else "",
            "UNITS_OF_MEASURE": unit, "SCALE": "0",
            "TERRITORIAL_COVERAGE": "Ukraine, regions",
        }
        if override and year == override_year:
            row.update(override)
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


class VitalSourceTests(unittest.TestCase):
    def test_exact_codelist_indicator_perimeter_and_units(self):
        self.assertEqual({k: (v[1], v[2]) for k, v in vital.SPECS.items()}, {
            "live_births": ("PNMI_17", "1760"),
            "deaths": ("PNMI_19", "1760"),
            "birth_rate_per_1000": ("PNMI_32", "2860"),
            "death_rate_per_1000": ("PNMI_46", "2860"),
            "total_fertility": ("PNMI_3341", "2840"),
        })
        self.assertEqual(vital.DEATH_DIMS["CITIZENSHIP"], "_Z")
        self.assertEqual(vital.BIRTH_DIMS["FAMILY_STATUS"], "_Z")
        self.assertEqual(vital.BIRTH_DIMS["REGION"], "UA00000000000000000")

    def test_all_five_series_are_reconstructed_without_filling_rates(self):
        decoded = {name: vital.decode(name, source_rows(name))
                   for name in vital.SPECS}
        result = vital.to_csv(vital.combine(decoded))
        self.assertEqual(result, ACCEPTED.read_text(encoding="utf-8"))
        self.assertIn("2025,167801,485290,,,,c,c,c", result)
        self.assertIn("2021,271983,714263,7.3,18.5,1.16,,,", result)

    def test_2022_to_2025_crude_rates_and_fertility_are_suppressed(self):
        for year in vital.SUPPRESSED:
            for name in ("birth_rate_per_1000", "death_rate_per_1000",
                         "total_fertility"):
                self.assertFalse(ACCEPTED_ROWS[year][name])
                self.assertEqual(ACCEPTED_ROWS[year][
                    {"birth_rate_per_1000": "birth_rate_flag",
                     "death_rate_per_1000": "death_rate_flag",
                     "total_fertility": "fertility_flag"}[name]], "c")
        self.assertEqual(ACCEPTED_ROWS[2025]["live_births"], "167801")
        self.assertEqual(ACCEPTED_ROWS[2025]["deaths"], "485290")

    def test_unit_source_dimension_and_geographic_drift_rejected(self):
        cases = [
            {"UNITS_OF_MEASURE": "2860"},
            {"SCALE": "6"}, {"INDICATOR": "PNMI_17"},
            {"REGION": "UA01000000000013043"}, {"GENDER": "FEMALE"},
            {"TERRAIN_TYPE": "RUR"}, {"CITIZENSHIP": "_T"},
            {"FREQ": "M"}, {"TERRITORIAL_COVERAGE": "Unknown"},
            {"STRUCTURE_ID": "SSSU:DF_POPULATION_MORTALITY(4.0.0)"},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                vital.decode("deaths", source_rows(
                    "deaths", override_year=2021, override=case))

    def test_no_false_death_rate_or_fertility_in_war_years(self):
        bad = [
            {"OBS_FLAG": ""},
            {"OBS_FLAG": "p"},
            {"OBS_VALUE": "0"},
            {"OBS_VALUE": "18.5"},
            {"NOTES_OBS": ""},
        ]
        for name in ("birth_rate_per_1000","death_rate_per_1000",
                     "total_fertility"):
            for case in bad:
                with self.subTest(name=name,case=case), self.assertRaises(ValueError):
                    vital.decode(name, source_rows(name,override_year=2024,
                                                   override=case))

    def test_old_observed_rate_cannot_be_zero_filled_or_erased(self):
        for case in [{"OBS_VALUE": ""}, {"OBS_FLAG": "c"},
                     {"OBS_VALUE": "0"}, {"OBS_VALUE": "-1"}]:
            with self.subTest(case=case), self.assertRaises(ValueError):
                vital.decode("birth_rate_per_1000", source_rows(
                    "birth_rate_per_1000", override_year=2021,
                    override=case))

    def test_no_publisher_revision_without_explicit_review(self):
        with self.assertRaisesRegex(ValueError, "anchor revised"):
            vital.decode("live_births", source_rows(
                "live_births", override_year=2025,
                override={"OBS_VALUE": "167802"}))

    def test_isolated_country_source_refuses_wrong_dimension_code(self):
        u = vital.source_url("deaths")
        self.assertIn("PNMI_19",u)
        self.assertIn("c%5BCITIZENSHIP%5D=_Z",u)
        self.assertIn("c%5BREGION%5D=UA00000000000000000",u)
        self.assertNotIn("c%5BCITIZENSHIP%5D=_T",u)


if __name__ == "__main__":
    unittest.main()
