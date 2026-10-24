"""Validate SSSU population, Jan-1 geography seams and suppressed 2023-25.

Offline fabricated SDMX fixtures check parsing only; acceptance anchors and
the curated source CSV are independently checked against the publisher.
"""
from __future__ import annotations

import csv
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "ukr_population", ROOT / "fetch" / "fetch_sssu_population.py")
src = module_from_spec(SPEC)
SPEC.loader.exec_module(src)
ACCEPTED = ROOT / "data" / "social" / "population.csv"

PUBLISHER_VALUES = {
    2006: 46929525, 2007: 46646046, 2008: 46372664,
    2009: 46143714, 2010: 45962947, 2011: 45778534,
    2012: 45633637, 2013: 45553047, 2014: 45426249,
    2015: 42929298, 2016: 42760516, 2017: 42584542,
    2018: 42386403, 2019: 42153201, 2020: 41902416,
    2021: 41588354, 2022: 41167335,
}
SUPPRESSION_NOTE = (
    "Data are not released in order to comply with the requirements of "
    "Ukraine's law on official statistics during the Period of Martial Law."
)
FIELDS = [
    "STRUCTURE_ID", "ACTION", *src.DIMENSIONS,
    "TIME_PERIOD", "OBS_VALUE", "UNITS_OF_MEASURE", "SCALE",
    "OBS_FLAG", "NOTES_OBS", "TERRITORIAL_COVERAGE",
]


def official_shape(*, change=None, drop=None, additional=None):
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for year in range(src.FIRST, src.LAST + 1):
        if year == drop:
            continue
        observed = year <= src.LAST_OBSERVED
        row = {
            "STRUCTURE_ID": src.FLOW, "ACTION": "R",
            **src.DIMENSIONS, "TIME_PERIOD": str(year),
            "OBS_VALUE": str(PUBLISHER_VALUES[year]) if observed else "",
            "UNITS_OF_MEASURE": src.UNIT, "SCALE": src.SCALE,
            "OBS_FLAG": "" if observed else "c",
            "NOTES_OBS": "" if observed else SUPPRESSION_NOTE,
            "TERRITORIAL_COVERAGE": "Ukraine, regions",
        }
        if year == 2022 and change:
            row.update(change)
        if year == 2024 and additional:
            row.update(additional)
        writer.writerow(row)
    return out.getvalue().encode("utf-8")


class PopulationSourceTests(unittest.TestCase):
    def test_national_jan_first_selection_not_displacement_or_survey(self):
        url = src.source_url()
        self.assertIn("DF_POPULATION_STRUCTURE/8.0.1", url)
        for expected in ("PNMI_01", "UA00000000000000000",
                         "c%5BTERRAIN_TYPE%5D=_T", "c%5BFREQ%5D=A"):
            self.assertIn(expected, url)

    def test_exact_publisher_counts_and_suppressed_years(self):
        rows = src.parse_population(official_shape())
        self.assertEqual(len(rows), 20)
        self.assertEqual([int(row["year"]) for row in rows], list(range(2006, 2026)))
        observed = {int(row["year"]): row for row in rows}
        for year, count in PUBLISHER_VALUES.items():
            with self.subTest(year=year):
                self.assertEqual(observed[year]["population_persons"], str(count))
                self.assertEqual(observed[year]["obs_flag"], "")
        for year in (2023, 2024, 2025):
            with self.subTest(year=year):
                self.assertEqual(observed[year]["population_persons"], "")
                self.assertEqual(observed[year]["obs_flag"], "c")

    def test_curated_csv_reproducible_without_fill_or_splice(self):
        data = src.to_csv(src.parse_population(official_shape()))
        self.assertEqual(data, ACCEPTED.read_text(encoding="utf-8"))
        self.assertIn("2025,,c\n", data)
        self.assertIn("2022,41167335,\n", data)

    def test_changes_of_units_and_dimensions_require_manual_review(self):
        for delta in (
            {"REGION": "UA01000000000013043"},
            {"AGE": "15"}, {"GENDER": "F"},
            {"TERRAIN_TYPE": "URB"},
            {"INDICATOR": "PNMI_02"}, {"FREQ": "M"},
            {"UNITS_OF_MEASURE": "1010"}, {"SCALE": "3"},
            {"STRUCTURE_ID": "SSSU:DF_POPULATION_STRUCTURE(7.0.0)"},
            {"ACTION": "D"},
            {"TERRITORIAL_COVERAGE": "Occupied regions excluded"},
            {"OBS_FLAG": "c"}, {"OBS_VALUE": "0"},
            {"OBS_VALUE": "40000000"},
        ):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                src.parse_population(official_shape(change=delta))

    def test_wrong_suppression_or_data_release_requires_manual_review(self):
        for delta in (
            {"OBS_FLAG": ""},
            {"OBS_FLAG": "M"},
            {"OBS_VALUE": "40000000"},
            {"NOTES_OBS": ""},
            {"NOTES_OBS": "Missing for unknown reasons"},
        ):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                src.parse_population(official_shape(additional=delta))

    def test_omitted_year_fails_instead_of_zero_or_interpolation(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            src.parse_population(official_shape(drop=2017))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            src.parse_population(official_shape(drop=2024))

    def test_no_html_or_corrupt_csv(self):
        with self.assertRaises(ValueError):
            src.parse_population(b"<html>rate limit</html>")
        with self.assertRaises(ValueError):
            src.parse_population(b"\xff")

    def test_2015_geographical_scope_drop_not_a_demographic_loss_rate(self):
        self.assertGreater(PUBLISHER_VALUES[2014] - PUBLISHER_VALUES[2015],
                           2_000_000)
        # The physical headcount drop is distorted by statistical exclusions.
        # The plate must split at Jan-1 2015 and must not claim this is all
        # emigration or excess death of people in one year.


if __name__ == "__main__":
    unittest.main()
