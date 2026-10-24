"""Ukrainian reusable number style, currency and chart-font integration.

Run with atlas dependencies installed:
  python -m pytest countries/ukraine/integration/test_uk_locale.py -q

Country is intentionally not registered until its datasets and plates
pass the full atlas acceptance gates.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from core import i18n, numstyle, style
from core.sitebuild import AFFIX, CURRENCY_AFFIX, SiteContext


@pytest.fixture
def ctx():
    c = SimpleNamespace(
        slug="synthetic",
        currency="UAH",
        locale_codes=("en", "uk", "pt"),
        last_full_year=2025,
        number_style=lambda code: code,
    )
    return SiteContext(c)


def test_Ukrainian_numbers_use_decimal_comma_and_group_space():
    n = numstyle.NBSP
    assert numstyle.STYLES["uk"] == "uk"
    assert numstyle.swap("1,234.5", "uk") == f"1{n}234,5"
    assert numstyle.swap("20.2", "uk") == "20,2"
    assert numstyle.swap("2006", "uk") == "2006"
    assert numstyle.swap("2006–2026", "uk") == "2006–2026"
    assert i18n.localize_numbers("12.5%", "uk") == f"12,5{n}%"


def test_all_language_numeric_specs_have_Ukrainian_forms():
    for spec, by_style in AFFIX.items():
        assert "uk" in by_style, spec


def test_hryvnia_affixes_and_native_portuguese_numbers(ctx):
    n = numstyle.NBSP
    assert "money_bn" in CURRENCY_AFFIX["UAH"]
    assert ctx.render(7662, "money_bn") == {
        "en": "₴7,662bn",
        "uk": f"7{n}662{n}млрд грн",
        "pt": "₴ 7.662 bi",
    }
    assert ctx.render(12.7, "pct")["uk"] == f"12,7{n}%"
    assert ctx.render(-28.8, "pct_gdp_s")["uk"] == f"-28,8{n}% ВВП"


def test_Ukrainian_plate_currency_and_usd_labels():
    n = numstyle.NBSP
    assert "uk" in i18n._UNITS
    assert i18n.localize_numbers("₴ 2,991bn", "uk") == f"2{n}991{n}млрд{n}грн"
    assert i18n.localize_numbers("US$ 684bn", "uk") == f"684{n}млрд{n}дол. США"
    assert i18n.is_value_label("₴ 2,991bn")


def test_Ukrainian_can_render_Cyrillic_without_noto_minus_gap():
    assert style.has_script_font("uk")
    assert style.body_font("uk") == "DejaVu Sans"
