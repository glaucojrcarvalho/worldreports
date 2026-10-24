"""Render research-stage Ukraine plots in an isolated synthetic country.

This exercises core.render, Context, Infographic and the fixed spine without
registering incomplete Ukraine in the public country catalog. Rendering
uses ONLY the committed reviewed CSVs; no network requests are made.

Test market FX and whole-economy GFCF, which fit the existing shared scales.
The unmodified shared GDP growth / trade-balance ranges cannot yet
accommodate Ukraine's observed 2022/2024 extremes. Those chapters must
NOT be clipped or silently replotted until the peer-wide scale decision.
"""
from __future__ import annotations

import shutil

import matplotlib
matplotlib.use("Agg")
import pytest
import yaml

from core import context, i18n, render
from core.country import Country

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = (
    "markets/fx.csv",
    "spending/investment.csv",
    "macro/reserves.csv",
)


@pytest.fixture
def isolated_country(tmp_path):
    home = tmp_path / "ukraine"
    home.mkdir()
    palette = {
        "ink": "#151515", "muted": "#5a6170", "faint": "#9296a0",
        "paper": "#faf9f5", "card": "#ffffff", "grid": "#e6e3db",
        "spine": "#c6c1b7", "band": "#e9e5db", "primary": "#1b5e9a",
        "BLUE": "#1b5e9a", "RED": "#ac3030", "GREEN": "#327751",
        "alert": "#ac3030",
        "series": ["#1b5e9a", "#ac3030", "#e9bc39"],
        "flag_bands": ["#155ca3", "#f6c846", "#155ca3"],
    }
    country = {
        "slug": "ukraine", "name": {"en": "Ukraine"},
        "flag_emoji": "🇺🇦",
        "locales": [{"code": "en", "endonym": "English"}],
        "default_locale": "en",
        "years": {"from": 2006, "to": 2026},
        "last_full_year": 2025, "tick_every": 2,
        "bands": [{"from": 2022, "to": 2024, "label": "Full-scale invasion"}],
        "currency": {"code": "UAH"}, "palette": palette,
        "seo": {"title": {"en": "Test fixture"}, "description": {"en": "Only tests"},
                "keywords": ["test"], "spatial": "Ukraine"},
        "spine": True,
    }
    (home / "country.yaml").write_text(
        yaml.safe_dump(country, allow_unicode=True), encoding="utf-8")
    shutil.copy2(ROOT / "plates.py", home / "plates.py")
    for dataset in DATASETS:
        target = home / "data" / dataset
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "data" / dataset, target)
    return Country.from_dir(home)


@pytest.mark.parametrize("topic", ["markets", "spending", "world"])
def test_accepted_source_panel_can_be_rendered_offline(isolated_country, topic, tmp_path):
    i18n.bind(isolated_country)
    i18n.set_lang("en")
    ctx = context.Context(isolated_country, out_dir=tmp_path / "generated")
    try:
        plates = [p for p in render.load_plates(isolated_country)
                  if p.topic == topic]
        assert len(plates) == 1
        render.draw(ctx, plates[0])
        path = tmp_path / "generated" / plates[0].filename
        assert path.is_file(), f"{topic}: no rendered plate"
        assert path.stat().st_size > 5000, f"{topic}: unexpectedly empty plate"
    finally:
        i18n.set_lang("en")


def test_missing_ukraine_full_atlas_remains_unregistered():
    assert not (ROOT / "country.yaml").exists()
    assert (ROOT / "data" / "macro" / "gdp_growth.csv").is_file()
