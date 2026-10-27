"""Read-only issuer-definition audit; no invented Moldova annual observations."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research/source_candidates"
NBM_ANNUAL_ROUTE = "https://www.bnm.md/bdi/pages/reports/dpmc/DPMC8.xhtml?lang=en"
NBM_OUTSTANDING_ROUTE = "https://www.bnm.md/bdi/pages/reports/dpmc/DPMC10.xhtml?id=74410&lang=en"
ERP_URL = "https://mf.gov.md/sites/default/files/ERP%202026-2028%20ENG.pdf"
SNAPSHOTS = {
  (2024, 12): ("6.99", "2025-01-20", "https://bnm.md/en/content/bank-loans-market-development-december-2024-0"),
  (2025, 12): ("8.24", "2026-01-20", "https://www.bnm.md/en/content/developments-bank-loan-market-december-2025"),
}
# Column headers cross-checked against both distinct ERP tables
# and Table 1e GDP for the SAME year, not by positional offset.
ERP = {
  2024: ("3.20", "1.0", "erp_historical_baseline"),
  2025: ("3.40", "1.0", "erp_program_estimate"),
  2026: ("5.20", "1.4", "erp_forecast_not_observed"),
  2027: ("8.10", "2.0", "erp_forecast_not_observed"),
  2028: ("8.00", "1.8", "erp_forecast_not_observed"),
}
ERP_NOMINAL_GDP = {
  2024: 323.8, 2025: 351.5, 2026: 377.6,
  2027: 406.9, 2028: 440.0,
}

def rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(s for s in f if not s.startswith("#")))

def verify(mortgage,investment):
    if len(mortgage)!=2 or {(int(r["year"]),int(r["month"])) for r in mortgage}!=set(SNAPSHOTS):
        raise AssertionError("Expected exactly two December mortgage observations")
    for r in mortgage:
        year,month=int(r["year"]),int(r["month"])
        expected=SNAPSHOTS[year,month]
        identity=(r["country"],r["borrower_category"],r["loan_purpose"],
                  r["currency"],r["measure"],r["observation_type"])
        if identity!=("MDA","individuals","real_estate_new_loans","MDL",
                     "nominal_new_loan_rate","monthly_december_snapshot"):
            raise AssertionError("Wrong loan flow, borrower, purpose, currency or frequency")
        if (r["rate_pct"],r["release_date"],r["source_url"])!=expected:
            raise AssertionError("Mortgage publisher observation or vintage changed")
        if not 0<float(r["rate_pct"])<100:
            raise AssertionError("Mortgage interest rate out of range")
    if len(investment)!=5 or {int(r["year"]) for r in investment}!=set(ERP):
        raise AssertionError("Expected government P51 baseline and estimates")
    for r in investment:
        year=int(r["year"])
        if (r["sector"],r["transaction"],r["unit"],r["edition"],
            r["source_pdf"],r["printed_page"])!=(
            "S13","P51","nominal_bn_mdl","2026-01",ERP_URL,"82"):
            raise AssertionError("Government P51 sector or edition drift")
        if (r["amount_bn_mdl"],r["share_pct_gdp"],r["status"])!=ERP[year]:
            raise AssertionError("ERP value/forecast classification mismatch")
        if not 0<float(r["share_pct_gdp"])<12:
            raise AssertionError("Government GFCF exceeds canonical shared scale")
        # Cross-table invariant: 2b nominal capital / Table 1e nominal GDP
        # must round to the Table 2a percent-GDP value in SAME year.
        same_year_share = 100 * float(r["amount_bn_mdl"]) / ERP_NOMINAL_GDP[year]
        if abs(same_year_share - float(r["share_pct_gdp"])) > 0.06:
            raise AssertionError("Government GFCF fails same-year nominal GDP reconciliation")
    registered = ROOT/"country.yaml"
    # Full atlas CI temporarily registers an EXACT candidate copy.
    # The real research Git tree stays unregistered; no other config is valid.
    if registered.exists() and registered.read_bytes() != (
        ROOT/"research/country_candidate.yaml").read_bytes():
        raise AssertionError("Non-candidate Moldova country registered")
    return {
       "decision":"SOURCE_LANES_VERIFIED_NO_CANONICAL_PROMOTION",
       "household_new_loans":{
          "official_annual_export":NBM_ANNUAL_ROUTE,
          "incorrect_outstanding_balance_route":NBM_OUTSTANDING_ROUTE,
          "December_only_official_snapshots":len(mortgage),
          "annual_rate_rows_verified":0,
          "blockers":[
             "Export DPMC8 annual nominal MDL individuals-real-estate series, total maturities",
             "Verify original weighted method and a coherent annual historical release",
             "Never substitute a DPMC10 stock-rate or a December snapshot for an annual average",
          ],
       },
       "public_investment":{
          "source":ERP_URL,"perimeter":"S13 general government","transaction":"P51",
          "historical_baseline":[2024],"program_estimate":[2025],"forecast":[2026,2027,2028],
          "verified_continuous_historical_series":False,
          "blockers":[
             "S13 P51 January-2026 programme is not a long historical annual series",
             "2025 estimate and 2026-28 forecasts are not independently verified final outturns",
             "Do not substitute economy-wide WDI GFCF or national cash spending",
          ],
       },
       "pending_canonical":["credit.lending_rate","spending.public_investment"],
       "canonical_data_rows_changed":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("/tmp/moldova-official-source-lanes.json"))
    args=p.parse_args()
    result=verify(rows(DATA/"nbm_mortgage_december.csv"),
                  rows(DATA/"gov_gfcf_erp.csv"))
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PASS: official mortgage-rate and government P51 lanes; no annual promotion")

if __name__=="__main__":
    main()
