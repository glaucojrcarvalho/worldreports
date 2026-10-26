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


def test_spine_range_conflict_preserved_not_clipped_or_discarded():
    rows = _rows("trade/trade.csv")
    balance = {int(r["year"]): r["exports_pct_gdp"] - r["imports_pct_gdp"]
               for r in rows}
    lo, hi = spine.SLOTS["trade.balance"].ref
    assert min(balance.values()) < lo, "Re-evaluate the exception if shared spine changes"
    assert balance[2008] == pytest.approx(-52.777445, abs=0.03)
    assert balance[2025] == pytest.approx(-29.162309, abs=0.03)
    # The draft draws every year in a separate lens instead of altering
    # the comparison scale or cropping only the difficult first years.
    text = (ROOT / "plates.py").read_text(encoding="utf-8")
    assert 'ig.slot("trade.balance"' in text
    assert 'ig.slot("trade.lens"' in text
    assert "Full trade balance, untruncated" in text


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


def test_bns_cash_budget_is_not_used_in_fpp_gdp_spine():
    src = (ROOT / "plates.py").read_text(encoding="utf-8")
    # Only an explicit pending explanation may mention the cash budget.
    assert '_series(ctx, "fiscal/public_budget.csv"' not in src
    assert 'ig.slot("spending.by_function"' in src
    assert 'ctx.pending(ax)' in src
