"""Offline safety contracts for official BNS EXT010200 partner-goods research."""
from __future__ import annotations

import csv
import importlib.util
import io
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "countries/moldova/fetch/fetch_bns_trade.py"
spec = importlib.util.spec_from_file_location("moldova_bns_trade", SCRIPT)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def synthetic():
    pc, yc = "Tari", "Ani"
    partners = {"0": "Total", "1": "CIS countries", "2": "..Armenia", "3": "Romania"}
    partners.update({str(i): f"Partner {i}" for i in range(4, 89)})
    years = {str(i): str(y) for i, y in enumerate(range(1997, 2026))}
    return {
        "title": "Exports of the Republic of Moldova by countries",
        "variables": [
            {"code": pc, "text": "Countries",
             "values": list(partners), "valueTexts": list(partners.values())},
            {"code": yc, "text": "Years",
             "values": list(years), "valueTexts": list(years.values())},
        ],
    }


def test_metadata_and_query_preserve_all_codes_and_2006_2025_grid():
    pc, yc, countries, years = audit.metadata_codes(synthetic())
    request = audit.query(pc, yc, countries, years)
    assert [row["code"] for row in request["query"]] == [pc, yc]
    assert len(request["query"][0]["selection"]["values"]) == 89
    assert len(request["query"][1]["selection"]["values"]) == 20
    assert request["response"] == {"format": "json-stat2"}
    assert request["query"][1]["selection"]["values"][-1] == "28"  # 2025
    assert "2026" not in years.values()


def cube(reordered=True):
    pc, yc, countries, years = audit.metadata_codes(synthetic())
    selected = audit.query(pc, yc, countries, years)
    years_selected = selected["query"][1]["selection"]["values"]
    dims = [yc, pc] if reordered else [pc, yc]
    sizes = [len(years_selected) if dim == yc else len(countries) for dim in dims]
    dimension = {
        pc: {"category": {"index": {c: i for i, c in enumerate(countries)}}},
        yc: {"category": {"index": {c: i for i, c in enumerate(years_selected)}}},
    }
    values = []
    for left in (years_selected if reordered else countries):
        for right in (countries if reordered else years_selected):
            ycval, pcval = (left, right) if reordered else (right, left)
            yr = int(years[ycval])
            values.append(3782700.0 if pcval == "0" and yr == 2025 else
                          3000000.0 if pcval == "0" else 0.0)
    return ({"class": "dataset", "id": dims, "size": sizes,
             "dimension": dimension, "value": values}, pc, yc, countries, years)


@pytest.mark.parametrize("reordered", [True, False])
def test_decode_dimension_order_and_total_anchor(reordered):
    dataset, pc, yc, partners, years = cube(reordered)
    rows = audit.decode(dataset, pc, yc, partners, years)
    assert len(rows) == 89 * 20
    assert rows[(2025, "0")] == ("Total", 3782700.0)
    audit.verify(rows, partners)
    text = audit.render(rows, partners)
    parsed = list(csv.DictReader(x for x in io.StringIO(text) if not x.startswith("#")))
    assert len(parsed) == 1780
    assert parsed[-1]["year"] == "2025"
    assert "GOODS" in text and "Bender" in text and "Ukraine" in text
    assert "NO country shares or sums" in text


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(size=[19, 89]),
    lambda d: d["value"].pop(),
    lambda d: d["value"].__setitem__(0, -1),
    lambda d: d["value"].__setitem__(0, float("nan")),
    lambda d: d["dimension"]["Ani"]["category"]["index"].pop(next(iter(d["dimension"]["Ani"]["category"]["index"]))),
])
def test_decode_fail_closed_on_incomplete_or_invalid_cells(mutation):
    dataset, pc, yc, partners, years = cube()
    mutation(dataset)
    with pytest.raises(ValueError):
        audit.decode(dataset, pc, yc, partners, years)


def test_rejects_wrong_schema_and_anchor():
    metadata = synthetic()
    metadata["variables"][0]["text"] = "Industries"
    with pytest.raises(ValueError, match="Unrecognized"):
        audit.metadata_codes(metadata)
    dataset, pc, yc, partners, years = cube()
    rows = audit.decode(dataset, pc, yc, partners, years)
    rows[(2025, "0")] = ("Total", 2000000.0)
    with pytest.raises(ValueError, match="diverge"):
        audit.verify(rows, partners)


def test_refuses_to_guess_parent_group_totals_or_substitute_wdi():
    assert audit.TABLE_ID == "EXT010200.px"
    assert audit.MAX_CELLS == 10000
    assert audit.OUTPUT.name == "exports_partner_from_bns.csv"
    assert audit.ANCHOR_2025_THOUSAND_USD == 3782700.0
    assert audit.OUTPUT.name != "trade.csv"
    assert audit.EVIDENCE.name.endswith("_source_metadata.json")

def test_verified_2025_top_five_source_codebook_and_annual_shares():
    """Source response pins trace to BNS publisher job 40446267708."""
    curated = audit.ROOT / "data/trade/destinations.csv"
    rows = list(csv.DictReader(
        x for x in curated.read_text("utf-8").splitlines() if not x.startswith("#")))
    assert len(rows) == 20
    assert [int(x["year"]) for x in rows] == list(audit.YEARS)
    assert list(rows[0]) == [
        "year", "romania_pct", "turkey_pct", "italy_pct", "czechia_pct",
        "ukraine_pct",
    ]
    assert set(audit.PARTNER_GROUPS) == {"1", "13", "42"}
    assert audit.UKRAINE_CODES == {
        "old": ("11", "..Ukraine (CSI)"), "new": ("87", "..Ukraine")}
    for row in rows:
        percentages = [float(value) for name, value in row.items() if name != "year"]
        assert all(0 <= value < 90 for value in percentages)
        assert sum(percentages) < 100
    assert [float(rows[-1][k]) for k in list(rows[-1])[1:]] == pytest.approx(
        [29.007598, 9.950059, 9.226513, 8.218764, 7.919071], abs=1e-6)
    assert float(rows[-3]["ukraine_pct"]) == pytest.approx(14.706501, abs=1e-6)
    assert float(rows[-2]["ukraine_pct"]) == pytest.approx(9.257305, abs=1e-6)
    source = curated.read_text("utf-8")
    assert "5e1fc55f430c4e75a07c172b99a7b60501217fbfd6816e3dc5a5a32a97454fa4" in source
    assert "1adfac120905d511a524ed0a8c957e48da88fe9c9a41f4ee76a36d186e7" in source
    assert "Bender" in source and "not WDI goods and services" in source


def test_destination_curator_rejects_wrong_group_taxonomy():
    dataset, pc, yc, partners, years = cube()
    rows = audit.decode(dataset, pc, yc, partners, years)
    with pytest.raises(ValueError, match="changed partner code"):
        audit.verify_destination_taxonomy(rows, partners)


def test_verified_destination_panel_is_plotted_not_pending():
    text = (audit.ROOT / "plates.py").read_text("utf-8")
    trade = text.split("def plate_trade(", 1)[1].split("def plate_markets(", 1)[0]
    assert 'ig.slot("trade.destinations"' in trade
    assert '"trade/destinations.csv"' in trade
    assert "BNS EXT010200" in trade and '"trade/trade.csv"' in trade
    assert 'ig.slot("trade.lens"' not in trade
