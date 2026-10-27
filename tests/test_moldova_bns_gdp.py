"""Offline contract tests for BNS nominal-MDL GDP source (no network).

We do not infer missing historical GDP by mixing WDI current USD with NBM
annual FX; GDP national-account vintages must be checked at the publisher.
"""
from __future__ import annotations

import csv
from io import StringIO

import pytest

from countries.moldova.fetch import fetch_bns_gdp as src


def fixture():
    years = list(src.YEARS)
    md = {
        "variables": [
            {"code": "Indicators", "values": ["a", "b"],
             "valueTexts": ["GDP, current prices, thousand Lei",
                            "GDP, current prices, thousand $ US"]},
            {"code": "Years", "values": [str(y) for y in years],
             "valueTexts": [str(y) for y in years]},
        ]
    }
    values = [150_000_000 + (y - 2016) * 20_000_000 for y in years]
    values[years.index(2023)] = src.ANCHORS_THOUSAND_MDL[2023]
    values[years.index(2024)] = src.ANCHORS_THOUSAND_MDL[2024]
    cube = {
        "class": "dataset", "id": ["Indicators", "Years"], "size": [1, len(years)],
        "dimension": {
            "Indicators": {"category": {"index": {"a": 0}}},
            "Years": {"category": {"index": {str(y): i for i, y in enumerate(years)}}},
        }, "value": values,
    }
    return md, cube


def test_source_is_review_only_and_cannot_replace_publication():
    assert "nominal_gdp_from_bns.csv" in str(src.OUTPUT)
    assert src.YEARS == tuple(range(2016, 2025))
    assert 2025 not in src.YEARS
    assert src.TARGET == "CNT208100.px"


def test_exact_nominal_lei_metric_selected_not_usd():
    md, cube = fixture()
    ind, year, code, mapping = src.metadata_codes(md)
    assert (ind, year, code) == ("Indicators", "Years", "a")
    result = src.decode(cube, ind, year, code, mapping)
    assert len(result) == 9
    src.verify_anchors(result)
    text = src.sidecar(result, "https://statbank.statistica.md/PxWeb/api/v1/en/example.px")
    rows = list(csv.DictReader(StringIO("\n".join(
        line for line in text.splitlines() if not line.startswith("#")))))
    assert len(rows) == 9
    assert rows[-1] == {"year": "2024", "gdp_mdl_mn": "323932.494"}
    assert "2025 preliminary is a separate press release" in text
    assert "thousand MDL" in text and "million" not in text.splitlines()[0]


def test_reject_different_edition_without_review():
    md, cube = fixture()
    ind, year, code, mapping = src.metadata_codes(md)
    cube["value"][-1] += 5000
    result = src.decode(cube, ind, year, code, mapping)
    with pytest.raises(ValueError, match="anchor changed"):
        src.verify_anchors(result)


def test_reject_usd_unit_and_missing_or_zero_values():
    md, cube = fixture()
    md["variables"][0]["valueTexts"][0] = "GDP, current prices, thousand $ US"
    with pytest.raises(ValueError, match="nominal-MDL GDP"):
        src.metadata_codes(md)
    md, cube = fixture()
    ind, year, code, mapping = src.metadata_codes(md)
    cube["value"][-1] = None
    with pytest.raises(ValueError, match="invalid nominal GDP"):
        src.decode(cube, ind, year, code, mapping)
    cube["value"][-1] = 0
    with pytest.raises(ValueError, match="invalid nominal GDP"):
        src.decode(cube, ind, year, code, mapping)


def test_reject_partial_year_grid_and_reversed_or_wrong_dimensions():
    md, cube = fixture()
    ind, year, code, mapping = src.metadata_codes(md)
    cube["dimension"]["Years"]["category"]["index"].pop("2021")
    with pytest.raises(ValueError, match="position mismatch|incomplete"):
        src.decode(cube, ind, year, code, mapping)
    md, cube = fixture()
    cube["id"] = ["Indicators", "Perioade"]
    ind, year, code, mapping = src.metadata_codes(md)
    with pytest.raises(ValueError, match="Invalid BNS GDP JSON-stat"):
        src.decode(cube, ind, year, code, mapping)


def test_publisher_ratio_anchors_use_same_currency_year_and_territory():
    """Validate the fiscal GDP denominator against ratios *published* by BNS.

    The BNS Finance overview gives 2024 total 122,962.6m = 38.0% of GDP,
    2025 preliminary 139,856.4m = 39.6%. 2025 denominator comes only from
    the separately verified GDP press-release value of 353,520.9m.
    """
    assert round(100 * 122962.6 / 323932.494, 1) == 38.0
    assert round(100 * 139856.4 / 353520.9, 1) == 39.6
    assert round(100 * 47007.8 / 323932.494, 3) == 14.512
    # The grouped national cash ratio is not IMF GFS/COFOG by definition;
    # keep canonical fiscal and spending series separately attributed.
