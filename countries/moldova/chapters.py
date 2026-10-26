"""Trilingual Moldova cards sourced from the same curated CSVs as the plates.

This Phase B module is intentionally unregistered pending the full locale,
source-provenance, output, and site-wide quality gates. No values are copied
into the prose: numerical readings are derived from year-stamped CSV rows.
National BNS cash budget and IMF general-government ratios are never joined.
"""
from __future__ import annotations

MONEY, WORLD, PEOPLE = "money", "world", "people"


def _scaled(ctx, path: str, col: str, divisor: float):
    return [(y, value / divisor) for y, value in ctx.col(path, col)]


def _net_migration_rate(ctx):
    """UN-modelled net migration over WDI/UN *same-year* population."""
    population = dict(ctx.col("demography/demography.csv", "population"))
    return [(y, net / population[y] * 1000)
            for y, net in ctx.col("migration/migration.csv", "net_migration")
            if y in population and population[y] > 0]


def _fx_strength(ctx):
    """Annual-average MDL per USD → rising 2006-based MDL strength."""
    fx = dict(ctx.col("markets/usd_mdl.csv", "mdl_per_usd_annual_avg"))
    base = fx[2006]
    return [(y, base / fx[y] * 100) for y in sorted(fx)]


def headline(ctx):
    T = ctx.text
    return [
        ctx.stat(T(ro="PIB", en="GDP", pt="PIB"),
                 _scaled(ctx, "world/world.csv", "gdp_usd", 1e9),
                 "usd_bn"),
        ctx.stat(T(ro="PIB pe locuitor, USD", en="GDP per person, US$",
                   pt="PIB por pessoa, US$"),
                 ctx.col("world/world.csv", "gdp_per_person_usd"),
                 "count", kind="level"),
        ctx.stat(T(ro="Populația", en="Population", pt="População"),
                 _scaled(ctx, "demography/demography.csv", "population", 1e6),
                 "pop_mn", kind="level"),
        ctx.stat(T(ro="Creșterea reală a PIB", en="Real GDP growth",
                   pt="Crescimento real do PIB"),
                 ctx.col("macro/economy.csv", "gdp_growth_pct"), "pct_s"),
        ctx.stat(T(ro="Inflația IPC", en="CPI inflation", pt="Inflação IPC"),
                 ctx.col("macro/economy.csv", "cpi_inflation_pct"), "pct"),
        ctx.stat(T(ro="Datoria publică, FMI WEO", en="Gross debt, IMF WEO",
                   pt="Dívida bruta, FMI WEO"),
                 ctx.col("fiscal/weo_bal_debt.csv", "debt_pct_gdp"),
                 "pct_gdp", kind="level"),
        ctx.stat(T(ro="Rata de bază BNM, media anuală",
                   en="NBM policy, annual day-weighted mean",
                   pt="Taxa básica BNM, média ponderada por dias"),
                 ctx.col("markets/policy.csv", "policy_mean_pct"), "pct"),
    ]


def build(ctx):
    T = ctx.text
    specs = [
        ("01-economy", "economy", MONEY,
         T(ro="Economia", en="The Economy", pt="A Economia"),
         T(ro="Creșterea reală, venitul pe locuitor, inflația și șomajul modelat în seria comparabilă a Băncii Mondiale.",
           en="Real growth, income per person, consumer inflation and modelled unemployment in comparable World Bank series.",
           pt="Crescimento real, renda por pessoa, inflação e desemprego modelado em séries comparáveis do Banco Mundial."),
         T(ro="Patru panouri despre creștere, PIB pe locuitor, inflație și șomajul modelat de OIM; definițiile naționale rămân separate.",
           en="Four panels show growth, GDP per person, inflation and ILO-modelled unemployment; national statistical definitions remain distinct.",
           pt="Quatro painéis mostram crescimento, PIB por pessoa, inflação e desemprego modelado pela OIT; definições nacionais ficam separadas."),
         "macro/economy.csv", "gdp_growth_pct", "pct_s",
         ["macro/economy.csv", "world/world.csv"]),
        ("02-fiscal", "fiscal", MONEY,
         T(ro="Finanțele publice", en="Public Finances", pt="Finanças Públicas"),
         T(ro="Două ediții distincte FMI: FPP decembrie 2025 pentru venituri, cheltuieli, soldul primar și dobânzi; WEO octombrie 2026 pentru deficit și datorie.",
           en="Two separately identified IMF releases: December 2025 FPP for revenue, spending, primary balance and interest; October 2026 WEO for deficit and debt.",
           pt="Duas edições distintas do FMI: FPP de dezembro de 2025 para receitas, despesas, saldo primário e juros; WEO de outubro de 2026 para déficit e dívida."),
         T(ro="Patru panouri de finanțe publice pe metodologia FMI, cu edițiile FPP și WEO semnalate separat; nu sunt datele execuției bugetului național BNS.",
           en="Four fiscal panels identify FPP and WEO vintages separately; they do not represent the BNS national cash-budget execution.",
           pt="Quatro painéis fiscais identificam separadamente as edições FPP e WEO; não representam a execução de caixa do orçamento nacional do BNS."),
         "fiscal/weo_bal_debt.csv", "debt_pct_gdp", "pct_gdp",
         ["fiscal/weo_bal_debt.csv", "fiscal/fpp_finances.csv"]),
        ("03-spending", "spending", MONEY,
         T(ro="Cheltuielile și investițiile", en="Spending & Investment",
           pt="Despesas e Investimentos"),
         T(ro="Investițiile totale din WDI sunt observate; funcțiile bugetului în lei nu au fost încă convertite printr-un PIB compatibil.",
           en="Whole-economy investment is observed in WDI; national spending functions in MDL are not divided by unverified GDP denominators.",
           pt="O investimento da economia é observado no WDI; as funções do orçamento em MDL não são divididas por PIB sem compatibilidade comprovada."),
         T(ro="Un panou arată investițiile brute în capital fix; trei panouri rămân în așteptare, pentru că execuția de casă nu este echivalentă cu cheltuielile guvernului general.",
           en="One panel shows gross fixed capital formation; three are pending because cash-budget execution is not general-government investment.",
           pt="Um painel mostra a formação bruta de capital fixo; três seguem pendentes porque a execução de caixa não é investimento do governo geral."),
         "macro/economy.csv", "gfcf_pct_gdp", "pct_gdp",
         ["macro/economy.csv", "fiscal/public_budget.csv"]),
        ("04-trade", "trade", WORLD,
         T(ro="Comerțul exterior", en="Trade", pt="Comércio Exterior"),
         T(ro="Exporturile și importurile de bunuri și servicii, în conturile naționale WDI, nu fluxurile vamale doar de mărfuri.",
           en="Goods and services in WDI national accounts, not goods-only customs flows.",
           pt="Bens e serviços nas contas nacionais WDI, não apenas mercadorias das alfândegas."),
         T(ro="Exporturile și importurile ca pondere în PIB și balanța calculată între ele folosesc aceeași ediție WDI; destinațiile exporturilor de mărfuri rămân de verificat.",
           en="Exports and imports as a GDP share and their computed balance share one WDI vintage; goods-export destinations remain unverified.",
           pt="Exportações e importações como parcela do PIB e seu saldo calculado usam a mesma edição WDI; destinos das mercadorias seguem sem validação."),
         "trade/trade.csv", "imports_pct_gdp", "pct_gdp",
         ["trade/trade.csv"]),
        ("05-markets", "markets", MONEY,
         T(ro="Piețele și leul", en="Markets & the Leu", pt="Mercados e o Leu"),
         T(ro="Rata BNM medie ponderată cu zilele de valabilitate și cursul mediu MDL/USD; inflația provine din WDI.",
           en="NBM calendar-day-weighted base rate and average MDL/USD, compared with WDI annual CPI inflation.",
           pt="Taxa BNM ponderada pelos dias de vigência e câmbio médio MDL/USD, junto à inflação anual WDI."),
         T(ro="Rata de bază și inflația sunt două definiții distincte; leul este indexat în raport cu dolarul SUA din 2006. Randamentele la zece ani și indicele bursier rămân în așteptare.",
           en="The observed base rate and inflation have separate definitions; the leu is indexed against the dollar from 2006. Ten-year yields and equities remain pending.",
           pt="Taxa básica e inflação têm definições separadas; o leu é indexado frente ao dólar desde 2006. Títulos de dez anos e ações seguem pendentes."),
         "markets/policy.csv", "policy_mean_pct", "pct",
         ["markets/policy.csv", "markets/usd_mdl.csv", "macro/economy.csv"]),
        ("06-credit", "credit", MONEY,
         T(ro="Creditul gospodăriilor", en="Household Credit", pt="Crédito das Famílias"),
         T(ro="Datoria gospodăriilor, dobânzile la împrumuturi și creditele neperformante necesită aceeași definiție a debitorului și a stocului.",
           en="Household debt, household lending rates and non-performing loan ratios need borrower-consistent original sources.",
           pt="Dívida das famílias, taxas de empréstimos e crédito inadimplente exigem fontes originais com definições coerentes do tomador."),
         T(ro="Cele trei panouri canonice sunt declarate în așteptare: nu sunt înlocuite prin creditul întregului sector privat.",
           en="All three canonical slots are explicitly pending; aggregate private credit is not substituted for household borrowing.",
           pt="Os três painéis canônicos estão explicitamente pendentes; crédito privado agregado não substitui endividamento familiar."),
         None, None, None, []),
        ("07-people", "people", PEOPLE,
         T(ro="Veniturile și inegalitatea", en="People & Inequality",
           pt="Pessoas e Desigualdade"),
         T(ro="Coeficientul Gini WDI este un sondaj armonizat; sărăcia absolută BNS după consum este observată din 2014, cu revizuire a anchetei în 2019. Salariul minim rămâne nevalidat.",
           en="WDI's harmonised survey Gini is observed; BNS consumption-based national absolute poverty is observed from 2014 with a 2019 household-survey method break. The legal minimum wage remains unverified.",
           pt="O Gini harmonizado do WDI está disponível; a pobreza absoluta BNS por consumo é observada desde 2014, com mudança metodológica em 2019. O salário mínimo ainda precisa de auditoria."),
         T(ro="Gini din sondaje este observat până în 2024; sărăcia BNS este afișată în două perioade neconectate (2014–2018 și 2019–2025); salariul minim în USD rămâne în așteptare.",
           en="Survey Gini is observed through 2024; BNS poverty is shown in disconnected 2014–2018 and 2019–2025 periods; USD minimum wage is pending.",
           pt="O Gini da pesquisa vai até 2024; pobreza BNS aparece em dois períodos não conectados, 2014–2018 e 2019–2025; salário mínimo em dólares segue pendente."),
         "people/gini.csv", "gini", "dec2",
         ["people/gini.csv", "people/absolute_poverty.csv"]),
        ("08-world", "world", WORLD,
         T(ro="Moldova în lume", en="Moldova in the World", pt="Moldávia no Mundo"),
         T(ro="PIB-ul nominal și rezervele din WDI sunt în dolari SUA; IDU și indicele percepției corupției au încă surse de verificat.",
           en="Nominal GDP and reserves come from WDI's US-dollar series; HDI and corruption-index vintages remain unverified.",
           pt="PIB nominal e reservas vêm do WDI em dólares; as edições do IDH e do índice de percepção da corrupção ainda precisam de verificação."),
         T(ro="PIB-ul nominal și rezervele sunt observate; indicele dezvoltării umane și indicele percepției corupției rămân marcate în așteptare.",
           en="GDP and reserves are observed; the Human Development Index and Corruption Perceptions Index remain explicitly pending.",
           pt="PIB e reservas são observados; IDH e Índice de Percepção da Corrupção permanecem explicitamente pendentes."),
         "world/world.csv", "gdp_usd", "usd_bn",
         ["world/world.csv"]),
        ("09-demography", "demography", PEOPLE,
         T(ro="Demografia", en="Demography", pt="Demografia"),
         T(ro="Populația la mijlocul anului în seria WDI/ONU nu este identică cu persoanele cu reședință obișnuită din recensământul BNS.",
           en="WDI/UN mid-year population is not the same statistic as the BNS usual-resident census.",
           pt="A população WDI/ONU no meio do ano não é a mesma estatística do censo BNS de residentes habituais."),
         T(ro="Patru panouri prezintă populația indexată, fertilitatea, natalitatea și mortalitatea, creșterea naturală și migrația netă modelată pe o bază demografică comună.",
           en="Four panels cover indexed population, fertility, births and deaths, natural change and UN-modelled migration on a consistent population denominator.",
           pt="Quatro painéis mostram população indexada, fecundidade, nascimentos e mortes, crescimento natural e migração modelada com denominador populacional coerente."),
         "demography/demography.csv", "population", "pop_mn",
         ["demography/demography.csv", "migration/migration.csv"]),
        ("10-security", "security", PEOPLE,
         T(ro="Siguranța publică", en="Security", pt="Segurança"),
         T(ro="Omuciderile, sinuciderile și decesele rutiere au definiții și ani finali diferiți în seriile UNODC/OMS prin WDI.",
           en="Homicides, suicides and road deaths from UNODC/WHO via WDI stop in different years.",
           pt="Homicídios, suicídios e mortes no trânsito das séries UNODC/OMS via WDI terminam em anos diferentes."),
         T(ro="Trei panouri de rate la 100.000 de persoane: omucideri până în 2023, sinucideri până în 2021 și decese rutiere până în 2019; golurile nu sunt completate.",
           en="Three rates per 100,000: homicide through 2023, suicide through 2021 and road deaths through 2019; absent years are not interpolated.",
           pt="Três taxas por 100 mil habitantes: homicídios até 2023, suicídios até 2021 e mortes no trânsito até 2019; anos ausentes não são interpolados."),
         "security/security.csv", "homicide_per_100k", "per100k2",
         ["security/security.csv"]),
        ("11-mortality", "mortality", PEOPLE,
         T(ro="Mortalitatea", en="Mortality", pt="Mortalidade"),
         T(ro="Rata brută a deceselor și speranța de viață sunt estimate din WDI; decesele excedentare cer numărări anuale compatibile.",
           en="Crude death rates and life expectancy are WDI observations; excess deaths need compatible annual death counts.",
           pt="Taxas brutas de mortalidade e expectativa de vida vêm do WDI; excesso de mortes exige contagens anuais compatíveis."),
         T(ro="Rata brută a mortalității și speranța de viață sunt observate; decesele excedentare și COVID-19 după cauza principală rămân în așteptare.",
           en="Crude death rates and life expectancy are available; excess and underlying-cause COVID-19 deaths are pending.",
           pt="Taxa bruta de mortalidade e expectativa de vida estão disponíveis; excesso de mortes e COVID-19 como causa básica seguem pendentes."),
         "mortality/mortality.csv", "death_rate_per_1000", "dec2",
         ["mortality/mortality.csv"]),
        ("12-migration", "migration", PEOPLE,
         T(ro="Migrația", en="Migration", pt="Migração"),
         T(ro="Migrația netă modelată de ONU și stocul de migranți internaționali nu sunt aceleași date cu înregistrările naționale.",
           en="UN-modelled net migration and international migrant stock are not national arrival/departure registers.",
           pt="Migração líquida modelada pela ONU e estoque de migrantes internacionais não são registros nacionais de entradas e saídas."),
         T(ro="Migrația netă folosește populația WDI din același an; stocul ONU este afișat doar ca instantanee 2010, 2015, 2020 și 2024, fără interpolare.",
           en="Net migration uses same-year WDI population; UN migrant stock is shown only at 2010, 2015, 2020 and 2024, without interpolation.",
           pt="A migração líquida usa a população WDI do mesmo ano; o estoque da ONU aparece apenas em 2010, 2015, 2020 e 2024, sem interpolação."),
         "migration/migration.csv", "net_migration", "count",
         ["migration/migration.csv", "demography/demography.csv"]),
    ]
    rows = []
    for ident, topic, family, title, blurb, alt, path, column, fmt, sources in specs:
        pairs = ctx.col(path, column) if path and column else []
        if topic == "world":
            pairs = [(y, v / 1e9) for y, v in pairs]
        if topic == "demography":
            pairs = [(y, v / 1e6) for y, v in pairs]
        if topic == "migration":
            pairs = _net_migration_rate(ctx)
            fmt = "dec2"
        if topic == "markets":
            # A real rate, not the year-end policy setting.
            assert column == "policy_mean_pct"
        stats = [ctx.stat(title, pairs, fmt, kind="level")] if pairs else []
        rows.append({
            "id": ident, "topic": topic, "n": ident[:2], "family": family,
            "title": title, "blurb": blurb, "alt": alt, "spark": pairs,
            "stats": [s for s in stats if s],
            "sources": sources,
        })
    return rows
