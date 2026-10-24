"""Offline regression tests for source-vintage trade and GFCF shares."""
from __future__ import annotations
import csv
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=spec_from_file_location("ukr_macro",ROOT/"fetch"/"fetch_sssu_macro_ratios.py")
macro=module_from_spec(SPEC)
SPEC.loader.exec_module(macro)
TRADE=ROOT/"data"/"trade"/"trade_na.csv"
INVEST=ROOT/"data"/"spending"/"investment.csv"

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def make_source(name,update=None,drop=None):
    codes=macro.INDICATORS
    trade={int(r["year"]):r for r in read_csv(TRADE)}
    gfcf={int(r["year"]):r for r in read_csv(INVEST)}
    fields=["STRUCTURE_ID","ACTION","INDICATOR",*macro.DIMENSIONS,
            "TIME_PERIOD","OBS_VALUE","UNITS_OF_MEASURE","SCALE",
            "OBS_FLAG","TERRITORIAL_COVERAGE"]
    out=StringIO()
    w=csv.DictWriter(out,fieldnames=fields,lineterminator="\n")
    w.writeheader()
    for year in range(2010,2025):
        if year==drop:continue
        lookup={"exports":trade[year]["exports_uah_mn"],
                "imports":trade[year]["imports_uah_mn"],
                "gfcf":gfcf[year]["gfcf_uah_mn"]}
        row={"STRUCTURE_ID":macro.STRUCTURE,"ACTION":"R",
             "INDICATOR":codes[name],**macro.DIMENSIONS,
             "TIME_PERIOD":str(year),"OBS_VALUE":lookup[name],
             "UNITS_OF_MEASURE":"1090","SCALE":"6",
             "OBS_FLAG":"","TERRITORIAL_COVERAGE":"Ukraine"}
        if update and year==2024:row.update(update)
        w.writerow(row)
    return out.getvalue().encode("utf-8")

class MacroRatiosTests(unittest.TestCase):
    def test_national_accounts_current_price_sources_are_distinct(self):
        for item in ("exports","imports","gfcf"):
            url=macro.source_url(item)
            self.assertIn("CURR_PRICES",url)
            self.assertIn(macro.INDICATORS[item],url)
            self.assertIn("UA00000000000000000",url)

    def test_complete_annual_curated_denominator(self):
        gdp=macro.read_curated_gdp()
        self.assertEqual(len(gdp),15)
        self.assertEqual(gdp[2024],7662376)

    def test_all_three_publisher_series_have_15_observations(self):
        for item in macro.INDICATORS:
            years=macro.parse_component(make_source(item),item)
            self.assertEqual(set(years),set(range(2010,2025)))

    def test_derived_csv_exactly_matches_reviewed_snapshots(self):
        trade,investment=macro.transform(
            {item:make_source(item) for item in macro.INDICATORS},
            macro.read_curated_gdp(),
        )
        self.assertEqual(trade,TRADE.read_text(encoding="utf-8"))
        self.assertEqual(investment,INVEST.read_text(encoding="utf-8"))

    def test_import_amount_is_positive_but_balance_is_exports_less_imports(self):
        trade=read_csv(TRADE)
        row=next(r for r in trade if r["year"]=="2024")
        self.assertGreater(int(row["imports_uah_mn"]),0)
        self.assertEqual(row["balance_pct_gdp"],"-20.3445")
        self.assertLess(float(row["balance_pct_gdp"]),-15)
        self.assertEqual(next(r["gfcf_pct_gdp"] for r in read_csv(INVEST)
                              if r["year"]=="2024"),"18.4575")

    def test_rejects_wrong_scope_units_flags_and_anchors(self):
        for change in [
            {"REGION":"OTHER"}, {"PRICE_TYPE":"IDX_VOL_PY"},
            {"SCALE":"0"}, {"UNITS_OF_MEASURE":"1010"},
            {"OBS_FLAG":"M"}, {"TERRITORIAL_COVERAGE":"Other"},
            {"OBS_VALUE":"999999"},
        ]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                macro.parse_component(make_source("exports",change), "exports")

    def test_rejects_partial_vintage_and_incompatible_components(self):
        with self.assertRaisesRegex(ValueError,"incomplete"):
            macro.parse_component(make_source("imports",drop=2023),"imports")
        with self.assertRaises(ValueError):
            macro.transform({"exports":make_source("exports")},macro.read_curated_gdp())

if __name__=="__main__":
    unittest.main()
