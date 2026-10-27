"""Moldova's twelve *draft* canonical plates: checked source lanes, not a release.

This module is deliberately not discoverable by the published country registry:
research/country_candidate.yaml has NOT been promoted to country.yaml yet.
The branch-only action temporarily registers the candidate inside its runner
and renders these plates in English; it never deploys or publishes them.

Each line reads a committed Moldova CSV. National BNS cash-budget execution
and the IMF's FPP / WEO *different vintages* are never silently fused.
No annual 2026 value is drawn as a complete calendar-year observation.
"""
from __future__ import annotations


def _series(ctx, file: str, column: str):
    table = ctx.table(file)
    if table is None or column not in table:
        raise KeyError(f"Moldova curated source missing {file}:{column}")
    return ctx.series(table, column)


def _aligned(ctx, file: str, first: str, second: str):
    """Two percentages in one CSV release, joined by YEAR, never by row."""
    aa = dict(zip(*_series(ctx, file, first)))
    bb = dict(zip(*_series(ctx, file, second)))
    years = sorted(aa.keys() & bb.keys())
    return years, [aa[y] for y in years], [bb[y] for y in years]


def _pending(ctx, ig, ax, reason: str):
    ctx.pending(ax)
    ax.text(0.50, 0.30, reason, transform=ax.transAxes,
            ha="center", va="top", fontsize=8.0, color=ctx.p.MUTED,
            style="italic")


def _foot(ctx, ax, label: str):
    ax.text(0.5, -0.06, label, transform=ax.transAxes, ha="center",
            va="top", color=ctx.p.FAINT, style="italic", fontsize=7.1)


def _finish(ig):
    for ax in ig.axes_flat:
        if ax.get_visible():
            ig.style_axis(ax)


# Economy: WB WDI, modelled unemployment (not the national LFS).
def plate_economy(ctx, ig):
    p = ctx.p
    ax = ig.slot("economy.growth", "Real GDP growth (% per year)")
    y, v = _series(ctx, "macro/economy.csv", "gdp_growth_pct")
    ctx.bars(ax, y, v, lambda x: p.GREEN if x >= 0 else p.RED)
    _foot(ctx, ax, "World Bank WDI, real national-accounts growth")

    ax = ig.slot("economy.gdp_per_person", "GDP per person (US$, current)")
    ctx.line(ax, *_series(ctx, "world/world.csv", "gdp_per_person_usd"), p.BLUE)
    _foot(ctx, ax, "World Bank WDI, current US dollars")

    ax = ig.slot("economy.inflation", "Consumer price inflation (% per year)")
    ctx.line(ax, *_series(ctx, "macro/economy.csv", "cpi_inflation_pct"), p.RED)
    _foot(ctx, ax, "World Bank WDI, annual CPI")

    ax = ig.slot("economy.unemployment", "Unemployment (% of labour force)")
    ctx.line(ax, *_series(ctx, "macro/economy.csv", "unemployment_pct"), p.NAVY)
    _foot(ctx, ax, "World Bank WDI, ILO-modelled unemployment")
    _finish(ig)


# Fiscal: FPP 2025-12 ends 2024; WEO 2026-10 ends 2025.
# Their general-government concepts are similar, but the vintages DIFFER.
def plate_fiscal(ctx, ig):
    p = ctx.p
    ax = ig.slot("fiscal.revenue_expenditure", "Revenue and spending (% of GDP)")
    y, a, b = _aligned(ctx, "fiscal/fpp_finances.csv",
                        "revenue_pct_gdp", "expenditure_pct_gdp")
    ctx.line(ax, y, a, p.TEAL, label="FPP revenue")
    ctx.line(ax, y, b, p.RED, label="FPP expenditure")
    ax.legend(fontsize=8, frameon=False)
    _foot(ctx, ax, "IMF FPP, December 2025 vintage; through 2024")

    ax = ig.slot("fiscal.balance", "Overall and primary balance (% of GDP)")
    y, v = _series(ctx, "fiscal/weo_bal_debt.csv", "balance_pct_gdp")
    ctx.bars(ax, y, v, lambda x: p.RED if x < 0 else p.GREEN)
    py, pv = _series(ctx, "fiscal/fpp_finances.csv", "primary_balance_pct_gdp")
    ctx.line(ax, py, pv, p.NAVY, label="FPP primary balance (different vintage)")
    ax.legend(fontsize=8, frameon=False)
    _foot(ctx, ax, "WEO October 2026 overall; FPP December 2025 primary")

    ax = ig.slot("fiscal.debt", "Gross general-government debt (% of GDP)")
    ctx.line(ax, *_series(ctx, "fiscal/weo_bal_debt.csv", "debt_pct_gdp"), p.BLUE)
    _foot(ctx, ax, "IMF WEO, October 2026 vintage; 2026 forecast excluded")

    ax = ig.slot("fiscal.interest", "Interest paid (% of GDP)")
    ctx.line(ax, *_series(ctx, "fiscal/fpp_finances.csv", "interest_pct_gdp"), p.GOLD)
    _foot(ctx, ax, "IMF FPP, December 2025 vintage; through 2024")
    _finish(ig)


# National BNS FIN010100 (cash execution) and BNS national-account GDP
# BOTH exclude the left-bank Nistru districts and municipality Bender.
# This is a domestic national-public-budget classification, NOT identical
# to IMF FPP/WEO or independently verified general-government GFS/COFOG.
# 2025 GDP and spending remain PRELIMINARY; older data are source-vintage
# observations without an invented year-by-year finality flag.
def plate_spending(ctx, ig):
    p = ctx.p
    columns = (
        "expenditure_mdl_mn", "general_services_mdl_mn",
        "defense_mdl_mn", "public_order_mdl_mn", "economic_affairs_mdl_mn",
        "environment_mdl_mn", "housing_mdl_mn", "health_mdl_mn",
        "culture_mdl_mn", "education_mdl_mn", "social_protection_mdl_mn",
    )
    budget = {col: dict(zip(*_series(ctx, "fiscal/public_budget.csv", col)))
              for col in columns}
    gdp = dict(zip(*_series(ctx, "fiscal/nominal_gdp_bns.csv", "gdp_mdl_mn")))
    years = sorted(set(gdp) & set(budget["expenditure_mdl_mn"]))
    if years != list(range(2016, 2026)) or any(gdp[y] <= 0 for y in years):
        raise ValueError("Moldova national functional spending GDP scope/year gap")

    # Ten mutually exclusive official national functions → seven atlas groups.
    # 'Other' combines environment, housing/community amenities and culture.
    groups = (
        ("Social protection, BNS", ("social_protection_mdl_mn",), p.TEAL),
        ("Health, BNS", ("health_mdl_mn",), p.GREEN),
        ("Education, BNS", ("education_mdl_mn",), p.BLUE),
        ("General services, BNS", ("general_services_mdl_mn",), p.NAVY),
        ("Economic affairs, BNS", ("economic_affairs_mdl_mn",), p.GOLD),
        ("Defence and public order, BNS",
         ("defense_mdl_mn", "public_order_mdl_mn"), p.RED),
        ("Other functions, BNS",
         ("environment_mdl_mn", "housing_mdl_mn", "culture_mdl_mn"), p.MUTED),
    )
    shares = {
        label: [sum(budget[col][y] for col in cols) / gdp[y] * 100
                for y in years]
        for label, cols, _ in groups
    }
    totals = [budget["expenditure_mdl_mn"][y] / gdp[y] * 100 for y in years]
    for idx, year in enumerate(years):
        if abs(sum(shares[label][idx] for label, _, _ in groups) -
               totals[idx]) > 0.01:
            raise ValueError(f"{year}: BNS function totals do not reconcile")
    # Independent source anchors: BNS Finance overview explicitly publishes
    # 38.0% (2024 FINAL) / 39.6% (2025 PRELIMINARY) of GDP. Its 2024
    # vintage differs by 0.1 MDL million from the 2016-25 PxWeb table.
    if round(totals[-2], 1) != 38.0 or round(totals[-1], 1) != 39.6:
        raise ValueError("Moldova BNS functional spending denominator revised")

    ax = ig.slot("spending.by_function", "Spending by function (% of GDP)")
    ax.stackplot(years, *(shares[label] for label, _, _ in groups),
                 labels=[label for label, _, _ in groups],
                 colors=[color for _, _, color in groups], alpha=0.88, lw=0)
    ax.legend(fontsize=5.9, ncol=2, loc="upper left", frameon=False)
    _foot(ctx, ax, "BNS national cash functions / BNS GDP; 2025 provisional")

    ax = ig.slot("spending.social_protection", "Social protection (% of GDP)")
    social = shares["Social protection, BNS"]
    remainder = [total - soc for total, soc in zip(totals, social)]
    ctx.line(ax, years, social, p.TEAL, label="Social protection, BNS")
    ctx.line(ax, years, remainder, p.NAVY, label="Other national functions")
    ax.legend(fontsize=7.3, frameon=False)
    _foot(ctx, ax, "Same BNS budget/GDP denominator; not IMF GFS")

    ax = ig.slot("spending.investment", "Whole-economy investment (% of GDP)")
    ctx.line(ax, *_series(ctx, "macro/economy.csv", "gfcf_pct_gdp"), p.TEAL)
    _foot(ctx, ax, "World Bank WDI gross fixed capital formation")

    ax = ig.slot("spending.public_investment", "Government investment (% of GDP)")
    _pending(ctx, ig, ax, "Government GFCF is not independently staged;\n"
             "national-budget capital spending is not the same.")
    _foot(ctx, ax, "IMF GFS/COFOG route still needs checking")
    _finish(ig)


def plate_trade(ctx, ig):
    p = ctx.p
    years, exports, imports = _aligned(
        ctx, "trade/trade.csv", "exports_pct_gdp", "imports_pct_gdp")
    balance = [a - b for a, b in zip(exports, imports)]

    ax = ig.slot("trade.exports_imports", "Goods and services (% of GDP)")
    ctx.line(ax, years, exports, p.BLUE, label="Exports, national accounts")
    ctx.line(ax, years, imports, p.RED, label="Imports, national accounts")
    ax.legend(fontsize=8, frameon=False)
    _foot(ctx, ax, "World Bank WDI, goods AND services")

    ax = ig.slot("trade.balance", "Trade balance (% of GDP)")
    # -52.8% of GDP in 2008 is verified; the SHARED spine, not just
    # Moldova's own axis, has been widened to show every observation.
    ctx.bars(ax, years, balance, lambda x: p.RED if x < 0 else p.GREEN)
    _foot(ctx, ax, "WDI exports minus imports; all 2006–2025 years")

    ax = ig.slot("trade.destinations", "Top merchandise-export destinations")
    for column, label, color in (
        ("romania_pct", "Romania", p.BLUE),
        ("turkey_pct", "Turkey", p.GOLD),
        ("italy_pct", "Italy", p.RED),
        ("czechia_pct", "Czechia", p.GREEN),
        ("ukraine_pct", "Ukraine", p.TEAL),
    ):
        ctx.line(ax, *_series(ctx, "trade/destinations.csv", column),
                 color, label=label, lw=1.6, ms=2.8)
    ax.legend(fontsize=6.8, ncol=2, loc="upper right", frameon=False)
    _foot(ctx, ax, "BNS EXT010200 customs GOODS; Ukraine group moved in 2024")
    _finish(ig)


def plate_markets(ctx, ig):
    p = ctx.p
    ax = ig.slot("markets.policy_rate", "Policy base rate and CPI inflation (%)")
    ctx.line(ax, *_series(ctx, "markets/policy.csv", "policy_mean_pct"),
             p.BLUE, label="NBM day-weighted base rate")
    ctx.line(ax, *_series(ctx, "macro/economy.csv", "cpi_inflation_pct"),
             p.RED, label="WDI annual CPI inflation")
    ax.legend(fontsize=8, frameon=False)
    _foot(ctx, ax, "NBM effective-date derivative vs WDI CPI; different sources")

    ax = ig.slot("markets.bond_10y", "10-year government bond yield (%)")
    _pending(ctx, ig, ax, "No verified annual-average 10-year secondary\n"
             "market yield has been staged.")
    _foot(ctx, ax, "NBM and Ministry of Finance route unresolved")

    ax = ig.slot("markets.currency", "Moldovan leu vs US$ (2006 = 100)")
    exchange = _series(ctx, "markets/usd_mdl.csv", "mdl_per_usd_annual_avg")
    y, v = ctx.fx_index(exchange)
    ctx.line(ax, y, v, p.TEAL)
    _foot(ctx, ax, "NBM annual-average MDL per USD, inverted; higher = stronger")

    ax = ig.slot("markets.equities", "Equity index in US$ (2006 = 100)")
    _pending(ctx, ig, ax, "No verified tradable equity benchmark or\n"
             "USD-adjusted S&P 500 comparison is staged.")
    _foot(ctx, ax, "Do not substitute a synthetic market index")
    _finish(ig)


def plate_credit(ctx, ig):
    ax = ig.slot("credit.household_debt", "Household credit (% of GDP)")
    _pending(ctx, ig, ax, "Borrower-defined household credit stock\n"
             "is not verified; aggregate private credit differs.")
    ax = ig.slot("credit.lending_rate", "Household lending rate vs policy (%)")
    _pending(ctx, ig, ax, "NBM lending rate needs new-loan, household\n"
             "and currency perimeter validation.")
    ax = ig.slot("credit.npl", "Bank-wide prudential non-performing loans (%)")
    # Prudential NPL means ALL bank loans, not a household-only ratio.
    # The published 2024 drop of 1.4pp differs from the separately
    # rounded 2023 5.6% minus 2024 4.1% (=1.5pp). No inferred cause.
    # Keep the two source-edition segments disconnected.
    ctx.line(ax, *_series(ctx, "credit/prudential_npl.csv",
                          "release_2022_2023_pct"), ctx.p.RED,
             label="NBM 2022–23 year-end reports")
    ctx.line(ax, *_series(ctx, "credit/prudential_npl.csv",
                          "release_2024_2025_pct"), ctx.p.BLUE,
             label="NBM 2024–25 year-end reports")
    ax.legend(fontsize=7.2, frameon=False)
    _foot(ctx, ax, "NBM prudential bank-wide NPL; NOT household; release seam")
    # A separate contextual lens, NEVER a household-credit proxy.
    # FS.AST.PRVT.GD.ZS covers private corporations as well as households.
    ax = ig.slot("credit.lens", "Domestic credit to private sector (% of GDP)")
    ctx.line(ax, *_series(ctx, "credit/private_credit.csv",
                          "private_credit_pct_gdp"), ctx.p.TEAL)
    _foot(ctx, ax, "WDI FS.AST.PRVT.GD.ZS: private sector, NOT households")
    _finish(ig)


def plate_people(ctx, ig):
    ax = ig.slot("people.gini", "Income inequality, Gini (0–100)")
    ctx.line(ax, *_series(ctx, "people/gini.csv", "gini"), ctx.p.BLUE)
    _foot(ctx, ax, "World Bank WDI household-survey Gini; ends 2024")

    ax = ig.slot("people.poverty", "National poverty rate (% of people)")
    # Two source-defined regimes, not a connected series: the HBS was
    # revised in 2019, so a 2018-to-2019 segment would be misleading.
    ctx.line(ax, *_series(ctx, "people/absolute_poverty.csv", "pre_2019_pct"),
             ctx.p.GOLD, label="BNS survey, 2014–2018")
    ctx.line(ax, *_series(ctx, "people/absolute_poverty.csv", "post_2019_pct"),
             ctx.p.BLUE, label="BNS revised survey, 2019–2025")
    ax.legend(fontsize=7.5, frameon=False)
    _foot(ctx, ax, "BNS consumption poverty; methodology break in 2019")

    ax = ig.slot("people.minimum_wage", "Minimum wage (US$ monthly)")
    # A full-year *unified* legal floor exists from 2023. The 2022 law
    # took effect September 1; earlier sectoral minima MUST NOT be spliced.
    # Each USD value is MDL per month / official NBM annual mean MDL/USD.
    ctx.line(ax, *_series(ctx, "people/minimum_wage.csv",
                          "usd_per_month"), ctx.p.TEAL)
    _foot(ctx, ax, "Govt minimum 2023–25 / NBM annual USD/MDL")
    _finish(ig)


def plate_world(ctx, ig):
    p = ctx.p
    ax = ig.slot("world.gdp", "GDP at current prices (US$ bn)")
    y, v = _series(ctx, "world/world.csv", "gdp_usd")
    ctx.line(ax, y, [x / 1e9 for x in v], p.BLUE)
    _foot(ctx, ax, "World Bank WDI; nominal current US dollars")

    ax = ig.slot("world.hdi", "Human Development Index (0–1)")
    ctx.line(ax, *_series(ctx, "world/hdi.csv", "hdi"), p.TEAL)
    _foot(ctx, ax, "UNDP HDR 2025 CSV; through 2023; see edition note")
    ax = ig.slot("world.cpi", "Corruption Perceptions Index (0–100)")
    ctx.line(ax, *_series(ctx, "world/cpi.csv", "cpi_score"), p.RED)
    _foot(ctx, ax, "Transparency International CPI 2025; comparable since 2012")

    ax = ig.slot("world.reserves", "Total reserves including gold (US$ bn)")
    y, v = _series(ctx, "world/world.csv", "reserves_usd")
    ctx.line(ax, y, [x / 1e9 for x in v], p.GOLD)
    _foot(ctx, ax, "World Bank WDI; includes gold; not identical to NBM FX-only")
    _finish(ig)


def plate_demography(ctx, ig):
    p = ctx.p
    ax = ig.slot("demography.population", "Population (index 2006 = 100)")
    pop = _series(ctx, "demography/demography.csv", "population")
    ctx.line(ax, *ctx.index_2006(pop), p.BLUE)
    _foot(ctx, ax, "WDI mid-year population, NOT BNS census residents")

    ax = ig.slot("demography.fertility", "Children per woman (total fertility)")
    ctx.line(ax, *_series(ctx, "demography/demography.csv", "fertility"), p.TEAL)
    ax.axhline(2.1, color=p.FAINT, linestyle=":", linewidth=1)
    _foot(ctx, ax, "WDI harmonised fertility; reference 2.1, ends 2024")

    ax = ig.slot("demography.birth_death", "Crude births and deaths (per 1,000)")
    ctx.line(ax, *_series(ctx, "demography/demography.csv",
                         "birth_rate_per_1000"), p.GREEN, label="Crude birth rate")
    ctx.line(ax, *_series(ctx, "demography/demography.csv",
                         "death_rate_per_1000"), p.RED, label="Crude death rate")
    ax.legend(fontsize=8, frameon=False)
    _foot(ctx, ax, "World Bank WDI population rates; through 2024")

    ax = ig.slot("demography.natural_migration",
                 "Natural change and modelled net migration (/1,000)")
    y, births, deaths = _aligned(ctx, "demography/demography.csv",
                                "birth_rate_per_1000", "death_rate_per_1000")
    ctx.line(ax, y, [a - b for a, b in zip(births, deaths)], p.RED,
             label="Births minus deaths (WDI)")
    net = _series(ctx, "migration/migration.csv", "net_migration")
    yy, vv = ctx.per_1000(net, pop)
    ctx.line(ax, yy, vv, p.BLUE, label="UN-modelled net migration")
    ax.legend(fontsize=7.5, frameon=False)
    _foot(ctx, ax, "Same WDI population denominator; not a registry flow")
    _finish(ig)


def plate_security(ctx, ig):
    p = ctx.p
    ax = ig.slot("security.homicide", "Intentional homicides (/100,000)")
    ctx.line(ax, *_series(ctx, "security/security.csv", "homicide_per_100k"),
             p.RED)
    _foot(ctx, ax, "World Bank WDI / UNODC; through 2023")

    ax = ig.slot("security.suicide", "Suicides (/100,000)")
    ctx.line(ax, *_series(ctx, "security/security.csv", "suicide_per_100k"),
             p.NAVY)
    _foot(ctx, ax, "World Bank WDI / WHO; through 2021")

    ax = ig.slot("security.road_deaths", "Road traffic deaths (/100,000)")
    ctx.line(ax, *_series(ctx, "security/security.csv",
                         "road_deaths_per_100k"), p.GOLD)
    _foot(ctx, ax, "World Bank WDI / WHO; through 2019")
    _finish(ig)


def plate_mortality(ctx, ig):
    p = ctx.p
    ax = ig.slot("mortality.death_rate", "Crude death rate (per 1,000)")
    ctx.line(ax, *_series(ctx, "mortality/mortality.csv",
                         "death_rate_per_1000"), p.RED)
    _foot(ctx, ax, "World Bank WDI; ends 2024, no fabricated 2025")
    ax = ig.slot("mortality.excess_deaths", "Excess deaths (% vs 2015–2019)")
    _pending(ctx, ig, ax, "Same-territory yearly death counts are needed;\n"
             "a crude rate cannot be treated as a death count.")
    ax = ig.slot("mortality.covid", "COVID deaths, underlying cause (/100,000)")
    _pending(ctx, ig, ax, "Cause-of-death COVID series is not staged;\n"
             "reported cases are not death certificates.")
    ax = ig.slot("mortality.lens", "Life expectancy at birth (years)")
    ctx.line(ax, *_series(ctx, "mortality/mortality.csv",
                         "life_expectancy"), p.TEAL)
    _foot(ctx, ax, "WDI period life table; not observed cohort lifespan")
    _finish(ig)


def plate_migration(ctx, ig):
    p = ctx.p
    pop = _series(ctx, "demography/demography.csv", "population")
    ax = ig.slot("migration.flows", "Arrivals and departures (/1,000)")
    _pending(ctx, ig, ax, "No nationally comparable immigration and\n"
             "emigration registration series is staged.")
    ax = ig.slot("migration.net", "Net migration (/1,000)")
    net = _series(ctx, "migration/migration.csv", "net_migration")
    ctx.line(ax, *ctx.per_1000(net, pop), p.BLUE)
    _foot(ctx, ax, "UN model / WDI population; not BNS registered moves")

    ax = ig.slot("migration.foreign_born", "Foreign-born share (%)")
    # Only a national census snapshot exists for 2024, not a comparable
    # time series for the canonical slot. Per PLATE_SPINE.md §1 rule 2,
    # isolated snapshots belong ONLY in a country-specific lens panel.
    _pending(ctx, ig, ax, "One 2024 BNS census observation;\n"
             "no comparable annual foreign-born series.")

    ax = ig.slot("migration.lens", "UN migrant stock versus BNS census (%)")
    # UN international migrant stock (sometimes citizenship-based) is
    # not BNS country-of-birth status. They are plotted as DISCRETE
    # observations with separate legends and source definitions.
    stock = dict(zip(*_series(ctx, "migration/migration.csv", "migrant_stock")))
    denom = dict(zip(*pop))
    years = sorted(stock.keys() & denom.keys())
    share = [stock[y] / denom[y] * 100 for y in years]
    ax.scatter(years, share, color=p.TEAL, s=42, zorder=4,
               label="UN migrant-stock snapshots")
    census_years, census_pct = _series(
        ctx, "migration/foreign_born_census.csv", "foreign_born_pct")
    if census_years != [2024] or census_pct != [4.4]:
        raise ValueError("Moldova census foreign-born anchor/coverage revised")
    ax.scatter(census_years, census_pct, color=p.RED, marker="D",
               s=54, zorder=5, label="BNS 2024 foreign-born census")
    ax.legend(fontsize=7.0, frameon=False)
    _foot(ctx, ax, "UN stock vs BNS country of birth; different definitions")
    _finish(ig)


PLATES = (
    dict(id="01", slug="economy", topic="economy", builder=plate_economy,
         title="Moldova — Growth, Prices and Employment",
         subtitle="World Bank's comparable macroeconomic measures",
         source="World Bank WDI; source notes in SOURCES.yaml",
         alt="GDP growth, GDP per person, annual inflation and modelled unemployment."),
    dict(id="02", slug="fiscal", topic="fiscal", builder=plate_fiscal,
         title="Moldova — Two IMF Fiscal Vintages",
         subtitle="FPP 2025-12 and WEO 2026-10: never mistaken for one release",
         source="IMF FPP (December 2025); IMF WEO (October 2026)",
         alt="General-government revenue, spending, balances, gross debt and interest."),
    dict(id="03", slug="spending", topic="spending", builder=plate_spending,
         title="Moldova — Public Spending and Investment",
         subtitle="BNS national functional cash spending / same-scope GDP",
         source="BNS FIN010100; World Bank WDI; IMF FPP",
         alt="BNS national-budget functions and social protection as GDP shares, alongside the whole-economy investment rate; government GFCF remains pending."),
    dict(id="04", slug="trade", topic="trade", builder=plate_trade,
         title="Moldova — Imports, Exports and the Gap",
         subtitle="WDI national-accounts trade versus separate BNS customs destinations",
         source="World Bank WDI; BNS EXT010200 merchandise exports",
         alt="WDI exports, imports and trade balance; BNS customs-goods partner shares, 2006–2025."),
    dict(id="05", slug="markets", topic="markets", builder=plate_markets,
         title="Moldova — Interest Rates and the Leu",
         subtitle="Official NBM annual rates; WDI inflation; no invented securities",
         source="National Bank of Moldova; World Bank WDI",
         alt="The day-weighted policy rate, inflation and indexed MDL against US dollars."),
    dict(id="06", slug="credit", topic="credit", builder=plate_credit,
         title="Moldova — Credit and Its Definitions",
         subtitle="Private-sector context is not a household loan series",
         source="World Bank WDI; NBM household loan definitions pending",
         alt="Private-sector credit is contextual; bank-wide prudential NPL is observed in 2022–2025, not household debt."),
    dict(id="07", slug="people", topic="people", builder=plate_people,
         title="Moldova — Household Inequality",
         subtitle="WDI Gini, BNS poverty and 2023–25 statutory minimum wage",
         source="World Bank WDI; BNS poverty; Moldova Government wage; NBM FX",
         alt="Household inequality and BNS poverty with a 2019 method break; verified legal minimum 2023–25."),
    dict(id="08", slug="world", topic="world", builder=plate_world,
         title="Moldova in the World — GDP, HDI and CPI",
         subtitle="WDI nominal; UNDP HDR 2025 HDI; TI CPI 2025, comparable since 2012",
         source="World Bank WDI; UNDP HDR 2025; TI CPI 2025",
         alt="GDP and reserves in US dollars; HDI through 2023; comparable CPI scores for 2012–2025."),
    dict(id="09", slug="demography", topic="demography", builder=plate_demography,
         title="Moldova — A Smaller Population",
         subtitle="WDI mid-year model, not the 2024 BNS usual-resident census",
         source="World Bank WDI / UN Population Division",
         alt="Population index, fertility, crude births, deaths and modelled migration."),
    dict(id="10", slug="security", topic="security", builder=plate_security,
         title="Moldova — Homicides, Suicide and Road Safety",
         subtitle="International rates stop in different years; the gaps stay visible",
         source="World Bank WDI, UNODC, WHO",
         alt="Homicides, suicides and road deaths with source-specific end dates."),
    dict(id="11", slug="mortality", topic="mortality", builder=plate_mortality,
         title="Moldova — Death Rates and Life Expectancy",
         subtitle="No substitute for uncollected excess-death and cause-of-death series",
         source="World Bank WDI; national vital data pending",
         alt="Crude mortality and life expectancy; excess and COVID deaths pending."),
    dict(id="12", slug="migration", topic="migration", builder=plate_migration,
         title="Moldova — Migration and Its Definitions",
         subtitle="UN modelled flow; separate UN-stock and BNS birth-country snapshots",
         source="World Bank WDI / UN Population Division; BNS 2024 census",
         alt="Modelled net migration; distinct UN stock snapshots and one BNS 2024 foreign-born census point in the lens. Measured migration flows pending."),
)
