"""Research-only market plate QA for Moldova in Romanian/English/Portuguese.

No publication through Country.all, no live network in tests.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "countries/moldova/research/render_markets_preview.py"
spec = importlib.util.spec_from_file_location("moldova_market_research", MODULE)
assert spec and spec.loader
markets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(markets)


def test_market_inputs_share_complete_calendar_years_and_publishers() -> None:
    dataset = markets.data()
    assert dataset["years"] == list(range(2006, 2026))
    assert dataset["policy"][2025]["policy_mean_pct"] == pytest.approx(6.134247)
    assert dataset["inflation"][2025]["cpi_inflation_pct"] == pytest.approx(7.759041)
    assert dataset["fx"][2025]["mdl_per_usd_annual_avg"] == pytest.approx(17.3705)
    assert dataset["policy"][2025]["policy_dec31_pct"] == 5.0
    assert dataset["policy"][2025]["policy_mean_pct"] != dataset["policy"][2025]["policy_dec31_pct"]


def test_fx_strength_sign_and_baseline() -> None:
    dataset = markets.data()
    assert dataset["strength"][2006] == 100.0
    assert dataset["fx"][2025]["mdl_per_usd_annual_avg"] > dataset["fx"][2006]["mdl_per_usd_annual_avg"]
    # More leu per USD = depreciation = LOW index, never reverse.
    assert dataset["strength"][2025] < 100.0
    expected = (dataset["fx"][2006]["mdl_per_usd_annual_avg"] /
                dataset["fx"][2025]["mdl_per_usd_annual_avg"]) * 100.0
    assert dataset["strength"][2025] == pytest.approx(expected, abs=1e-12)
    assert dataset["strength"][2025] == pytest.approx(75.598859, abs=.01)


def test_research_catalog_three_complete_locales_with_missing_panels() -> None:
    translated = markets.catalog()
    assert set(translated) == {"ro", "en", "pt"}
    for locale, t in translated.items():
        assert set(t) == markets.REQUIRED_STRINGS
        assert "{" not in t["pending_bond"] and "{" not in t["pending_equity"]
        assert "{rate}" in t["fx_latest"]
        assert t["pending"] != t["p1"]
    assert "piațe" in translated["ro"]["title"]
    assert "policy" in translated["en"]["title"]
    assert "mercados" in translated["pt"]["title"]


def test_catalog_strictly_refuses_missing_translation(tmp_path: Path, monkeypatch) -> None:
    current = json.loads(markets.CATALOG.read_text(encoding="utf-8"))
    current["ro"].pop("pending_equity")
    bad = tmp_path / "catalog.json"
    bad.write_text(json.dumps(current), encoding="utf-8")
    monkeypatch.setattr(markets, "CATALOG", bad)
    with pytest.raises(ValueError, match="ro: missing"):
        markets.catalog()


def test_invalid_source_year_grid_refuses_to_plot(tmp_path: Path) -> None:
    source = markets.SOURCES["fx"][0]
    raw = source.read_text(encoding="utf-8")
    # Cut one known middle year: it must raise rather than graph a smooth splice.
    cut = "\n".join(line for line in raw.splitlines()
                    if not line.startswith("2018,")) + "\n"
    broken = tmp_path / "fx.csv"
    broken.write_text(cut, encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete"):
        markets.get_year_rows(broken, ("mdl_per_usd_annual_avg",))


@pytest.mark.parametrize("locale", ["ro", "en", "pt"])
def test_market_preview_three_languages_is_reproducible_no_input_write(
        locale: str, tmp_path: Path) -> None:
    before = {key: path.read_bytes() for key, (path, _) in markets.SOURCES.items()}
    out = tmp_path / f"{locale}.png"
    assert markets.draw(locale, out) == out
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert out.stat().st_size > 45_000
    for key, (path, _) in markets.SOURCES.items():
        assert path.read_bytes() == before[key]


def test_comparator_panels_are_not_faked_by_other_datasets() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert 'pending(axes[0, 1]' in source
    assert 'pending(axes[1, 1]' in source
    assert "10-year" in source
    # Exchange-rate strength is an INDEX, not a literal MDL-per-USD quote.
    assert '100.0 * fx[2006]' in source
    assert '"inflation": (COUNTRY / "data/macro/economy.csv"' in source
    # No research preview script may import a different country's CSV.
    assert "countries/ukraine" not in source
