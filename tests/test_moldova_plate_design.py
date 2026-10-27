"""Design-level checks for Moldova's draft atlas plates (not registry tests).

The real English render runs in a disposable CI runner with the candidate
country.yaml temporarily copied into place. These tests protect the data
semantics even while the atlas is not yet published.
"""
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest
from core import render, spine

ROOT = Path(__file__).resolve().parent.parent / "countries/moldova"


def _rows(rel):
    with (ROOT / "data" / rel).open(encoding="utf-8") as stream:
        return [{k: float(v) if k != "year" and v else
                 int(v) if k == "year" else None
                 for k, v in row.items()}
                for row in csv.DictReader(
                    line for line in stream if not line.startswith("#"))]


def _plates():
    spec = importlib.util.spec_from_file_location("moldova_draft_plates",
                                                   ROOT / "plates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return render.normalise(module.PLATES)


def test_twelve_declarative_spine_topics_without_duplicate_ids():
    plates = _plates()
    assert len(plates) == 12
    topics = [p.topic for p in plates]
    assert len(topics) == len(set(topics))
    assert set(topics) == set(spine.SPINE) - {"prices"}
    assert [p.filename for p in plates] == [
        f"{i:02d}-{topic}.png" for i, topic in enumerate(topics, start=1)]
    assert all(p.alt and p.subtitle and p.source for p in plates)


def test_shared_spine_scales_cover_moldova_without_country_local_override():
    rows = _rows("trade/trade.csv")
    balance = {int(r["year"]): r["exports_pct_gdp"] - r["imports_pct_gdp"]
               for r in rows}
    lo, hi = spine.SLOTS["trade.balance"].ref
    assert balance[2008] == pytest.approx(-52.777445, abs=0.03)
    assert balance[2025] == pytest.approx(-29.162309, abs=0.03)
    assert lo <= min(balance.values()) and max(balance.values()) <= hi
    assert lo == -60 and hi == 40
    text = (ROOT / "plates.py").read_text(encoding="utf-8")
    assert 'ig.slot("trade.balance"' in text
    assert "ctx.bars(ax, years, balance" in text
    assert 'ig.slot("trade.lens"' not in text

    world = _rows("world/world.csv")
    gdp = [r["gdp_usd"] / 1e9 for r in world]
    reserves = [r["reserves_usd"] / 1e9 for r in world]
    gdp_ref = spine.SLOTS["world.gdp"].ref
    reserves_ref = spine.SLOTS["world.reserves"].ref
    assert gdp_ref == (1, 50_000)
    assert reserves_ref == (0.1, 5_000)
    assert min(gdp) >= gdp_ref[0] and max(gdp) <= gdp_ref[1]
    assert min(reserves) >= reserves_ref[0] and max(reserves) <= reserves_ref[1]
    assert spine._LADDER_GDP[0] == gdp_ref[0]
    assert spine._LADDER_RESERVES[0] == reserves_ref[0]


def test_wdi_net_migration_is_joined_to_wdi_population_only():
    movement = {r["year"]: r["net_migration"]
                for r in _rows("migration/migration.csv")}
    residents = {r["year"]: r["population"]
                 for r in _rows("demography/demography.csv")}
    assert movement.keys() == residents.keys()
    rates = {year: movement[year] / residents[year] * 1_000
             for year in residents}
    assert rates[2022] == pytest.approx(35.26, abs=0.02)
    assert all(spine.SLOTS["migration.net"].ref[0] <= r <=
               spine.SLOTS["migration.net"].ref[1] for r in rates.values())


def test_migrant_stock_remains_snapshots_not_annual_interpolation():
    rows = _rows("migration/migration.csv")
    stock = {r["year"] for r in rows if r["migrant_stock"] is not None}
    assert stock == {2010, 2015, 2020, 2024}
    src = (ROOT / "plates.py").read_text(encoding="utf-8")
    assert "ax.scatter(years, share" in src
    assert 'ig.slot("migration.foreign_born"' in src


def test_fiscal_vintages_and_projection_are_never_conflated():
    fpp = _rows("fiscal/fpp_finances.csv")
    weo = _rows("fiscal/weo_bal_debt.csv")
    assert max(r["year"] for r in fpp) == 2024
    assert next(r for r in weo if r["year"] == 2026)["debt_pct_gdp"] is None
    assert next(r for r in weo if r["year"] == 2026)["debt_pct_gdp_proj"] == 41.8
    assert next(r for r in weo if r["year"] == 2025)["debt_pct_gdp"] == 39.2
    text = (ROOT / "plates.py").read_text(encoding="utf-8")
    assert "FPP December 2025 primary" in text
    assert 'debt_pct_gdp_proj' not in text
    assert 'balance_pct_gdp_proj' not in text


def test_market_rate_is_inverted_and_policy_mean_is_not_year_end():
    fx = {r["year"]: r["mdl_per_usd_annual_avg"]
          for r in _rows("markets/usd_mdl.csv")}
    strength = fx[2006] / fx[2025] * 100
    assert strength == pytest.approx(75.60, abs=0.03)
    policy = {r["year"]: r for r in _rows("markets/policy.csv")}
    assert policy[2025]["policy_mean_pct"] == pytest.approx(6.134247)
    assert policy[2025]["policy_dec31_pct"] == 5
    src = (ROOT / "plates.py").read_text(encoding="utf-8")
    assert "ctx.fx_index(exchange)" in src
    assert '"policy_mean_pct"' in src


def test_bns_functional_cash_budget_is_distinct_from_fpp_fiscal_spine():
    src = (ROOT / "plates.py").read_text(encoding="utf-8")
    fiscal = src.split("def plate_fiscal(", 1)[1].split("def plate_spending(", 1)[0]
    spending = src.split("def plate_spending(", 1)[1].split("def plate_trade(", 1)[0]
    # The national cash budget is now used ONLY for the spending classification,
    # paired with same-territory BNS nominal-MDL GDP, never IMF fiscal panels.
    assert 'fiscal/public_budget.csv' not in fiscal
    assert 'fiscal/nominal_gdp_bns.csv' not in fiscal
    assert '_series(ctx, "fiscal/public_budget.csv"' in spending
    assert '_series(ctx, "fiscal/nominal_gdp_bns.csv"' in spending
    assert 'ig.slot("spending.by_function"' in spending
    assert 'ig.slot("spending.social_protection"' in spending
    assert '_pending(ctx, ig, ax,' in spending  # Government GFCF still unavailable.


def test_national_budget_function_grouping_and_matched_nominal_gdp():
    budget = {r["year"]: r for r in _rows("fiscal/public_budget.csv")}
    gdp = {r["year"]: r["gdp_mdl_mn"]
           for r in _rows("fiscal/nominal_gdp_bns.csv")}
    assert sorted(budget) == sorted(gdp) == list(range(2016, 2026))
    functions = (
        "general_services_mdl_mn", "defense_mdl_mn", "public_order_mdl_mn",
        "economic_affairs_mdl_mn", "environment_mdl_mn", "housing_mdl_mn",
        "health_mdl_mn", "culture_mdl_mn", "education_mdl_mn",
        "social_protection_mdl_mn",
    )
    for year in sorted(gdp):
        assert gdp[year] > 0
        row = budget[year]
        assert sum(row[k] for k in functions) == pytest.approx(
            row["expenditure_mdl_mn"], abs=1.1)
        total = 100 * row["expenditure_mdl_mn"] / gdp[year]
        social = 100 * row["social_protection_mdl_mn"] / gdp[year]
        assert 0 < social < total < 65
        assert total-social < 45
    # Independently cross-checked with BNS Finance own GDP-ratio presentation.
    assert round(100 * budget[2024]["expenditure_mdl_mn"] / gdp[2024], 1) == 38.0
    assert round(100 * budget[2025]["expenditure_mdl_mn"] / gdp[2025], 1) == 39.6
    assert gdp[2023] == pytest.approx(303554.038)
    assert gdp[2024] == pytest.approx(323932.494)
    assert gdp[2025] == pytest.approx(353520.9)


def test_private_credit_lens_does_not_fill_household_slots():
    """A verified broad-sector context lens is not a household debt series."""
    rows = _rows("credit/private_credit.csv")
    assert [r["year"] for r in rows] == list(range(2006, 2026))
    assert [r["year"] for r in rows if r["private_credit_pct_gdp"] is None] == [2006, 2007, 2008, 2009]
    assert next(r for r in rows if r["year"] == 2025)["private_credit_pct_gdp"] == pytest.approx(33.593935)
    content = (ROOT / "plates.py").read_text("utf-8")
    credit = content.split("def plate_credit(", 1)[1].split("def plate_people(", 1)[0]
    assert credit.count("_pending(ctx, ig, ax,") == 2
    assert '"credit/prudential_npl.csv"' in credit
    assert "release_2022_2023_pct" in credit
    assert "release_2024_2025_pct" in credit
    assert all(tag in credit for tag in ("credit.household_debt", "credit.lending_rate", "credit.npl", "credit.lens"))
    assert "credit/private_credit.csv" in credit
    assert "NOT households" in credit

def test_world_hdi_and_ti_cpi_use_distinct_verified_source_vintages():
    rows = _rows("world/hdi.csv")
    assert [r["year"] for r in rows] == list(range(2006, 2026))
    observed = {r["year"]: r["hdi"] for r in rows if r["hdi"] is not None}
    assert list(observed) == list(range(2006, 2024))
    assert observed[2022] == pytest.approx(0.784)
    assert observed[2023] == pytest.approx(0.785)
    assert all(spine.SLOTS["world.hdi"].ref[0] <= v <=
               spine.SLOTS["world.hdi"].ref[1] for v in observed.values())
    plate = (ROOT / "plates.py").read_text(encoding="utf-8")
    world = plate.split("def plate_world(", 1)[1].split("def plate_demography(", 1)[0]
    assert '_series(ctx, "world/hdi.csv", "hdi")' in world
    before_cpi = world.split('ig.slot("world.cpi"', 1)[0]
    assert '"UNDP HDR 2025 CSV' in before_cpi
    assert '_pending(ctx, ig, ax,' not in before_cpi
    cpi = world.split('ig.slot("world.cpi"', 1)[1].split('ig.slot("world.reserves"', 1)[0]
    assert '_series(ctx, "world/cpi.csv", "cpi_score")' in cpi
    assert "_pending(ctx, ig, ax," not in cpi
    rows = _rows("world/cpi.csv")
    assert [r["year"] for r in rows] == list(range(2006, 2026))
    assert [r["year"] for r in rows if r["cpi_score"] is None] == list(range(2006, 2012))
    assert [r["year"] for r in rows if r["cpi_score"] is not None] == list(range(2012, 2026))
    assert {r["year"]: r["cpi_score"] for r in rows if r["year"] in (2023, 2024, 2025)} == {2023: 42, 2024: 43, 2025: 42}
    assert all(spine.SLOTS["world.cpi"].ref[0] <= r["cpi_score"] <= spine.SLOTS["world.cpi"].ref[1] for r in rows if r["cpi_score"] is not None)


def test_wdi_life_expectancy_is_period_not_birth_cohort_longevity():
    """WDI SP.DYN.LE00.IN is a synthetic period life table, not observed lifespan."""
    import json
    from pathlib import Path
    source = (ROOT / "plates.py").read_text(encoding="utf-8")
    mortality = source.split("def plate_mortality(", 1)[1].split("def plate_migration(", 1)[0]
    assert '_series(ctx, "mortality/mortality.csv"' in mortality
    label = "WDI period life table; not observed cohort lifespan"
    assert label in mortality
    assert "birth-cohort estimate" not in mortality
    catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
    assert catalog[label] == {
        "ro": "WDI: tabelă de viață pe perioadă, nu durata reală a cohortei",
        "pt": "WDI: tábua de vida de período; não a longevidade da coorte",
    }
    manifest = (ROOT / "SOURCES.yaml").read_text(encoding="utf-8")
    assert "PERIOD life-table estimate" in manifest
    assert "SP.DYN.LE00.IN" in manifest
