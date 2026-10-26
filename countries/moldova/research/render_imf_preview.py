#!/usr/bin/env python3
"""Four-panel Moldova IMF fiscal RESEARCH PREVIEW (not a published atlas plate).

The top row is DECEMBER 2025 FPP (revenue/spending, primary/interest), and
the bottom row is OCTOBER 2026 WEO (net balance, gross debt). Source vintage
is prominent on each subplot. No cross-vintage derived total is drawn.

    python3 countries/moldova/research/render_imf_preview.py
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent.parent
FPP_FILE = ROOT / "data" / "fiscal" / "fpp_finances.csv"
WEO_FILE = ROOT / "data" / "fiscal" / "weo_bal_debt.csv"
OUTPUT = ROOT / "research" / "output" / "moldova_imf_fiscal_preview.png"


def read(path: Path) -> dict[int, dict[str, float | None]]:
    with path.open(encoding="utf-8") as handle:
        records = list(csv.DictReader(line for line in handle
                                      if not line.startswith("#")))
    out = {}
    for record in records:
        year = int(record.pop("year"))
        out[year] = {name: float(v) if v else None
                     for name, v in record.items()}
    return out


def validated() -> tuple[dict, dict]:
    fpp, weo = read(FPP_FILE), read(WEO_FILE)
    if sorted(fpp) != list(range(2006, 2025)):
        raise ValueError("Unexpected IMF FPP year coverage")
    if sorted(weo) != list(range(2006, 2027)):
        raise ValueError("Unexpected IMF WEO year coverage")
    for yr in range(2006, 2026):
        if weo[yr]["balance_pct_gdp_proj"] is not None:
            raise ValueError("IMF WEO projections were spliced into observed years")
        if weo[yr]["debt_pct_gdp_proj"] is not None:
            raise ValueError("IMF WEO debt forecasts were spliced into history")
    if weo[2026]["balance_pct_gdp"] is not None or weo[2026]["debt_pct_gdp"] is not None:
        raise ValueError("IMF 2026 forecast appears as historical actual")
    if weo[2026]["balance_pct_gdp_proj"] is None or weo[2026]["debt_pct_gdp_proj"] is None:
        raise ValueError("IMF projection columns missing")
    return fpp, weo


def render(path: Path = OUTPUT) -> Path:
    fpp, weo = validated()
    fig, axs = plt.subplots(2, 2, figsize=(16, 10.2))
    fig.patch.set_facecolor("#fafafa")
    a, b, c, d = axs.flat
    x = list(fpp)
    a.plot(x, [fpp[y]["revenue_pct_gdp"] for y in x],
           label="Revenue", color="#1a6475", lw=2.6)
    a.plot(x, [fpp[y]["expenditure_pct_gdp"] for y in x],
           label="Expenditure", color="#bb762f", lw=2.6)
    a.set_title("Revenue and expenditure | FPP December 2025", loc="left", fontsize=12.5, weight="bold")
    a.set_ylabel("% of GDP")
    a.legend(frameon=False, fontsize=9)
    b.plot(x, [fpp[y]["primary_balance_pct_gdp"] for y in x],
           label="Primary balance", color="#36695a", lw=2.6)
    b.plot(x, [fpp[y]["interest_pct_gdp"] for y in x],
           label="Interest paid", color="#b0505c", lw=2.6)
    b.axhline(0, color="#3e3e3e", linewidth=0.8)
    b.set_title("Primary balance and interest | FPP December 2025", loc="left", fontsize=12.5, weight="bold")
    b.set_ylabel("% of GDP")
    b.legend(frameon=False, fontsize=9)
    wx = list(range(2006, 2026))
    c.plot(wx, [weo[y]["balance_pct_gdp"] for y in wx], color="#8e4e66",
           lw=2.6, label="WEO pre-projection")
    c.plot([2025, 2026], [weo[2025]["balance_pct_gdp"], weo[2026]["balance_pct_gdp_proj"]],
           color="#8e4e66", lw=2, ls="--", label="2026 forecast")
    c.scatter([2026], [weo[2026]["balance_pct_gdp_proj"]], marker="o",
              facecolors="white", edgecolors="#8e4e66", linewidths=1.5, zorder=5)
    c.axhline(0, color="#3e3e3e", linewidth=0.8)
    c.set_title("General government balance | WEO October 2026", loc="left", fontsize=12.5, weight="bold")
    c.set_ylabel("% of GDP")
    c.legend(frameon=False, fontsize=9)
    d.plot(wx, [weo[y]["debt_pct_gdp"] for y in wx], color="#236582",
           lw=2.6, label="WEO pre-projection")
    d.plot([2025, 2026], [weo[2025]["debt_pct_gdp"], weo[2026]["debt_pct_gdp_proj"]],
           color="#236582", lw=2, ls="--", label="2026 forecast")
    d.scatter([2026], [weo[2026]["debt_pct_gdp_proj"]], marker="o",
              facecolors="white", edgecolors="#236582", linewidths=1.5, zorder=5)
    d.set_title("General government gross debt | WEO October 2026", loc="left", fontsize=12.5, weight="bold")
    d.set_ylabel("% of GDP")
    d.legend(frameon=False, fontsize=9)
    for ax in axs.flat:
        ax.set_facecolor("#fafafa")
        ax.grid(axis="y", color="#ddd", linewidth=.7)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(MultipleLocator(4))
        ax.set_xlim(2005.5, 2026.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle("MOLDOVA · IMF fiscal comparables", x=.052, y=.985,
                 horizontalalignment="left", size=23, weight="bold")
    fig.text(.052, .946, "RESEARCH PREVIEW — TWO DISTINCT DATASETS AND VINTAGES, NOT A SINGLE WEO FISCAL PLATE",
             color="#555", size=10)
    fig.text(.052, .035, "IMF DataMapper v2, MDA. FPP Dec 2025 covers 2006–2024; WEO Oct 2026 covers 2006–2025 + 2026 projection.",
             size=9, color="#333")
    fig.text(.052, .018, "Do not splice FPP % GDP with WEO or with BNS national cash-budget MDL levels; historical IMF estimates are not audited national outturns.",
             size=9, color="#905060")
    fig.tight_layout(rect=[.04, .07, .98, .91], h_pad=3.8, w_pad=2.8)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=145, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    target = render(parser.parse_args().output)
    print(f"Generated IMF source-vintage research preview: {target}")


if __name__ == "__main__":
    main()
