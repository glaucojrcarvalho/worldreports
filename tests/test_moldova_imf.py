"""IMF source-vintage, forecast and observed-Moldova fiscal checks.

All tests are offline. Real publisher payload validation happened separately
in GitHub Actions run 40269456831; curated rows reproduce its outputs.
"""
from __future__ import annotations

import csv
import importlib.util
import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "countries" / "moldova"
SCRIPT = DIR / "fetch" / "fetch_imf.py"
spec = importlib.util.spec_from_file_location("moldova_imf", SCRIPT)
assert spec and spec.loader
imf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imf)


def csvrows(name: str) -> list[dict[str, str]]:
    with (DIR / "data" / "fiscal" / name).open(encoding="utf-8") as h:
        return list(csv.DictReader(line for line in h if not line.startswith("#")))


def by_year(rows: list[dict[str, str]], year: int) -> dict[str, str]:
    return next(row for row in rows if int(row["year"]) == year)


def test_distinct_imf_datasets_and_attributions_are_explicit() -> None:
    assert {imf.SPECS[c][0] for c in imf.WEO_CODES} == {"WEO"}
    assert {imf.SPECS[c][0] for c in imf.FPP_CODES} == {"FPP"}
    m = yaml.safe_load((DIR / "SOURCES.yaml").read_text(encoding="utf-8"))
    w = m["fiscal"]["weo_bal_debt.csv"]
    f = m["fiscal"]["fpp_finances.csv"]
    assert w["official"] and f["official"]
    assert w["refreshed_by"] == "fetch/fetch_imf.py"
    assert f["refreshed_by"] == "fetch/fetch_imf.py"
    assert "October 2026" in w["source"]
    assert "December 2025" in f["source"]
    assert "NOT WEO" in f["notes"]


def test_weo_2006_to_2026_projections_cannot_be_historical() -> None:
    rows = csvrows("weo_bal_debt.csv")
    assert len(rows) == 21
    assert [int(r["year"]) for r in rows] == list(range(2006, 2027))
    assert list(rows[0]) == [
        "year", "balance_pct_gdp", "balance_pct_gdp_proj",
        "debt_pct_gdp", "debt_pct_gdp_proj",
    ]
    for r in rows:
        if int(r["year"]) < 2026:
            assert r["balance_pct_gdp"] and r["debt_pct_gdp"]
            assert r["balance_pct_gdp_proj"] == r["debt_pct_gdp_proj"] == ""
        else:
            assert r["balance_pct_gdp"] == r["debt_pct_gdp"] == ""
            assert r["balance_pct_gdp_proj"] and r["debt_pct_gdp_proj"]
    assert float(by_year(rows, 2024)["balance_pct_gdp"]) == -4.0
    assert float(by_year(rows, 2025)["balance_pct_gdp"]) == -3.9
    assert float(by_year(rows, 2025)["debt_pct_gdp"]) == 39.2
    assert float(by_year(rows, 2026)["balance_pct_gdp_proj"]) == -5.0
    assert float(by_year(rows, 2026)["debt_pct_gdp_proj"]) == 41.8
    assert "NOT claimed final/audited" in (
        DIR / "data/fiscal/weo_bal_debt.csv"
    ).read_text(encoding="utf-8")


def test_fpp_2006_to_2024_only_and_internal_balances() -> None:
    rows = csvrows("fpp_finances.csv")
    assert len(rows) == 19
    assert [int(r["year"]) for r in rows] == list(range(2006, 2025))
    assert list(rows[0]) == [
        "year", "revenue_pct_gdp", "expenditure_pct_gdp",
        "primary_balance_pct_gdp", "interest_pct_gdp",
    ]
    for row in rows:
        rev, exp, pb, interest = [float(row[k]) for k in list(row)[1:]]
        assert all(math.isfinite(x) for x in (rev, exp, pb, interest))
        assert rev - exp == pytest.approx(pb - interest, abs=1e-4)
    assert by_year(rows, 2024)["revenue_pct_gdp"] == "34.072411"
    assert by_year(rows, 2024)["expenditure_pct_gdp"] == "37.956860"
    assert "NOT IMF WEO" in (DIR / "data/fiscal/fpp_finances.csv").read_text(encoding="utf-8")


def test_weo_fpp_2024_differences_not_reconciled_by_splicing() -> None:
    w = by_year(csvrows("weo_bal_debt.csv"), 2024)
    f = by_year(csvrows("fpp_finances.csv"), 2024)
    fpp_balance = float(f["revenue_pct_gdp"]) - float(f["expenditure_pct_gdp"])
    assert fpp_balance == pytest.approx(-3.884449, abs=1e-6)
    assert float(w["balance_pct_gdp"]) == -4.0
    assert abs(float(w["balance_pct_gdp"]) - fpp_balance) > 0.1


def fake_payload(code: str) -> dict:
    dataset, source, _ = imf.SPECS[code]
    indic = {
        "dataset": dataset,
        "source": source,
        "unit": "Percent of GDP" if dataset == "WEO" else "% of GDP",
    }
    if dataset == "WEO":
        indic["projection-year"] = 2026
    end = 2026 if dataset == "WEO" else 2024
    return {
        "indicators": {code: indic},
        "values": {code: {"MDA": {str(y): 2.0 for y in range(2006, end + 1)}}},
    }


@pytest.mark.parametrize("code", imf.SPECS)
def test_validator_accepts_only_pinned_imf_country_dataset(code: str) -> None:
    sample = fake_payload(code)
    value, info = imf.validate(sample, code)
    assert len(value) == (21 if info["dataset"] == "WEO" else 19)
    assert 2006 in value


@pytest.mark.parametrize("change", [
    lambda p, code: p["values"][code].update({"MDA": {"2024": 1.0}}),
    lambda p, code: p["indicators"][code].update({"dataset": "WEO"}),
    lambda p, code: p["indicators"][code].update({"source": "WEO April 2026"}),
    lambda p, code: p["indicators"][code].update({"unit": "Billions US$"}),
    lambda p, code: p["values"][code]["MDA"].update({"2024": float("nan")}),
])
def test_validator_rejects_wrong_source_scope_and_values(change) -> None:
    code = "rev"
    sample = fake_payload(code)
    change(sample, code)
    with pytest.raises(ValueError):
        imf.validate(sample, code)


def test_weo_validator_rejects_unflagged_forecast() -> None:
    sample = fake_payload("GGXCNL_NGDP")
    sample["indicators"]["GGXCNL_NGDP"]["projection-year"] = 2027
    with pytest.raises(ValueError, match="projection boundary"):
        imf.validate(sample, "GGXCNL_NGDP")
