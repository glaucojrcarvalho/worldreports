"""Offline WDI private-credit provenance and scope, distinct from household debt."""
from __future__ import annotations
import csv
from pathlib import Path
import pytest
import yaml
ROOT = Path(__file__).resolve().parent.parent / 'countries/moldova'
def test_verified_wdi_credit_years_and_blanks():
    content = (ROOT / 'data/credit/private_credit.csv').read_text('utf-8')
    rows = list(csv.DictReader(x for x in content.splitlines() if x and not x.startswith('#')))
    assert [int(r['year']) for r in rows] == list(range(2006, 2026))
    assert list(rows[0]) == ['year', 'private_credit_pct_gdp']
    observed = {int(r['year']): float(r['private_credit_pct_gdp']) for r in rows if r['private_credit_pct_gdp']}
    assert list(observed) == list(range(2010, 2026))
    assert observed[2010] == pytest.approx(29.497046, abs=1e-6)
    assert observed[2024] == pytest.approx(29.333210, abs=1e-6)
    assert observed[2025] == pytest.approx(33.593935, abs=1e-6)
    assert all(0 < val < 100 for val in observed.values())
    assert 'lastupdated=2026-10-08' in content
def test_wdi_credit_manifest_and_refresh_contract():
    source = yaml.safe_load((ROOT / 'SOURCES.yaml').read_text('utf-8'))
    entry = source['credit']['private_credit.csv']
    assert entry['official'] is False
    assert entry['refreshed_by'] == 'fetch/fetch_wdi.py'
    assert 'FS.AST.PRVT.GD.ZS' in entry['url']
    assert 'NOT household-only' in entry['notes']
    from importlib import util
    spec = util.spec_from_file_location('md_credit_wdi', ROOT / 'fetch/fetch_wdi.py')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.GROUPS['credit/private_credit.csv'] == (('private_credit_pct_gdp', 'FS.AST.PRVT.GD.ZS'),)
