"""Ukraine atlas plate builders, research-stage implementation.

Twelve declarative chapter plates, each in the canonical four-panel spine.
Only reviewed source values are drawn. An unverified canonical series is
shown as an explicit RESEARCH PENDING placeholder, never a zero or proxy.

No country.yaml is registered until the rest of the source/localization/
rendering gates pass. This file does not change upstream or other countries.
"""
from __future__ import annotations

from typing import Iterable

# English authored strings are localized by core.i18n at figure-save time.
PENDING_NOTE = "Research pending: definition or coverage not verified"
TERRITORY_NOTE = "2014 and 2022: territorial scope changes"
NOT_GOVERNMENT = "Whole-economy investment, not government investment"
IMPORT_NOTE = "Goods and services, not customs merchandise trade"
FX_NOTE = "2006 = 100; higher = stronger hryvnia"


def _values(ctx, relative: str, column: str) -> tuple[list[int], list[float]]:
    """Use the country data accessor; missing inputs are never fabricated."""
    table = ctx.table(relative)
    if table is None or column not in table:
        return [], []
    return ctx.series(table, column)


def _segments(years: Iterable[int], values: Iterable[float],
              seams: tuple[int, ...] = (2014, 2022)):
    """Never connect different publisher territorial-coverage regimes."""
    groups = {}
    for year, value in zip(years, values):
        y = int(year)
        group = sum(y >= seam for seam in seams)
        ys, vals = groups.setdefault(group, ([], []))
        ys.append(y)
        vals.append(value)
    return [groups[key] for key in sorted(groups)]


def _line(ctx, ax, years, values, color, label="", seams=()):
    """Separate definitional regimes without interpolating missing years."""
    parts = _segments(years, values, seams) if seams else [(years, values)]
    for i, (ys, vals) in enumerate(parts):
        if ys:
            ctx.line(ax, ys, vals, color, marker="o", ms=3.2, lw=1.9,
                     label=label if i == 0 else "_nolegend_")


def _missing(ctx, ax):
    ctx.pending(ax)
    ax.text(0.5, 0.35, PENDING_NOTE, transform=ax.transAxes,
            ha="center", va="top", color=ctx.p.muted, fontsize=8.0)


def _small_note(ctx, ax, note):
    ax.text(0.02, 0.96, note, transform=ax.transAxes, ha="left",
            va="top", color=ctx.p.muted, fontsize=7.6,
            style="italic", zorder=6)


def _plot(ctx, ig, key, ax):
    if key == "economy.growth":
        years, values = _values(ctx, "macro/gdp_growth.csv", "real_growth")
        if not years:
            return _missing(ctx, ax)
        ctx.bars(ax, years, values,
                 lambda v: ctx.p.GREEN if v >= 0 else ctx.p.RED)
        return _small_note(ctx, ax, TERRITORY_NOTE)

    if key == "economy.inflation":
        years, values = _values(ctx, "macro/cpi.csv", "annual_inflation_pct")
        if not years:
            return _missing(ctx, ax)
        _line(ctx, ax, years, values, ctx.p.RED,
              label="Annual-average headline CPI", seams=(2014, 2022))
        _small_note(ctx, ax, TERRITORY_NOTE)
        ax.legend(loc="upper right", fontsize=8)
        return

    if key == "spending.investment":
        years, values = _values(ctx, "spending/investment.csv",
                                "gfcf_pct_gdp")
        if not years:
            return _missing(ctx, ax)
        _line(ctx, ax, years, values, ctx.p.BLUE,
              label="Gross fixed capital formation", seams=(2014, 2022))
        _small_note(ctx, ax, NOT_GOVERNMENT)
        return

    if key == "trade.exports_imports":
        years, exports = _values(ctx, "trade/trade_na.csv",
                                 "exports_pct_gdp")
        imported_years, imports = _values(ctx, "trade/trade_na.csv",
                                          "imports_pct_gdp")
        if not years or not imported_years:
            return _missing(ctx, ax)
        _line(ctx, ax, years, exports, ctx.p.BLUE, "Exports: goods and services",
              seams=(2014, 2022))
        _line(ctx, ax, imported_years, imports, ctx.p.RED,
              "Imports: goods and services", seams=(2014, 2022))
        ax.legend(loc="upper left", fontsize=7.6)
        return _small_note(ctx, ax, IMPORT_NOTE)

    if key == "trade.balance":
        years, values = _values(ctx, "trade/trade_na.csv",
                                "balance_pct_gdp")
        if not years:
            return _missing(ctx, ax)
        ctx.bars(ax, years, values,
                 lambda v: ctx.p.GREEN if v >= 0 else ctx.p.RED)
        return _small_note(ctx, ax, TERRITORY_NOTE)

    if key == "markets.currency":
        years, values = _values(ctx, "markets/fx.csv",
                                "avg_uah_per_usd")
        if not years:
            return _missing(ctx, ax)
        index_years, index_values = ctx.fx_index((years, values))
        _line(ctx, ax, index_years, index_values, ctx.p.BLUE,
              label="NBU annual mean USD/UAH, inverted")
        return _small_note(ctx, ax, FX_NOTE)

    # Nominal GDP is in million UAH, NOT the canonical USD world GDP slot.
    # Public GFCF is NOT interchangeable with whole-economy GFCF.
    # The remaining canonical slots require a sourced, compatible measure.
    return _missing(ctx, ax)


def _draw(ctx, ig, topic: str):
    from core import spine

    for slot in spine.slots(topic):
        if not slot.canonical:
            # A country-specific lens is optional. A missing lens must be
            # hidden by the spine rather than presented as comparable.
            continue
        ax = ig.slot(slot.key, slot.indicator)
        _plot(ctx, ig, slot.key, ax)
        ig.add_recessions(ax, label=False)

    for ax in ig.axes_flat:
        if ax.get_visible():
            ig.style_axis(ax)


def fig_economy(ctx, ig): _draw(ctx, ig, "economy")
def fig_fiscal(ctx, ig): _draw(ctx, ig, "fiscal")
def fig_spending(ctx, ig): _draw(ctx, ig, "spending")
def fig_trade(ctx, ig): _draw(ctx, ig, "trade")
def fig_markets(ctx, ig): _draw(ctx, ig, "markets")
def fig_credit(ctx, ig): _draw(ctx, ig, "credit")
def fig_people(ctx, ig): _draw(ctx, ig, "people")
def fig_world(ctx, ig): _draw(ctx, ig, "world")
def fig_demography(ctx, ig): _draw(ctx, ig, "demography")
def fig_security(ctx, ig): _draw(ctx, ig, "security")
def fig_mortality(ctx, ig): _draw(ctx, ig, "mortality")
def fig_migration(ctx, ig): _draw(ctx, ig, "migration")


SSSU = "Sources: State Statistics Service of Ukraine"
NBU = "Sources: National Bank of Ukraine"
UNDER_REVIEW = "Sources: verification in progress"

# The chapter IDs are the exact output filenames consumed by the site.
# Statements about source availability deliberately describe this draft,
# not a supposed full atlas or nationwide post-invasion coverage.
PLATES = (
    dict(slug="01_economy", topic="economy", builder=fig_economy,
         title="Ukraine — Economic Growth and Prices, 2006–2026",
         subtitle="Real output and annual-average consumer inflation; employment remains under source review.",
         alt="Four panels: real GDP growth and annual-average inflation from Ukrstat; GDP per person and unemployment pending verification.",
         source=SSSU),
    dict(slug="02_fiscal", topic="fiscal", builder=fig_fiscal,
         title="Ukraine — Public Finances, 2006–2026",
         subtitle="General-government revenue, balance, debt and interest require comparable fiscal definitions.",
         alt="Four research-stage panels for general-government revenue, balance, debt and interest; no invented annual data.",
         source=UNDER_REVIEW),
    dict(slug="03_spending", topic="spending", builder=fig_spending,
         title="Ukraine — Government Spending and Investment, 2006–2026",
         subtitle="Whole-economy fixed investment is verified; government accounts remain under review.",
         alt="Four panels: verified whole-economy gross fixed capital formation, with government spending and investment panels pending.",
         source=SSSU),
    dict(slug="04_trade", topic="trade", builder=fig_trade,
         title="Ukraine — Foreign Trade, 2006–2026",
         subtitle="Goods-and-services national accounts, separate from customs merchandise trade.",
         alt="Four panels: verified exports, imports and national-accounts trade balance, with partner destinations under review.",
         source=SSSU),
    dict(slug="05_markets", topic="markets", builder=fig_markets,
         title="Ukraine — Currency and Financial Markets, 2006–2026",
         subtitle="The official hryvnia exchange-rate index; policy rates, bonds and equities remain under review.",
         alt="Four panels: official hryvnia value versus the dollar indexed to 2006; financial interest and equity series pending.",
         source=NBU),
    dict(slug="06_credit", topic="credit", builder=fig_credit,
         title="Ukraine — Credit and Household Debt, 2006–2026",
         subtitle="Household credit measures require bank-sector and coverage checks.",
         alt="Research-stage canonical panels for household debt, borrowing costs and non-performing loans.",
         source=UNDER_REVIEW),
    dict(slug="07_people", topic="people", builder=fig_people,
         title="Ukraine — Inequality, Poverty and Wages, 2006–2026",
         subtitle="Household surveys were interrupted during the full-scale invasion; gaps are not zero.",
         alt="Research-stage panels for income inequality, poverty and the minimum wage.",
         source=UNDER_REVIEW),
    dict(slug="08_world", topic="world", builder=fig_world,
         title="Ukraine — International Comparisons, 2006–2026",
         subtitle="Comparable USD GDP, development, integrity and reserves measures remain under review.",
         alt="Research-stage panels for GDP in dollars, human development, corruption perceptions and reserves.",
         source=UNDER_REVIEW),
    dict(slug="09_demographics", topic="demography", builder=fig_demography,
         title="Ukraine — Population and Demography, 2006–2026",
         subtitle="Wartime displacement and statistical geography require denominator reconciliation.",
         alt="Research-stage panels for population, fertility, birth/death rates and migration.",
         source=UNDER_REVIEW),
    dict(slug="10_security", topic="security", builder=fig_security,
         title="Ukraine — Security and Safety, 2006–2026",
         subtitle="Police reports and certified causes of death are distinct statistical systems.",
         alt="Research-stage panels for homicide, suicide and road traffic deaths.",
         source=UNDER_REVIEW),
    dict(slug="11_mortality", topic="mortality", builder=fig_mortality,
         title="Ukraine — Mortality and Causes of Death, 2006–2026",
         subtitle="Civil registration, wartime completeness and pandemic definitions require review.",
         alt="Research-stage panels for mortality, excess deaths and underlying-cause COVID mortality.",
         source=UNDER_REVIEW),
    dict(slug="12_migration", topic="migration", builder=fig_migration,
         title="Ukraine — Migration and Displacement, 2006–2026",
         subtitle="Border crossings, migration flows, refugee stocks and internal displacement must not be conflated.",
         alt="Research-stage panels for migration flows, net migration and the foreign-born population.",
         source=UNDER_REVIEW),
)
