"""Offline verification of source-defined BNS LFS annual breaks and parsing."""
import csv
from io import StringIO

import pytest

from countries.moldova.fetch import fetch_bns_lfs_annual as src
from countries.moldova.fetch import fetch_bns_lfs as meta


def source_codebook():
    return [
        {"code": "Sexe", "name": "Sex",
         "categories": [{"code": "0", "label": "Both sexes"},
                        {"code": "1", "label": "Men"}]},
        {"code": "Medii", "name": "Area",
         "categories": [{"code": "0", "label": "Whole country"},
                        {"code": "1", "label": "Urban"}]},
        {"code": "Ani", "name": "Years",
         "categories": [{"code": str(y), "label": str(y)}
                        for y in meta.YEARS]},
        {"code": "Trimestre", "name": "Quarters",
         "categories": [{"code": "0", "label": "Annual average"},
                        {"code": "1", "label": "Quarter I"}]},
    ]


def responses():
    query, chosen, years = src.selection(source_codebook())
    cube = {
        "class": "dataset",
        "id": ["Trimestre", "Ani", "Medii", "Sexe"],
        "size": [1, 7, 1, 1],
        "dimension": {
            "Trimestre": {"category": {"index": {"0": 0}}},
            "Ani": {"category": {"index": {str(y): i for i, y in
                                           enumerate(meta.YEARS)}}},
            "Medii": {"category": {"index": {"0": 0}}},
            "Sexe": {"category": {"index": {"0": 0}}},
        },
        "value": [5.1, 3.8, 3.2, 2.3, 4.6, 4.0, 3.8],
    }
    return query, chosen, years, cube


def test_exact_annual_categories_and_2025_separated_from_previous_regime():
    q, chosen, labels, cube = responses()
    assert [d["code"] for d in q["query"]] == [
        "Sexe", "Medii", "Ani", "Trimestre"]
    assert chosen["Sexe"] == ["0"] and chosen["Medii"] == ["0"]
    assert chosen["Trimestre"] == ["0"]
    assert chosen["Ani"] == [str(y) for y in meta.YEARS]
    readings = src.decode(cube, chosen, labels)
    assert readings[2025] == 3.8 and len(readings) == 7
    txt = src.sidecar(readings, "https://official.example/source", "a"*64, "b"*64)
    rows = list(csv.DictReader(StringIO("\n".join(
        x for x in txt.splitlines() if not x.startswith("#")))))
    assert rows[-2] == {"year": "2024", "bns_lfs_2019_2024_pct": "4.0",
                        "bns_lfs_2025_pct": ""}
    assert rows[-1] == {"year": "2025", "bns_lfs_2019_2024_pct": "",
                        "bns_lfs_2025_pct": "3.8"}
    assert "NOT harmonised WDI" in txt and "2024 census" in txt
    assert str(src.OUT).endswith("national_lfs_from_bns.csv")


def test_reject_wrong_category_and_source_vintage():
    dims = source_codebook()
    dims[0]["categories"][0]["label"] = "Adult men"
    with pytest.raises(ValueError, match="Both sexes"):
        src.selection(dims)
    q, chosen, years, cube = responses()
    cube["value"][-1] = 8.9
    with pytest.raises(ValueError, match="independent published"):
        src.decode(cube, chosen, years)


def test_reject_dimension_order_mismatch_missing_and_nan():
    q, chosen, years, cube = responses()
    cube["id"] = ["Trimestre", "Ani", "Medii", "Unknown"]
    with pytest.raises(ValueError, match="grid"):
        src.decode(cube, chosen, years)
    q, chosen, years, cube = responses()
    cube["value"][4] = None
    with pytest.raises(ValueError, match="Invalid BNS"):
        src.decode(cube, chosen, years)
    q, chosen, years, cube = responses()
    cube["value"] = {str(i): v for i, v in enumerate(cube["value"])}
    cube["value"].pop("3")
    with pytest.raises(ValueError, match="Invalid BNS"):
        src.decode(cube, chosen, years)
