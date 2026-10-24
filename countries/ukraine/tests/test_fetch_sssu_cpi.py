"""Semantic and fail-closed tests for Ukrstat annual-average CPI."""
from __future__ import annotations

import csv
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=spec_from_file_location("ukr_cpi",ROOT/"fetch"/"fetch_sssu_cpi.py")
cpi=module_from_spec(SPEC)
SPEC.loader.exec_module(cpi)
CURATED=ROOT/"data"/"macro"/"cpi.csv"
INDEX={
 2006:"109.1",2007:"112.8",2008:"125.2",2009:"115.9",2010:"109.4",
 2011:"108.0",2012:"100.6",2013:"99.7",2014:"112.1",2015:"148.7",
 2016:"113.9",2017:"114.4",2018:"110.9",2019:"107.9",2020:"102.7",
 2021:"109.4",2022:"120.2",2023:"112.9",2024:"106.5",2025:"112.7",
}

def fixture(update=None,drop=None,extra=None):
    cols=["STRUCTURE_ID","ACTION",*cpi.FILTERS,"TIME_PERIOD","OBS_VALUE",
          "UNITS_OF_MEASURE","SCALE","OBS_FLAG"]
    out=StringIO()
    writer=csv.DictWriter(out,fieldnames=cols,lineterminator="\n")
    writer.writeheader()
    for year,index in INDEX.items():
        if year==drop:
            continue
        row={"STRUCTURE_ID":cpi.DATAFLOW,"ACTION":"R",**cpi.FILTERS,
             "TIME_PERIOD":str(year),"OBS_VALUE":index,
             "UNITS_OF_MEASURE":"1010","SCALE":"0","OBS_FLAG":""}
        if year==2022 and update:
            row.update(update)
        writer.writerow(row)
    if extra:
        writer.writerow({"STRUCTURE_ID":cpi.DATAFLOW,"ACTION":"R",**cpi.FILTERS,
                         "TIME_PERIOD":"2026","OBS_VALUE":"110.0",
                         "UNITS_OF_MEASURE":"1010","SCALE":"0","OBS_FLAG":""})
    return out.getvalue().encode("utf-8")


class CPITests(unittest.TestCase):
    def test_publisher_exact_annual_average_not_december_cpi(self):
        url=cpi.source_url()
        self.assertIn("INDEX_CONSUMPRICE",url)
        self.assertIn("PREV_YEAR",url)
        self.assertIn("c%5BFREQ%5D=A",url)
        self.assertIn("c%5BGOODS_SERVICES_TYPE%5D=0",url)

    def test_all_twenty_completed_years_and_index_to_inflation(self):
        rows=cpi.parse_cpi(fixture())
        self.assertEqual(len(rows),20)
        self.assertEqual([int(r["year"]) for r in rows],list(range(2006,2026)))
        by_year={int(r["year"]):r for r in rows}
        for year,index in INDEX.items():
            with self.subTest(year=year):
                self.assertEqual(Decimal(by_year[year]["annual_inflation_pct"]),
                                 Decimal(index)-100)
        self.assertEqual(by_year[2013]["annual_inflation_pct"],"-0.3")
        self.assertEqual(by_year[2022]["annual_inflation_pct"],"20.2")
        self.assertEqual(by_year[2025]["annual_inflation_pct"],"12.7")

    def test_2026_is_partial_and_not_promoted(self):
        rows=cpi.parse_cpi(fixture(extra=True))
        self.assertNotIn("2026",[r["year"] for r in rows])

    def test_wrong_vintage_dimensions_or_flags_fail(self):
        for delta in [
            {"STRUCTURE_ID":"SSSU:DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE(1.0.0)"},
            {"BASE_PERIOD":"DEC_TODEC_PREV_YEAR"},
            {"FREQ":"M"},
            {"REGION":"OTHER"},
            {"GOODS_SERVICES_TYPE":"01"},
            {"UNITS_OF_MEASURE":"1090"},
            {"SCALE":"6"},
            {"OBS_FLAG":"M"},
            {"OBS_VALUE":"121.2"},
        ]:
            with self.subTest(change=delta),self.assertRaises(ValueError):
                cpi.parse_cpi(fixture(update=delta))

    def test_missing_year_is_not_zero_or_interpolated(self):
        with self.assertRaisesRegex(ValueError,"missing complete"):
            cpi.parse_cpi(fixture(drop=2018))

    def test_curated_file_matches_exact_source_vintage(self):
        expected=cpi.render_csv(cpi.parse_cpi(fixture()))
        with CURATED.open(encoding="utf-8",newline="") as stream:
            actual=stream.read()
        self.assertEqual(actual,expected)
        self.assertEqual(len(list(csv.DictReader(StringIO(actual)))),20)


if __name__=="__main__":
    unittest.main()
