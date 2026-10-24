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
POLICY_NOTE = "Policy rate at year-end; inflation is an annual average"


def _values(ctx, relative: str, column: str) -> tuple[list[int], list[float]]:
    """Use the country data accessor; missing inputs are never fabricated."""
    table = ctx.table(relative)
    if table is None or column not in table:
        return [], []
    return ctx.series(table, column)


def _segments(years: Iterable[int], values: Iterable[float],
              seams: tuple[int, ...] = (2014, 2022)):
    """Never connect different publisher territorial-coverage regimes."""
    segments: list[tuple[list[int], list[float]]] = []
    previous_year = None
    previous_regime = None
    for year, value in zip(years, values):
        y = int(year)
        regime = sum(y >= seam for seam in seams)
        # A missing year is a broken observation, never a continuous line.
        if previous_year is not None and y <= previous_year:
            raise ValueError("Annual series years must be increasing")
        if previous_regime != regime or (previous_year is not None
                                         and y != previous_year + 1):
            segments.append(([], []))
        segments[-1][0].append(y)
        segments[-1][1].append(value)
        previous_year, previous_regime = y, regime
    return segments


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

    if key == "demography.population":
        years, values = _values(ctx, "social/population.csv", "population_persons")
        if not years:
            return _missing(ctx, ax)
        # The January-2015 geography excludes occupied regions not excluded
        # in January 2014: this step is a scope break, not just population
        # loss from mortality or emigration.
        index_years, index_values = ctx.index_2006((years, values))
        _line(ctx, ax, index_years, index_values, ctx.p.BLUE,
              label="Present population on 1 January", seams=(2015,))
        _small_note(ctx, ax, "2015: territorial coverage changed; 2023–25 suppressed")
        return

    if key == "world.reserves":
        years, values = _values(ctx, "macro/reserves.csv", "usd_bn")
        if not years:
            return _missing(ctx, ax)
        _line(ctx, ax, years, values, ctx.p.BLUE,
              label="NBU gross official reserves, year-end")
        _small_note(ctx, ax, "Gross reserve assets; US$ bn at year-end")
        return

    if key == "markets.policy_rate":
        years, rates = _values(ctx, "markets/policy_rate.csv",
                               "policy_rate_eoy_pct")
        cyears, inflation = _values(ctx, "macro/cpi.csv",
                                   "annual_inflation_pct")
        if not years or not cyears:
            return _missing(ctx, ax)
        _line(ctx, ax, years, rates, ctx.p.BLUE,
              label="NBU key rate, year-end")
        _line(ctx, ax, cyears, inflation, ctx.p.RED,
              label="Annual-average headline CPI", seams=(2014, 2022))
        _small_note(ctx, ax, POLICY_NOTE)
        ax.legend(loc="upper right", fontsize=7.6)
        return

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
         subtitle="Official year-end policy rate and exchange-rate index; government bonds and equities still under review.",
         alt="Four panels: official year-end NBU policy rate against annual-average CPI, plus the hryvnia index; bonds and equities pending.",
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
         subtitle="Official year-end international reserves are verified; comparable GDP, HDI and corruption measures remain under review.",
         alt="Four panels: verified year-end gross official reserves in US$ billions; comparable GDP, development and corruption perceptions remain pending.",
         source=UNDER_REVIEW),
    dict(slug="09_demographics", topic="demography", builder=fig_demography,
         title="Ukraine — Population and Demography, 2006–2026",
         subtitle="Estimated January 1 present population through 2022; data for 2023–2025 are suppressed, with a 2015 scope break.",
         alt="Four panels: indexed official present-population estimates on January 1, 2006–2022, with a 2015 coverage seam and suppressed 2023–2025; fertility, birth/death and migration measurements pending.",
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
