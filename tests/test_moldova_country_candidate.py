"""Non-published Moldova country identity draft QA.

The canonical registry reads ONLY countries/*/country.yaml. Moldova
cannot join it until the Romanian number style/MDL formatting, the
translated plates and site pages, source provenance and global test suite
are complete. This test prevents premature 'country registered' claims.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COUNTRY = ROOT / "countries/moldova"
DRAFT = COUNTRY / "research/country_candidate.yaml"


def test_country_candidate_is_complete_identity_but_not_registered() -> None:
    draft = yaml.safe_load(DRAFT.read_text(encoding="utf-8"))
    assert not (COUNTRY / "country.yaml").exists(), "Do not register partial Moldova atlas"
    assert draft["slug"] == "moldova"
    assert draft["flag_emoji"] == "🇲🇩"
    assert draft["currency"]["code"] == "MDL"
    assert draft["default_locale"] == "ro"
    assert draft["years"] == {"from": 2006, "to": 2026}
    assert draft["last_full_year"] == 2025
    assert draft["tick_every"] == 2
    assert draft["spine"] is True
    assert draft["bands"] == [], "Quarterly recession dating must be evidenced"


def test_locales_cover_ro_en_pt_and_country_switcher_names() -> None:
    draft = yaml.safe_load(DRAFT.read_text(encoding="utf-8"))
    locale_codes = [entry["code"] for entry in draft["locales"]]
    assert locale_codes == ["ro", "en", "pt"]
    assert [x["og_locale"] for x in draft["locales"]] == ["ro_MD", "en_US", "pt_BR"]
    for section in ("title", "description"):
        assert set(draft["seo"][section]) == set(locale_codes)
    assert set(draft["sources"]) == set(locale_codes)
    for lang in ("ro", "en", "pt", "fr", "es", "ko", "it", "he",
                 "ja", "zh-Hans", "zh-Hant", "vi", "de", "uk", "pl", "ru"):
        assert draft["name"].get(lang)
    assert draft["number_style"] == {"ro": "ro"}


def test_candidate_chart_and_web_palette_have_all_required_contracts() -> None:
    from core.country import Palette
    draft = yaml.safe_load(DRAFT.read_text(encoding="utf-8"))
    palette = draft["palette"]
    assert set(Palette.REQUIRED).issubset(palette)
    assert len(palette["flag_bands"]) == 3
    assert len(palette["series"]) >= 5
    assert len(set(palette["flag_bands"])) == 3
    assert {"ground", "raised", "raised_2", "rule", "ink", "muted",
            "faint", "money", "world", "people", "mark_bearing"}.issubset(palette["web"])
    assert "DATA_NOTES.md" in draft["seo"]["spatial"]
