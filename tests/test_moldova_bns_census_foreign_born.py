"""Offline original-publisher parsing and source-vintage contracts for BNS 2024 census."""
from __future__ import annotations

import csv
import hashlib
import io
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "countries/moldova/fetch/fetch_bns_census_foreign_born.py"
spec = importlib.util.spec_from_file_location("moldova_bns_census_snapshot", PATH)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def html_fixture(count="106.7", share="4.4", date="25.08.2025",
                 reference="April 8, 2024", noun="persons born in other countries"):
    return (f"""<!doctype html><html><body><h1>National Bureau of Statistics</h1>
        <p>{date}</p><p>Reference date: {reference}</p>
        <p>According to the census, <b>{noun}</b> – <strong>{count}</strong>
        thousand persons (or <b>{share}%</b> of the population).</p>
        </body></html>""").encode("utf-8")


def test_exact_single_census_statement_and_blanks_not_annual_interpolation():
    year, percentage = audit.parse_official_page(html_fixture())
    assert (year, percentage) == (2024, 4.4)
    raw_sha = hashlib.sha256(html_fixture()).hexdigest()
    body = audit.review_csv(year, percentage, raw_sha)
    assert raw_sha in body and audit.URL in body
    rows = list(csv.DictReader(x for x in io.StringIO(body)
                               if not x.startswith("#")))
    assert len(rows) == 20
    assert [int(x["year"]) for x in rows] == list(range(2006, 2026))
    assert [(int(x["year"]), x["foreign_born_pct"]) for x in rows
            if x["foreign_born_pct"]] == [(2024, "4.4")]
    assert "NOT" not in body  # no request for a national registration series


@pytest.mark.parametrize("kwargs", [
    {"count": "104.6"}, {"share": "5.5"}, {"date": "25.08.2026"},
    {"reference": "April 8, 2025"},
    {"noun": "persons with foreign citizenship"},
])
def test_fails_closed_on_wrong_publisher_definition_or_vintage(kwargs):
    with pytest.raises(ValueError):
        audit.parse_official_page(html_fixture(**kwargs))


def test_rejects_invalid_sidecar_digest_or_modified_figures():
    for args in [(2025, 4.4, "a"*64), (2024, 4.6, "b"*64),
                 (2024, 4.4, "bogus")]:
        with pytest.raises(ValueError):
            audit.review_csv(*args)


def test_quoted_publisher_url_and_no_write_back_to_curated_census():
    code = PATH.read_text(encoding="utf-8")
    assert "foreign_born_census_from_bns.csv" in code
    assert "foreign_born_census.csv" not in code.replace(
        "foreign_born_census_from_bns.csv", "")
    assert "country.yaml" not in code.replace(
        "never overwrite curated data, plates or country.yaml.", "")
    assert "2024-04-08" in code and "2025-08-25" in code
