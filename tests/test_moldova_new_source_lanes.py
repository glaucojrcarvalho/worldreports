"""Moldova publisher metadata guards: annual rates cannot be inferred."""
import pytest
from countries.moldova.research.audit_new_source_lanes import (
    ROOT,DATA,NBM_ANNUAL_ROUTE,NBM_OUTSTANDING_ROUTE,rows,verify
)
def evidence():
    return rows(DATA/"nbm_mortgage_december.csv"),rows(DATA/"gov_gfcf_erp.csv")

def test_two_official_routes_keep_both_canonical_slots_pending():
    mortgage,investment=evidence()
    r=verify(mortgage,investment)
    assert r["decision"]=="SOURCE_LANES_VERIFIED_NO_CANONICAL_PROMOTION"
    assert "DPMC8" in r["household_new_loans"]["official_annual_export"]
    assert "DPMC10" in r["household_new_loans"]["incorrect_outstanding_balance_route"]
    assert r["household_new_loans"]["December_only_official_snapshots"]==2
    assert r["household_new_loans"]["annual_rate_rows_verified"]==0
    assert r["public_investment"]["historical_baseline"]==[2024]
    assert r["public_investment"]["program_estimate"]==[2025]
    assert r["public_investment"]["forecast"]==[2026]
    assert r["canonical_data_rows_changed"]==0
    registered = ROOT/"country.yaml"
    if registered.exists():
        assert registered.read_bytes() == (
            ROOT/"research/country_candidate.yaml").read_bytes()

@pytest.mark.parametrize("field,bad",[
    ("borrower_category","businesses"),
    ("loan_purpose","all_loans"),
    ("currency","EUR"),
    ("measure","outstanding_balance_rate"),
    ("observation_type","annual_mean"),
    ("rate_pct","8.99"),
    ("source_url",NBM_OUTSTANDING_ROUTE),
])
def test_reject_wrong_rate_category_stock_or_annual_splice(field,bad):
    mortgage,investment=evidence()
    mortgage[-1][field]=bad
    with pytest.raises(AssertionError):
        verify(mortgage,investment)

@pytest.mark.parametrize("field,bad",[
    ("sector","S1"),
    ("transaction","P51_entire_economy"),
    ("status","erp_historical_baseline"),
    ("unit","pct_of_gdp"),
    ("share_pct_gdp","22.0"),
    ("source_pdf","https://example.invalid"),
])
def test_reject_economywide_investment_and_forecast_as_actual(field,bad):
    mortgage,investment=evidence()
    investment[1][field]=bad
    with pytest.raises(AssertionError):
        verify(mortgage,investment)

def test_missing_snapshot_or_source_release_rejected():
    mortgage,investment=evidence()
    with pytest.raises(AssertionError):
        verify(mortgage[:1],investment)
    with pytest.raises(AssertionError):
        verify(mortgage,investment[:1])
