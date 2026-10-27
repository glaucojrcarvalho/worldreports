"""Offline correctness checks for Moldova's Phase-A source research.

No network access, no full country registration, and no published plates
required. Moldova joins the regular atlas test suite only after Phase B.
"""
from __future__ import annotations

import csv
import importlib.util
import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
MOLDOVA = ROOT / "countries" / "moldova"
FETCHER = MOLDOVA / "fetch" / "fetch_wdi.py"

spec = importlib.util.spec_from_file_location("moldova_fetch_wdi", FETCHER)
assert spec is not None and spec.loader is not None
wdi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wdi)


def load_csv(name: str) -> list[dict[str, str]]:
    with (MOLDOVA / "data" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(line for line in stream
                                   if not line.startswith("#")))


def get(rows: list[dict[str, str]], year: int, column: str) -> float | None:
    row = next(r for r in rows if int(r["year"]) == year)
    return float(row[column]) if row[column] else None


def test_manifest_covers_exact_staged_publisher_files() -> None:
    manifest = yaml.safe_load((MOLDOVA / "SOURCES.yaml").read_text("utf-8"))
    declared = {
        f"{group}/{name}"
        for group, entries in manifest.items()
        if group != "meta" and isinstance(entries, dict)
        for name in entries
    }
    files = {
        str(f.relative_to(MOLDOVA / "data"))
        for f in (MOLDOVA / "data").rglob("*.csv")
        if not f.stem.endswith(("_from_wb", "_from_bns", "_from_undp", "_from_ti", "_from_nbm"))
    }
    expected = set(wdi.GROUPS) | {
        "fiscal/budget_summary.csv", "fiscal/public_budget.csv",
        "fiscal/nominal_gdp_bns.csv",
        "fiscal/weo_bal_debt.csv", "fiscal/fpp_finances.csv",
        "markets/policy.csv", "markets/usd_mdl.csv",
        "people/absolute_poverty.csv", "people/minimum_wage.csv", "world/hdi.csv", "world/cpi.csv",
        "trade/destinations.csv", "credit/prudential_npl.csv",
        "migration/foreign_born_census.csv",
    }
    assert declared == files == expected
    assert manifest["meta"]["status"] == "research_only_not_an_atlas_edition"
    for group, entries in manifest.items():
        if group == "meta":
            continue
        for name, details in entries.items():
            if group == "fiscal":
                assert name in {
                    "budget_summary.csv", "public_budget.csv", "nominal_gdp_bns.csv",
                    "weo_bal_debt.csv", "fpp_finances.csv",
                }
                assert details["official"] is True
                if name in {"budget_summary.csv", "public_budget.csv"}:
                    assert details["source"].startswith("National Bureau of Statistics")
                    assert details["refreshed_by"] == "fetch/fetch_bns_budget.py"
                elif name == "nominal_gdp_bns.csv":
                    assert details["source"].startswith("National Bureau of Statistics")
                    assert details["refreshed_by"] == "fetch/fetch_bns_gdp.py"
                    assert "2025" in details["notes"] and "PRELIMINARY" in details["notes"]
                else:
                    assert details["source"].startswith("International Monetary Fund")
                    assert details["refreshed_by"] == "fetch/fetch_imf.py"
            elif group == "markets":
                assert name in {"policy.csv", "usd_mdl.csv"}
                assert details["source"].startswith("National Bank of Moldova")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_nbm.py"
            elif group == "world" and name == "cpi.csv":
                assert details["source"].startswith("Transparency International")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_ti.py"
                assert "2012" in details["notes"] and "2006-2011" in details["notes"]
            elif group == "world" and name == "hdi.csv":
                assert details["source"].startswith("United Nations Development Programme")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_undp.py"
                assert "2022=0.784" in details["notes"]
            elif group == "trade" and name == "destinations.csv":
                assert details["source"].startswith("National Bureau of Statistics")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_bns_trade.py"
                assert "2024" in details["notes"]
            elif group == "people" and name == "absolute_poverty.csv":
                assert details["source"].startswith("National Bureau of Statistics")
                assert details["official"] is True
                assert "2019" in details["notes"]
                assert "Raport_ODD_" in details["url"]
            elif group == "people" and name == "minimum_wage.csv":
                assert details["source"].startswith("Government of the Republic of Moldova")
                assert details["official"] is True
                assert "2022-09-01" in details["notes"]
                assert "2023=4000" in details["notes"]
                assert "fetch/fetch_nbm.py" in details["refreshed_by"]
            elif group == "migration" and name == "foreign_born_census.csv":
                assert details["source"].startswith("National Bureau of Statistics")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_bns_census_foreign_born.py"
                assert "4.4%" in details["notes"] and "2024-04-08" in details["notes"]
            elif group == "credit" and name == "prudential_npl.csv":
                assert details["source"].startswith("National Bank of Moldova")
                assert details["official"] is True
                assert details["refreshed_by"] == "fetch/fetch_nbm_npl.py"
                assert "2022=6.4%" in details["notes"] and "2025=4.1%" in details["notes"]
                assert "NOT" in details["notes"] and "IFRS" in details["notes"]
            else:
                assert details["source"].startswith("World Bank WDI")
                assert details["official"] is False
                assert details["refreshed_by"] == "fetch/fetch_wdi.py"


@pytest.mark.parametrize("file,columns", wdi.GROUPS.items())
def test_staged_csv_complete_year_grid_with_no_invalid_values(file, columns) -> None:
    rows = load_csv(file)
    assert len(rows) == 20
    assert [int(row["year"]) for row in rows] == list(range(2006, 2026))
    assert list(rows[0]) == ["year", *(name for name, _ in columns)]
    for row in rows:
        for name, _ in columns:
            if row[name]:
                assert math.isfinite(float(row[name]))


def test_source_snapshot_anchors() -> None:
    macro = load_csv("macro/economy.csv")
    pop = load_csv("demography/demography.csv")
    trade = load_csv("trade/trade.csv")
    assert get(macro, 2025, "gdp_growth_pct") == pytest.approx(2.41649734575068, abs=1e-6)
    assert get(macro, 2024, "gdp_growth_pct") == pytest.approx(.270670455512573, abs=1e-6)
    assert get(pop, 2025, "population") == 2_360_527
    assert get(pop, 2024, "population") == 2_402_306
    assert get(trade, 2025, "exports_pct_gdp") == pytest.approx(31.75193204685, abs=1e-6)
    assert get(trade, 2025, "imports_pct_gdp") == pytest.approx(60.91424073893, abs=1e-6)


def test_source_gaps_are_not_zero_filled_or_interpolated() -> None:
    assert get(load_csv("people/gini.csv"), 2025, "gini") is None
    demography = load_csv("demography/demography.csv")
    assert get(demography, 2025, "fertility") is None
    assert get(demography, 2025, "death_rate_per_1000") is None
    security = load_csv("security/security.csv")
    assert get(security, 2024, "homicide_per_100k") is None
    assert get(security, 2020, "road_deaths_per_100k") is None
    assert get(security, 2022, "suicide_per_100k") is None
    migration = load_csv("migration/migration.csv")
    snapshot_years = {int(row["year"]) for row in migration if row["migrant_stock"]}
    assert snapshot_years == {2010, 2015, 2020, 2024}




def test_bns_2024_2025_fiscal_outturns_are_explicitly_editioned() -> None:
    rows = load_csv("fiscal/budget_summary.csv")
    assert [int(r["year"]) for r in rows] == [2024, 2025]
    assert [r["edition"] for r in rows] == ["final", "preliminary"]
    for year, revenue, expenditure, balance in [
        (2024, 110338.5, 122962.6, -12624.1),
        (2025, 125602.0, 139856.4, -14254.4),
    ]:
        assert get(rows, year, "revenue_mdl_mn") == revenue
        assert get(rows, year, "expenditure_mdl_mn") == expenditure
        assert get(rows, year, "balance_mdl_mn") == balance
        assert abs(revenue - expenditure - balance) < 0.1
    text = (MOLDOVA / "data" / "fiscal" / "budget_summary.csv").read_text("utf-8")
    assert "not imf" in text.lower()
    assert "left-bank Nistru" in text
    assert "PRELIMINARY" in text


def example_payload() -> list:
    rows = [
        {"indicator": {"id": "SP.POP.TOTL"}, "countryiso3code": "MDA",
         "date": str(year), "value": 2_500_000 + year, "obs_status": ""}
        for year in range(2020, 2024)
    ]
    return [{"page": 1, "pages": 1, "sourceid": "2",
             "total": len(rows), "lastupdated": "2026-10-08"}, rows]


def test_schema_guard_accepts_a_complete_wdi_page() -> None:
    values, vintage = wdi.validate_wdi_payload(example_payload(), "SP.POP.TOTL")
    assert vintage == "2026-10-08"
    assert len(values) == 4


@pytest.mark.parametrize("mutate", [
    lambda p: p[0].update(pages=2),
    lambda p: p[0].update(sourceid="1"),
    lambda p: p[1][1].update(countryiso3code="UKR"),
    lambda p: p[1][1].update(date="2020"),
    lambda p: p[1][1].update(obs_status="F"),
    lambda p: p[1][1].update(value=float("nan")),
])
def test_schema_guard_rejects_wrong_perimeter_or_payload(mutate) -> None:
    payload = example_payload()
    mutate(payload)
    with pytest.raises(ValueError):
        wdi.validate_wdi_payload(payload, "SP.POP.TOTL")


def test_sidecar_writer_preserves_undisclosed_years_as_blanks() -> None:
    cols = (("population", "SP.POP.TOTL"),)
    rendered = wdi.sidecar_text(cols, {"SP.POP.TOTL": {2024: 2402306.0}},
                                "2026-10-08")
    rows = list(csv.DictReader(line for line in rendered.splitlines()
                               if not line.startswith("#")))
    assert next(row for row in rows if row["year"] == "2023")["population"] == ""
    assert next(row for row in rows if row["year"] == "2024")["population"] == "2402306.000000"
    assert next(row for row in rows if row["year"] == "2025")["population"] == ""


def test_verified_publisher_ledger_is_not_contradicted_by_pending_routes() -> None:
    """Live audited publisher routes must not drift back into discovery gaps."""
    manifest = yaml.safe_load((MOLDOVA / "SOURCES.yaml").read_text("utf-8"))
    ledger = manifest["meta"]["verified"]
    by_name = {entry["name"]: entry for entry in ledger}
    names_and_files = {
        "BNS same-territory nominal GDP and functional public-budget shares, 2016–2025": {
            "fiscal/public_budget.csv", "fiscal/nominal_gdp_bns.csv"},
        "BNS customs merchandise export destinations, 2006–2025": {
            "trade/destinations.csv"},
        "NBM bank-wide prudential non-performing loans, 2022–2025": {
            "credit/prudential_npl.csv"},
        "UNDP HDR 2025 historical HDI for Moldova, 2006–2023": {
            "world/hdi.csv"},
        "TI CPI 2025 comparable corruption perception scores, 2012–2025": {
            "world/cpi.csv"},
    }
    assert len(by_name) == len(ledger), "Duplicate verified-source names"
    for name, paths in names_and_files.items():
        entry = by_name[name]
        assert entry["official"] is True
        assert set(entry["dataset_paths"]) == paths
        assert entry["reviewed_utc"] == "2026-10-27"
        assert entry["evidence"].startswith(
            "https://github.com/glaucojrcarvalho/worldreports/actions/runs/")
        for path in paths:
            assert (MOLDOVA / "data" / path).is_file(), path
            group, filename = path.split("/", 1)
            assert manifest[group][filename]["official"] is True
            assert manifest[group][filename]["source"]
            assert manifest[group][filename]["url"].startswith("https://")
    pending = " ".join(
        (item["name"] + " " + item["notes"]).lower()
        for item in manifest["meta"]["pending"])
    assert "nonperforming ratio" not in pending
    assert "non-performing ratio" not in pending
    assert "prudential npl series is already verified" in pending
    assert "household" in pending and "10-year" in pending
    assert "2016-2024" in by_name[
        "BNS same-territory nominal GDP and functional public-budget shares, 2016–2025"
    ]["notes"]
    assert "NOT a household-only" in by_name[
        "NBM bank-wide prudential non-performing loans, 2022–2025"
    ]["notes"]
    assert "0.763" in by_name[
        "UNDP HDR 2025 historical HDI for Moldova, 2006–2023"
    ]["notes"]
    assert "2012" in by_name[
        "TI CPI 2025 comparable corruption perception scores, 2012–2025"
    ]["notes"]
