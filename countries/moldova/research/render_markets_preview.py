#!/usr/bin/env python3
"""Draw three *noncanonical research previews* of Moldova's market indicators.

    python3 countries/moldova/research/render_markets_preview.py
    python3 countries/moldova/research/render_markets_preview.py --locale ro

These are NOT site plates: two of the market spine's four canonical
indicators are still missing, no country.yaml/i18n.json is registered, and
we must not pretend a 2006-2025 source dataset is a complete atlas edition.

Top-left: NBM day-weighted annual policy setting against World Bank WDI CPI
inflation. The two measures are independently attributed and are not
combined into an invented 'real policy rate'.
Top-right: 10-year government yield - genuinely pending.
Bottom-left: 2006=100 FX strength index (100 * FX_2006 / FX_year), rising
means stronger leu against USD, from NBM published MDL-per-USD annual FX.
Bottom-right: equity market index - genuinely pending.
All 3 languages are explicit, checked strings in markets_catalog.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

COUNTRY = Path(__file__).resolve().parent.parent
CATALOG = Path(__file__).with_name("markets_catalog.json")
OUTPUT = Path(__file__).parent / "output"
FIRST_YEAR, LAST_YEAR = 2006, 2025
LANGUAGES = ("ro", "en", "pt")

SOURCES = {
    "policy": (COUNTRY / "data/markets/policy.csv",
               ("policy_mean_pct", "policy_dec31_pct")),
    "fx": (COUNTRY / "data/markets/usd_mdl.csv",
           ("mdl_per_usd_annual_avg",)),
    "inflation": (COUNTRY / "data/macro/economy.csv",
                  ("cpi_inflation_pct",)),
}

REQUIRED_STRINGS = {
    "title", "subtitle", "p1", "p2", "p3", "p4", "policy", "inflation",
    "policy_end", "fx", "fx_latest", "pending", "pending_bond",
    "pending_equity", "units_percent", "units_index", "note",
    "sources", "footer",
}


def catalog() -> dict[str, dict[str, str]]:
    loaded = json.loads(CATALOG.read_text(encoding="utf-8"))
    if loaded.get("_meta", {}).get("languages") != list(LANGUAGES):
        raise ValueError("Moldova market research locale list changed")
    strings = {}
    for lang in LANGUAGES:
        entry = loaded.get(lang)
        if not isinstance(entry, dict) or set(entry) != REQUIRED_STRINGS:
            raise ValueError(f"{lang}: missing or unexpected research translations")
        if any(not isinstance(text, str) or not text.strip()
               for text in entry.values()):
            raise ValueError(f"{lang}: empty research translation")
        if entry["fx_latest"].count("{rate}") != 1:
            raise ValueError(f"{lang}: FX caption has no one rate placeholder")
        strings[lang] = entry
    return strings


def get_year_rows(path: Path, names: tuple[str, ...]) -> dict[int, dict[str, float]]:
    """Verify exactly a full calendar-year sequence and numeric schema.

    The input files have committed '#' provenance headers. Their year rows
    are strictly in 2006–2025 order; no network or interpolation allowed.
    """
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        if reader.fieldnames is None or not set(names).issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: missing expected indicator columns")
        rows = list(reader)
    years = [int(row["year"]) for row in rows]
    if years != list(range(FIRST_YEAR, LAST_YEAR + 1)):
        raise ValueError(f"{path.name}: incomplete, repeated or out-of-order years")
    data = {}
    for row in rows:
        year = int(row["year"])
        values = {}
        for name in names:
            raw = row[name]
            if not raw:
                raise ValueError(f"{path.name}: unverified blank {name}/{year}")
            number = float(raw)
            if not math.isfinite(number):
                raise ValueError(f"{path.name}: non-finite {name}/{year}")
            values[name] = number
        data[year] = values
    return data


def data() -> dict[str, object]:
    sources = {name: get_year_rows(path, columns)
               for name, (path, columns) in SOURCES.items()}
    policy = sources["policy"]
    fx = sources["fx"]
    inflation = sources["inflation"]
    if abs(policy[2024]["policy_mean_pct"] - 3.810519) > 1e-6:
        raise ValueError("2024 NBM policy mean revised")
    if abs(policy[2025]["policy_mean_pct"] - 6.134247) > 1e-6:
        raise ValueError("2025 NBM policy mean revised")
    if policy[2025]["policy_dec31_pct"] != 5.0:
        raise ValueError("2025 NBM year-end policy anchor revised")
    if abs(fx[2006]["mdl_per_usd_annual_avg"] - 13.1319) > 1e-5:
        raise ValueError("NBM 2006 FX indexing anchor revised")
    if abs(fx[2025]["mdl_per_usd_annual_avg"] - 17.3705) > 1e-5:
        raise ValueError("2025 NBM FX average revised")
    if abs(inflation[2025]["cpi_inflation_pct"] - 7.759041) > 1e-5:
        raise ValueError("2025 World Bank WDI inflation anchor revised")
    strength = {
        year: 100.0 * fx[2006]["mdl_per_usd_annual_avg"]
        / fx[year]["mdl_per_usd_annual_avg"]
        for year in range(FIRST_YEAR, LAST_YEAR + 1)
    }
    if strength[2006] != 100:
        raise ValueError("Moldova 2006 FX index must equal 100")
    if not all(0 < value < 300 for value in strength.values()):
        raise ValueError("Moldova FX index outside reasonable bounds")
    return {
        "years": list(range(FIRST_YEAR, LAST_YEAR + 1)),
        "policy": policy,
        "inflation": inflation,
        "fx": fx,
        "strength": strength,
    }


def fmt_rate(value: float, lang: str) -> str:
    text = f"{value:.4f}"
    return text.replace(".", ",") if lang in ("ro", "pt") else text


def pending(ax, title: str, message: str, texts: dict[str, str]) -> None:
    ax.set_title(title, loc="left", fontsize=13, weight="bold", pad=14)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(.50, .60, texts["pending"], transform=ax.transAxes,
            ha="center", va="center", fontsize=11, color="#8b4a3a",
            weight="bold")
    ax.text(.50, .43, message, transform=ax.transAxes,
            ha="center", va="center", fontsize=10, color="#4f5965",
            linespacing=1.6, wrap=True,
            bbox={"facecolor": "#f5f6f7", "edgecolor": "#d3d9df",
                  "boxstyle": "round,pad=0.8"})
    for spine in ax.spines.values():
        spine.set_color("#ced4d9")
    ax.set_facecolor("#fafafa")


def draw(locale: str, destination: Path | None = None) -> Path:
    texts = catalog()[locale]
    obs = data()
    years = obs["years"]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10.2))
    fig.patch.set_facecolor("#fcfcfd")

    ax = axes[0, 0]
    policy = [obs["policy"][year]["policy_mean_pct"] for year in years]
    cpi = [obs["inflation"][year]["cpi_inflation_pct"] for year in years]
    ax.plot(years, policy, lw=2.3, color="#235f77", marker="o",
            markersize=3.7, label=texts["policy"])
    ax.plot(years, cpi, lw=2.0, color="#b36f2b", linestyle="--",
            marker="s", markersize=3.3, label=texts["inflation"])
    ax.set_title(texts["p1"], loc="left", fontsize=13, weight="bold", pad=10)
    ax.set_ylabel(texts["units_percent"], fontsize=10)
    ax.set_ylim(-3, max(max(policy), max(cpi)) + 4)
    ax.legend(frameon=False, loc="upper left", fontsize=8.4)

    pending(axes[0, 1], texts["p2"], texts["pending_bond"], texts)

    ax = axes[1, 0]
    strength = [obs["strength"][year] for year in years]
    ax.plot(years, strength, lw=2.8, color="#287565")
    ax.axhline(100, color="#76828d", lw=1, linestyle=":")
    ax.fill_between(years, strength, 100, alpha=.12, color="#287565")
    ax.scatter([2025], [strength[-1]], color="#287565", s=42, zorder=3)
    ax.set_title(texts["p3"], loc="left", fontsize=13, weight="bold", pad=10)
    ax.set_ylabel(texts["units_index"], fontsize=10)
    ax.text(.985, .84, texts["fx"], transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color="#475467",
            bbox={"facecolor": "#fcfcfd", "edgecolor": "none", "alpha": .85, "pad": 2})
    rate = obs["fx"][2025]["mdl_per_usd_annual_avg"]
    ax.text(.985, .92, texts["fx_latest"].format(rate=fmt_rate(rate, locale)),
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.5, color="#475467",
            bbox={"facecolor": "#fcfcfd", "edgecolor": "none", "alpha": .85, "pad": 2})

    pending(axes[1, 1], texts["p4"], texts["pending_equity"], texts)

    for ax in (axes[0, 0], axes[1, 0]):
        ax.set_xlim(2005.5, 2025.5)
        ax.set_xticks(list(range(2006, 2026, 2)))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#dee3e7", lw=.8)
        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=9)
        ax.set_facecolor("#fcfcfd")
        for edge in ("right", "top"):
            ax.spines[edge].set_visible(False)
    fig.suptitle(texts["title"], x=.052, y=.984, ha="left",
                 fontsize=21, fontweight="bold")
    fig.text(.052, .947, texts["subtitle"], ha="left",
             fontsize=10, color="#7f4037", weight="bold")
    fig.text(.052, .074, texts["note"], ha="left", va="top",
             fontsize=8.5, color="#354052")
    fig.text(.052, .052, texts["sources"], ha="left", va="top",
             fontsize=8.5, color="#354052")
    fig.text(.052, .030, texts["footer"], ha="left", va="top",
             fontsize=8.5, color="#354052")
    fig.tight_layout(rect=[.045, .092, .986, .921], h_pad=2.8, w_pad=2.0)
    if destination is None:
        destination = OUTPUT / f"moldova_markets_preview.{locale}.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", choices=LANGUAGES, help="omit to build all three languages")
    args = parser.parse_args()
    locales = (args.locale,) if args.locale else LANGUAGES
    for locale in locales:
        print(f"{locale}: {draw(locale)} (research preview only, not atlas plate)")


if __name__ == "__main__":
    main()
