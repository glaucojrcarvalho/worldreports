"""Unit tests for Moldova BNS FIN010100 data-structure and budget gates.

The HTTP POST is deliberately mocked. This tests that a complete-year
million-MDL dataset is selected and decoded without assuming response order.
No publication, API credentials or network connection is required.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "countries/moldova/fetch/fetch_bns_budget.py"
spec = importlib.util.spec_from_file_location("moldova_bns_budget", SCRIPT)
assert spec is not None and spec.loader is not None
bns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bns)
META = json.loads(bns.METADATA_SNAPSHOT.read_text("utf-8"))


def test_verified_category_codebook() -> None:
    mapping = bns.validate_metadata(META)
    assert mapping["Indicatori"]["0"] == "Revenues"
    assert mapping["Indicatori"]["19"] == "Expenditures and non-financial assets"
    assert mapping["Indicatori"]["30"] == "Surplus (+), deficit (-)"
    assert mapping["Perioade"]["3"] == "January-December"
    assert mapping["Unitatea de masura"]["0"] == "Million lei"
    assert len(bns.INDICATORS) == 13
    assert len(bns.FUNCTIONS) == 10


def test_query_excludes_ytd_partial_and_double_counted_revenue_children() -> None:
    query = bns.query(bns.validate_metadata(META))
    dims = {q["code"]: q["selection"]["values"] for q in query["query"]}
    assert set(dims) == set(bns.VARIABLES)
    assert set(dims["Indicatori"]) == set(bns.INDICATORS)
    assert not any(str(i) in dims["Indicatori"] for i in range(1, 19))
    assert dims["Perioade"] == ["3"]
    assert dims["Unitatea de masura"] == ["0"]
    assert "2026" not in {
        bns.validate_metadata(META)["Ani"][year] for year in dims["Ani"]
    }
    assert len(dims["Ani"]) == 10
    assert query["response"]["format"] == "json-stat2"


def fake_cube() -> tuple[dict, dict[str, str]]:
    mapping = bns.validate_metadata(META)
    selected = bns.query(mapping)["query"]
    codes = {q["code"]: q["selection"]["values"] for q in selected}
    ids = list(bns.VARIABLES)
    dims = {
        key: {"category": {"index": {value: i for i, value in enumerate(codes[key])}}}
        for key in ids
    }
    # BNS source table may return indicators then years. A JSON-stat2
    # reader must use the dimension ID + category index, not hard-coded
    # array position.
    data = []
    for indicator in codes["Indicatori"]:
        for year_code in codes["Ani"]:
            year = int(mapping["Ani"][year_code])
            rev, exp, bal = (
                (110338.5, 122962.6, -12624.1) if year == 2024 else
                (125602.0, 139856.4, -14254.4) if year == 2025 else
                (1000.0, 1200.0, -200.0)
            )
            record = {"0": rev, "19": exp, "30": bal}
            record.update({code: exp / 10 for code in bns.FUNCTIONS})
            data.append(record[indicator])
    return ({
        "class": "dataset", "id": ids, "size": [13, 10, 1, 1],
        "dimension": dims, "value": data,
    }, mapping["Ani"])


def test_cube_decodes_and_reconciles_budget_arithmetic() -> None:
    payload, years = fake_cube()
    annual = bns.decode_jsonstat(payload, years)
    assert set(annual) == set(range(2016, 2026))
    assert annual[2025]["revenue_mdl_mn"] == pytest.approx(125602)
    assert annual[2024]["balance_mdl_mn"] == pytest.approx(-12624.1)
    bns.verify_budget(annual)
    rendered = bns.render(annual)
    rows = list(csv.DictReader(line for line in rendered.splitlines()
                               if not line.startswith("#")))
    assert len(rows) == 10
    assert rows[-1]["year"] == "2025"
    assert rows[-1]["expenditure_mdl_mn"] == "139856.4"


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(size=[13, 9, 1, 1]),
    lambda x: x["dimension"]["Perioade"]["category"]["index"].update({"0": 0}),
    lambda x: x["value"].pop(),
    lambda x: x["value"].__setitem__(0, None),
])
def test_cube_rejects_partial_wrong_period_or_missing_values(mutation) -> None:
    cube, years = fake_cube()
    mutation(cube)
    with pytest.raises(ValueError):
        bns.decode_jsonstat(cube, years)


def test_budget_math_fails_on_broken_totals() -> None:
    cube, years = fake_cube()
    annual = bns.decode_jsonstat(cube, years)
    annual[2024]["balance_mdl_mn"] = -12_000
    with pytest.raises(ValueError, match="identity broken"):
        bns.verify_budget(annual)


def test_fiscal_national_scope_is_not_imf_series() -> None:
    rendered = bns.render(bns.decode_jsonstat(*fake_cube()))
    assert "National public budget cash perimeter" in rendered
    assert "not IMF general-government accrual" in rendered
    assert "left-bank Nistru" in rendered
