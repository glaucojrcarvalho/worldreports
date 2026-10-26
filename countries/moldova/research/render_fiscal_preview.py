#!/usr/bin/env python3
"""Render a SOURCE-RESEARCH preview of Moldova's national cash budget.

Not an atlas chapter or canonical PLATE_SPINE fiscal plate. The canonical
fiscal page needs a harmonised IMF/Eurostat general-government %GDP layer
and Romanian/English/Portuguese translations. This research preview keeps
the BNS national cash-budget units and the 2024 edition seam explicit.

    python3 countries/moldova/research/render_fiscal_preview.py
    python3 countries/moldova/research/render_fiscal_preview.py --output /tmp/moldova.png

Requires matplotlib from the repository's requirements.txt.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

COUNTRY = Path(__file__).resolve().parent.parent
CSV = COUNTRY / "data" / "fiscal" / "public_budget.csv"
DEFAULT_OUTPUT = COUNTRY / "research" / "output" / "moldova_fiscal_preview.png"
FUNCTIONS = [
    ("general_services_mdl_mn", "General services"),
    ("defense_mdl_mn", "Defense"),
    ("public_order_mdl_mn", "Public order"),
    ("economic_affairs_mdl_mn", "Economic affairs"),
    ("environment_mdl_mn", "Environment"),
    ("housing_mdl_mn", "Housing"),
    ("health_mdl_mn", "Health"),
    ("culture_mdl_mn", "Culture"),
    ("education_mdl_mn", "Education"),
    ("social_protection_mdl_mn", "Social protection"),
]


def data() -> list[dict[str, float]]:
    with CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(l for l in handle if not l.startswith("#")))
    years = [int(row["year"]) for row in rows]
    if years != list(range(2016, 2026)):
        raise ValueError(f"Unexpected BNS annual history: {years}")
    parsed = [{"year": int(row["year"]),
               **{k: float(v) for k, v in row.items() if k != "year"}}
              for row in rows]
    for row in parsed:
        if abs(row["revenue_mdl_mn"] - row["expenditure_mdl_mn"]
               - row["balance_mdl_mn"]) > 0.11:
            raise ValueError(f"{row['year']}: national budget identity failed")
        if abs(sum(row[code] for code, _ in FUNCTIONS)
               - row["expenditure_mdl_mn"]) > 0.11:
            raise ValueError(f"{row['year']}: function totals failed")
    if parsed[-2]["expenditure_mdl_mn"] != 122962.7:
        raise ValueError("2024 API-vintage seam changed: review before drawing")
    if parsed[-1]["expenditure_mdl_mn"] != 139856.4:
        raise ValueError("2025 preliminary-source anchor changed")
    return parsed


def render(destination: Path) -> Path:
    rows = data()
    x = [r["year"] for r in rows]
    revenues = [r["revenue_mdl_mn"] for r in rows]
    expenditures = [r["expenditure_mdl_mn"] for r in rows]
    balances = [r["balance_mdl_mn"] for r in rows]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10.2))
    fig.patch.set_facecolor("#fafafa")

    ax = axes[0, 0]
    ax.plot(x, revenues, label="Revenue", lw=2.4, color="#186d7c", marker="o", markersize=4)
    ax.plot(x, expenditures, label="Expenditure + nonfinancial assets",
            lw=2.4, color="#ae642a", marker="o", markersize=4)
    ax.set_title("Receipts vs spending · MDL million", fontsize=13, weight="bold", loc="left")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda n, _: f"{n/1_000:.0f}k"))
    ax.set_ylim(bottom=0)

    ax = axes[0, 1]
    ax.bar(x, balances, color="#8b4252", width=0.68)
    ax.axhline(0, color="#343434", lw=0.8)
    ax.set_title("Budget balance · MDL million", fontsize=13, weight="bold", loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda n, _: f"{n/1_000:.0f}k"))
    ax.text(0.02, 0.05, "Negative = deficit", transform=ax.transAxes,
            fontsize=9, color="#444444")

    ax = axes[1, 0]
    latest = rows[-1]
    funcs = sorted(FUNCTIONS, key=lambda z: latest[z[0]])
    vals = [latest[code] * 100 / latest["expenditure_mdl_mn"] for code, _ in funcs]
    bars = ax.barh([name for _, name in funcs], vals, color="#266a68")
    ax.bar_label(bars, fmt="%.1f%%", fontsize=8, padding=3)
    ax.set_xlim(0, max(vals) * 1.17)
    ax.set_title("2025 preliminary · spending by function", fontsize=13, weight="bold", loc="left")
    ax.set_xlabel("Share of national public-budget expenditure (%)", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)

    ax = axes[1, 1]
    for code, title, color in [
        ("social_protection_mdl_mn", "Social protection", "#266a68"),
        ("education_mdl_mn", "Education", "#4576a4"),
        ("health_mdl_mn", "Health", "#ad7b30"),
    ]:
        vals = [r[code] * 100 / r["expenditure_mdl_mn"] for r in rows]
        ax.plot(x, vals, label=title, color=color, lw=2.2)
        ax.plot(x[-1], vals[-1], marker="o", ms=8, markerfacecolor="#fafafa",
                markeredgewidth=2, markeredgecolor=color)
    ax.set_title("Functional shares over time · % of spending", fontsize=13, weight="bold", loc="left")
    ax.set_ylabel("Share (%)")
    ax.legend(loc="best", fontsize=9, frameon=False)

    for ax in axes.flat:
        ax.set_facecolor("#fafafa")
        ax.grid(axis="y", color="#dddddd", lw=0.7)
        ax.set_axisbelow(True)
        if ax not in (axes[1, 0],):
            ax.set_xticks(x[::2])
            ax.set_xlim(2015.3, 2025.7)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    fig.suptitle("MOLDOVA · national public budget", fontsize=22, weight="bold",
                 y=0.986, x=0.055, ha="left")
    fig.text(0.055, 0.945,
             "RESEARCH PREVIEW — NOT AN ATLAS PLATE  ·  2016–2025 full-year cash execution; 2025 preliminary",
             fontsize=10, color="#444444")
    fig.text(0.055, 0.032,
             "Source: BNS / Ministry of Finance FIN010100 (January–December, million MDL). "
             "Territory excludes left-bank Nistru and Bender.",
             fontsize=8.5, color="#444444")
    fig.text(0.055, 0.015,
             "2024 LIVE API spending is 122,962.7 vs published BNS Finance overview FINAL 122,962.6 (million MDL). "
             "Separate editions; not silently merged.",
             fontsize=8.5, color="#8b4252")
    fig.tight_layout(rect=[0.045, 0.065, 0.98, 0.91], h_pad=3.4, w_pad=3.3)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=145, facecolor=fig.get_facecolor())
    plt.close(fig)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    output = render(parser.parse_args().output)
    print(f"Rendered {output}, BNS national-budget research preview, NOT a published atlas plate")


if __name__ == "__main__":
    main()
