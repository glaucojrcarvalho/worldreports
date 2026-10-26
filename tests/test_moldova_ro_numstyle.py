"""Romanian formatting and Moldovan leu contract, before country activation.

The atlas has not registered Moldova in Country.all() yet. This suite
exercises the SAME shared renderer with the candidate configuration in a
temporary directory and pins page/plate values explicitly. No changes to
other published countries or their data are needed.

For ro-MD, CLDR: 1.234.567,89 and a space before currency and percent.
Pages choose the human-readable word 'lei' instead of the shorter 'L'
symbol to disambiguate this currency on mixed-country comparisons.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from core import i18n, numstyle
from core.country import Country
from core.sitebuild import AFFIX, CURRENCY_AFFIX, NUMFMT, SiteContext, format_figure

NBSP = numstyle.NBSP
ROOT = Path(__file__).resolve().parent.parent
CANDIDATE = ROOT / "countries/moldova/research/country_candidate.yaml"


def card(style: str, spec: str, value: float, currency: str | None = None) -> str:
    source = AFFIX if currency is None else CURRENCY_AFFIX[currency]
    prefix, suffix = source[spec][style]
    return format_figure(value, spec, style, prefix, suffix)


def test_romania_number_style_is_shared_by_page_and_plate() -> None:
    assert numstyle.STYLES["ro"] == "ro"
    assert numstyle.SEPARATORS["ro"] == {",": ".", ".": ","}
    assert i18n._SEPARATORS is numstyle.SEPARATORS
    assert numstyle.swap("1,234,567.89", "ro") == "1.234.567,89"
    assert i18n.swap_separators("1,234,567.89", "ro") == "1.234.567,89"
    assert i18n.localize_numbers("2006–2026", "ro") == "2006–2026"
    assert i18n.localize_numbers("12.5%", "ro") == f"12,5{NBSP}%"


@pytest.mark.parametrize("spec,value,expected", [
    ("pct_gdp", 12.5, f"12,5{NBSP}% din PIB"),
    ("pct", 12.5, f"12,5{NBSP}%"),
    ("dec2", 1234.567, "1.234,57"),
    ("rank", 24, "locul 24"),
    ("usd_bn", 684.4, f"684{NBSP}mld.{NBSP}USD"),
    ("money_bn", 291.4, f"291{NBSP}mld.{NBSP}lei"),
    ("money_bn", 1101.3, f"1,10{NBSP}bln.{NBSP}lei"),
])
def test_romania_card_is_written_natively(spec: str, value: float,
                                          expected: str) -> None:
    currency = "MDL" if spec.startswith("money") else None
    assert card("ro", spec, value, currency) == expected


@pytest.mark.parametrize("english,expected", [
    ("MDL 1,234bn", f"1.234{NBSP}mld.{NBSP}lei"),
    ("MDL 1,234", f"1.234{NBSP}lei"),
    ("US$ 684bn", f"684{NBSP}mld.{NBSP}USD"),
    ("12.5%", f"12,5{NBSP}%"),
    ("+0.3pp", f"+0,3{NBSP}p.p."),
    ("2006", "2006"),
    ("2024-2025", "2024-2025"),
])
def test_romania_plate_labels_use_same_separators_and_units(
        english: str, expected: str) -> None:
    assert i18n.localize_numbers(english, "ro") == expected


def test_romanian_mdl_has_forms_for_all_three_candidate_languages() -> None:
    specs = CURRENCY_AFFIX["MDL"]
    for spec in ("money_bn", "money_tn", "money", "money2"):
        assert {"ro", "en", "pt"} <= set(specs[spec])
        assert spec in NUMFMT
    assert card("en", "money_bn", 291.4, "MDL") == "MDL 291bn"
    assert card("pt", "money_bn", 291.4, "MDL") == "MDL 291 bi"
    assert card("ro", "money", 12345, "MDL").endswith(f"12.345{NBSP}lei")
    assert i18n.is_value_label("MDL 1,234bn")


def test_every_ro_general_number_spec_and_plate_rules_exist() -> None:
    assert all("ro" in affix for affix in AFFIX.values())
    assert "ro" in i18n._UNITS


def test_candidate_can_be_loaded_and_formatted_without_registration(tmp_path: Path) -> None:
    assert not (CANDIDATE.parent.parent / "country.yaml").exists()
    tmp_country = tmp_path / "moldova"
    tmp_country.mkdir()
    shutil.copyfile(CANDIDATE, tmp_country / "country.yaml")
    country = Country.from_dir(tmp_country)
    assert country.number_style("ro") == "ro"
    assert country.currency == "MDL"
    assert [lang.code for lang in country.locales] == ["ro", "en", "pt"]
    ctx = SiteContext(country)
    expected = {
        "ro": f"12,5{NBSP}% din PIB",
        "en": "12.5% GDP",
        "pt": "12,5% do PIB",
    }
    assert ctx.render(12.5, "pct_gdp") == expected
    prices = ctx.render(291.4, "money_bn")
    assert prices == {
        "ro": f"291{NBSP}mld.{NBSP}lei",
        "en": "MDL 291bn",
        "pt": "MDL 291 bi",
    }
