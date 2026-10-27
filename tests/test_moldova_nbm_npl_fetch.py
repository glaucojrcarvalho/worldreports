"""Offline parser and fail-closed contracts for original NBM bank NPL bulletins."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "countries/moldova"
path = ROOT / "fetch/fetch_nbm_npl.py"
spec = importlib.util.spec_from_file_location("moldova_nbm_npl_source", path)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_original_year_end_report_phrasing_and_decimals():
    examples = {
        2022: "During the reference period, the share of non-performing loans (substandard, doubtful and compromised) in total loans increased by 0.3 pp, accounting for 6.4% on 31.12.2022, across banks.",
        2023: "During the reference period, the share of non-performing loans (substandard, doubtful, and compromised) in total loans decreased by 0,9 pp, accounting for 5,6% on 31.12.2023.",
        2024: "During the reference period, the share of non-performing loans (substandard, doubtful and compromised) in total loans decreased by 1,4 p.p. accounting for 4,1% as of 31 December 2024, by bank.",
        2025: "The share of non-performing loans in total loans (prudential) as of 31 December 2025, was 4.1%, unchanged from end of the previous year.",
    }
    for year, example in examples.items():
        raw = ("<html><head><script>share of non-performing loans: 99.9%</script></head>"
               "<body><p>" + example + "</p></body></html>").encode()
        assert audit.extract_npl(audit.visible_text(raw), year) == audit.EXPECTED[year]


def test_source_guard_detects_missing_year_change_and_duplicate():
    normal = ("The share of non-performing loans in total loans (prudential)"
              " as of 31 December 2025, was 4.1%.")
    with pytest.raises(ValueError, match="expected one"):
        audit.extract_npl(normal, 2024)
    with pytest.raises(ValueError, match="changed ratio"):
        audit.extract_npl(normal.replace("4.1%", "4.5%"), 2025)
    with pytest.raises(ValueError, match="expected one"):
        audit.extract_npl(normal + " " + normal, 2025)
    with pytest.raises(ValueError, match="not among"):
        audit.extract_npl(normal, 2026)
    with pytest.raises(ValueError, match="oversized"):
        audit.visible_text(b"x" * (audit.MAX_BYTES + 1))


def test_source_audit_writes_only_review_sidecar():
    assert set(audit.PAGES) == set(audit.EXPECTED) == {2022, 2023, 2024, 2025}
    assert all(url.startswith("https://bnm.md/") for url in audit.PAGES.values())
    assert audit.OUTPUT.name == "prudential_npl_from_nbm.csv"
    assert audit.EVIDENCE.name.endswith("_source_evidence.json")
    assert audit.OUTPUT != ROOT / "data/credit/prudential_npl.csv"
    rendered = audit.render_review(audit.EXPECTED)
    assert "2006,," in rendered and "2022,6.4," in rendered
    assert "2023,5.6," in rendered and "2024,,4.1" in rendered
    assert "2025,,4.1" in rendered
    with pytest.raises(ValueError, match="Unreviewed"):
        audit.render_review({2025: 4.1})
