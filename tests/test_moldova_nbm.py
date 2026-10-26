"""Offline semantic tests for official NBM sources and derived annual metrics."""
from __future__ import annotations

import importlib.util
import csv
import math
from datetime import date

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "countries" / "moldova" / "fetch" / "fetch_nbm.py"
spec = importlib.util.spec_from_file_location("moldova_nbm", SCRIPT)
assert spec is not None and spec.loader is not None
nbm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nbm)


def test_european_decimal_and_nominal_amount() -> None:
    assert nbm.as_decimal("7,50") == 7.5
    assert nbm.as_decimal("17.822") == 17.822
    with pytest.raises(ValueError):
        nbm.as_decimal("1,234.56")
    with pytest.raises(ValueError):
        nbm.as_decimal("NaN")


def test_fx_export_requires_exact_calendar_year_and_usd_unit() -> None:
    content = ('"Average rates for:";01.01.2024;31.12.2024;;\n'
               ';;;;\n'
               'Currency;Code;Abbr;Rate;Rates\n'
               '"US Dollar";840;USD;1;17.8200\n'
               '"Japanese Yen";392;JPY;100;11.23\n')
    assert nbm.parse_fx(content, 2024) == 17.82
    assert nbm.parse_fx(content.replace(";USD;1;17.8200", ";USD;100;1782.00"),
                        2024) == 17.82
    with pytest.raises(ValueError, match="period incorrect"):
        nbm.parse_fx(content, 2025)
    with pytest.raises(ValueError, match="exactly one USD"):
        nbm.parse_fx(content.replace("840;USD;", "841;USD;"), 2024)
    with pytest.raises(ValueError, match="exactly one USD"):
        nbm.parse_fx(content.replace("USD;1;17.8200\n", "EUR;1;17.8200\n"), 2024)


def events() -> list[tuple[date, float]]:
    d = [(date(2000, 1, 1), 4.25)]
    d += [(date(y, 1, 1), 4.25) for y in range(2001, 2024)]
    d += [(date(y, 7, 1), 4.25) for y in range(2000, 2024)]
    d += [
        (date(2024, 5, 7), 3.6),
        (date(2025, 1, 10), 5.6),
        (date(2025, 2, 5), 6.5),
        (date(2025, 8, 7), 6.25),
        (date(2025, 9, 18), 6.0),
        (date(2025, 12, 11), 5.0),
        (date(2026, 9, 17), 9.0),
    ]
    return sorted(d)


def test_policy_weighted_by_days_not_average_of_decisions() -> None:
    out = nbm.policy_by_year(events())
    assert set(out) == set(range(2006, 2026))
    assert out[2024][1] == 3.6
    assert out[2025][1] == 5.0
    # 2024 is a leap year, and the 7 May change is effective that day.
    # Days Jan1..May6 at 4.25; May7..Dec31 at 3.60.
    earlier = (date(2024, 5, 7) - date(2024, 1, 1)).days
    expected = (earlier * 4.25 + (366 - earlier) * 3.6) / 366
    assert out[2024][0] == pytest.approx(expected, abs=1e-12)
    assert out[2024][0] != pytest.approx((4.25 + 3.6) / 2, abs=0.001)


def test_policy_parser_rejects_partial_export() -> None:
    body = ('"Valid from:";"Overnight deposits";'
            '"Basic rate (rate applied on the main short-term monetary policy operation)";'
            '"Repo rate";"Overnight credits"\n'
            '11.12.2025;3,00;5,00;5,25;7,00\n')
    with pytest.raises(ValueError, match="Not enough policy history"):
        nbm.parse_policy(body)



def test_policy_accepts_official_publisher_footer_only_after_complete_history() -> None:
    header = ';'.join('"' + c + '"' for c in nbm.COLS)
    body = header + "\\n"
    for when, rate in reversed(events()):
        body += f"{when:%d.%m.%Y};3,00;{rate:.2f};5,25;7,00\\n"
    body += "Data source:;BNM\\n"
    assert len(nbm.parse_policy(body.replace("\\n", "\n"))) == len(events())
    with pytest.raises(ValueError):
        nbm.parse_policy(body.replace("Data source:;BNM", "Data source:;other")
                         .replace("\\n", "\n"))


def test_sidecar_headers_make_source_and_mean_semantics_explicit() -> None:
    policy = nbm.render_policy(nbm.policy_by_year(events()))
    assert len([line for line in policy.splitlines() if line.startswith("20")]) == 20
    assert "CALENDAR-DAY-weighted" in policy
    assert "2006,4.250000" in policy
    fx = nbm.render_fx({year: 17.8 for year in range(2006, 2026)})
    assert "MDL per exactly ONE USD" in fx
    assert "2025,17.800000" in fx


def test_verified_curated_nbm_rate_series_and_units() -> None:
    base = ROOT / "countries" / "moldova" / "data" / "markets"
    def read(name):
        with (base / name).open(encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(line for line in fp if not line.startswith("#")))
    policy = read("policy.csv")
    fx = read("usd_mdl.csv")
    assert [int(row["year"]) for row in policy] == list(range(2006, 2026))
    assert [int(row["year"]) for row in fx] == list(range(2006, 2026))
    assert list(policy[0]) == ["year", "policy_mean_pct", "policy_dec31_pct"]
    assert list(fx[0]) == ["year", "mdl_per_usd_annual_avg"]
    assert float(policy[-2]["policy_mean_pct"]) == pytest.approx(3.810519)
    assert float(policy[-1]["policy_mean_pct"]) == pytest.approx(6.134247)
    assert float(policy[-2]["policy_dec31_pct"]) == 3.6
    assert float(policy[-1]["policy_dec31_pct"]) == 5.0
    assert float(fx[-2]["mdl_per_usd_annual_avg"]) == pytest.approx(17.7918)
    assert float(fx[-1]["mdl_per_usd_annual_avg"]) == pytest.approx(17.3705)
    assert float(fx[0]["mdl_per_usd_annual_avg"]) == pytest.approx(13.1319)
    assert float(policy[-1]["policy_mean_pct"]) != float(policy[-1]["policy_dec31_pct"])
    assert all(3 <= float(row["mdl_per_usd_annual_avg"]) <= 50 for row in fx)
    policy_notes = (base / "policy.csv").read_text(encoding="utf-8")
    fx_notes = (base / "usd_mdl.csv").read_text(encoding="utf-8")
    assert "calendar-DAY-weighted" in policy_notes
    assert "per 1 USD" in fx_notes
    assert "40273821580" in policy_notes and "40273821580" in fx_notes
