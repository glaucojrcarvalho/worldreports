"""Ukraine chapter cards and verified headline metrics, research-stage.

One summary card per canonical plate. All figures read the same reviewed
country CSVs as the plots. No USD GDP, unemployment or government investment
is inferred from incompatible or unreviewed Ukrainian statistics.
"""
from __future__ import annotations

MONEY, WORLD, PEOPLE = "money", "world", "people"

# Each entry is a chapter id, spine topic, visual family and localized copy.
CARDS = (
    ("01_economy", "economy", MONEY,
     ("Ukraine's Economy", "Економіка України", "Economia da Ucrânia"),
     ("Real growth and annual-average consumer prices. Income and unemployment need compatible records.",
      "Реальне зростання та середньорічні споживчі ціни. Дані про доходи й безробіття потребують перевірки.",
      "Crescimento real e preços médios anuais. Renda e desemprego exigem séries compatíveis.")),
    ("02_fiscal", "fiscal", MONEY,
     ("Government Finances", "Державні фінанси", "Finanças públicas"),
     ("Comparable general-government fiscal measures are being verified, not substituted by cash-budget data.",
      "Показники сектору загального державного управління перевіряються; касові показники бюджету їх не замінюють.",
      "Contas consolidadas do governo geral em verificação, sem substituí-las por execução orçamentária de caixa.")),
    ("03_spending", "spending", MONEY,
     ("Spending and Investment", "Видатки та інвестиції", "Gastos e investimento"),
     ("Economy-wide fixed investment is observed; government investment and functional spending are separate.",
      "Валові інвестиції всієї економіки доступні; державні інвестиції й видатки за функціями — інші показники.",
      "O investimento da economia está verificado; investimento e gastos públicos são indicadores distintos.")),
    ("04_trade", "trade", WORLD,
     ("Trade in Goods and Services", "Торгівля товарами та послугами", "Comércio de bens e serviços"),
     ("National-accounts exports and imports are not customs goods-only trade.",
      "Експорт та імпорт за національними рахунками не тотожні митній статистиці торгівлі товарами.",
      "Exportações e importações das contas nacionais não equivalem ao comércio aduaneiro de mercadorias.")),
    ("05_markets", "markets", MONEY,
     ("Currency and Markets", "Валюта й фінансові ринки", "Moeda e mercados"),
     ("The official hryvnia exchange rate is measured; sovereign bonds and shares are still under review.",
      "Офіційний курс гривні перевірено; державні облігації та акції ще потребують перевірки.",
      "O câmbio oficial da hryvnia foi validado; títulos soberanos e ações seguem em análise.")),
    ("06_credit", "credit", MONEY,
     ("Credit and Household Debt", "Кредитування та борги домогосподарств", "Crédito e dívida familiar"),
     ("Household and banking-sector credit definitions require a compatible series.",
      "Для боргів домогосподарств і банківських кредитів потрібні порівнювані ряди даних.",
      "Dívida das famílias e crédito bancário exigem séries de definições comparáveis.")),
    ("07_people", "people", PEOPLE,
     ("Inequality, Poverty and Wages", "Нерівність, бідність і заробітна плата", "Desigualdade, pobreza e salários"),
     ("Household survey coverage was disrupted during the full-scale invasion; missing values are not zero.",
      "Під час повномасштабного вторгнення обстеження домогосподарств було порушено; пропуски не означають нуль.",
      "A invasão em larga escala interrompeu pesquisas domiciliares; ausência de dados não significa zero.")),
    ("08_world", "world", WORLD,
     ("Ukraine in the World", "Україна у світі", "Ucrânia no mundo"),
     ("Official reserves are verified; comparable GDP, human development and corruption sources remain under review.",
      "Офіційні резерви перевірено; зіставні показники ВВП, людського розвитку й корупції ще аналізуються.",
      "Reservas oficiais verificadas; PIB comparável, desenvolvimento humano e corrupção seguem em análise.")),
    ("09_demographics", "demography", PEOPLE,
     ("Population and Demography", "Населення й демографія", "População e demografia"),
     ("Official January-1 present population is observed through 2022; 2023–2025 are suppressed and 2015 changes geographic scope.",
      "Офіційну оцінку наявного населення на 1 січня опубліковано до 2022 року; дані 2023–2025 років приховано, а у 2015 році змінилося територіальне охоплення.",
      "A população presente estimada em 1.º de janeiro está disponível até 2022; 2023–2025 estão suprimidos e a cobertura muda em 2015.")),
    ("10_security", "security", PEOPLE,
     ("Security and Safety", "Безпека", "Segurança"),
     ("Police-recorded crime, mortality and conflict casualties cannot be merged into one series.",
      "Поліцейську статистику злочинів, смертність і втрати через війну не можна об'єднувати в один ряд.",
      "Crimes registrados pela polícia, mortalidade e vítimas da guerra não são uma única série.")),
    ("11_mortality", "mortality", PEOPLE,
     ("Mortality and Causes of Death", "Смертність і причини смерті", "Mortalidade e causas de morte"),
     ("Civil-registration completeness, causes of death and pandemic definitions remain under review.",
      "Повнота реєстрації смертей, причини смерті й визначення пандемічних показників перевіряються.",
      "Completude do registro civil, causas de morte e definições da pandemia seguem em análise.")),
    ("12_migration", "migration", PEOPLE,
     ("Migration and Displacement", "Міграція та переміщення", "Migração e deslocamento"),
     ("Border movements, migration, refugees and internally displaced people must remain distinct.",
      "Перетини кордону, міграцію, біженців і внутрішньо переміщених осіб слід розрізняти.",
      "Travessias de fronteira, migração, refugiados e deslocados internos são medidas diferentes.")),
)


def _lang(triple: tuple[str, str, str]) -> dict[str, str]:
    return dict(en=triple[0], uk=triple[1], pt=triple[2])


def _specs(ctx):
    """Only rows whose observation and unit were independently accepted."""
    return {
        "economy": (
            "macro/gdp_growth.csv", "real_growth",
            [
                (("Real GDP growth", "Реальне зростання ВВП", "Crescimento real do PIB"),
                 "macro/gdp_growth.csv", "real_growth", "pct_s"),
                (("Annual-average CPI inflation", "Середньорічна інфляція", "Inflação média anual"),
                 "macro/cpi.csv", "annual_inflation_pct", "pct"),
            ]),
        "spending": (
            "spending/investment.csv", "gfcf_pct_gdp",
            [(("Whole-economy investment", "Інвестиції всієї економіки", "Investimento da economia"),
              "spending/investment.csv", "gfcf_pct_gdp", "pct_gdp")],
        ),
        "trade": (
            "trade/trade_na.csv", "balance_pct_gdp",
            [
                (("Exports, goods and services", "Експорт товарів і послуг", "Exportações de bens e serviços"),
                 "trade/trade_na.csv", "exports_pct_gdp", "pct_gdp"),
                (("Imports, goods and services", "Імпорт товарів і послуг", "Importações de bens e serviços"),
                 "trade/trade_na.csv", "imports_pct_gdp", "pct_gdp"),
                (("Trade balance, goods and services", "Баланс торгівлі товарами та послугами", "Saldo de bens e serviços"),
                 "trade/trade_na.csv", "balance_pct_gdp", "pct_gdp_s"),
            ]),
        "demography": (
            "social/population.csv", "population_persons",
            [(("Present population on 1 January", "Наявне населення на 1 січня", "População presente em 1.º de janeiro"),
              "social/population.csv", "population_persons", "count")],
        ),
        "world": (
            "macro/reserves.csv", "usd_bn",
            [(("Official reserves, year-end", "Офіційні резерви на кінець року", "Reservas oficiais no fim do ano"),
              "macro/reserves.csv", "usd_bn", "usd_bn")],
        ),
        "markets": (
            "markets/policy_rate.csv", "policy_rate_eoy_pct",
            [
                (("NBU policy rate, year-end", "Облікова ставка НБУ на кінець року", "Taxa básica do BNU no fim do ano"),
                 "markets/policy_rate.csv", "policy_rate_eoy_pct", "pct2"),
                (("Official UAH per US dollar", "Офіційний курс гривні за долар США", "Taxa oficial UAH por dólar"),
                 "markets/fx.csv", "avg_uah_per_usd", "dec2"),
            ],
        ),
    }


def headline(ctx) -> list[dict]:
    return [
        ctx.stat(_lang(("Real GDP growth", "Реальне зростання ВВП", "Crescimento real do PIB")),
                 ctx.col("macro/gdp_growth.csv", "real_growth"), "pct_s"),
        ctx.stat(_lang(("Annual-average CPI inflation", "Середньорічна інфляція", "Inflação média anual")),
                 ctx.col("macro/cpi.csv", "annual_inflation_pct"), "pct"),
        ctx.stat(_lang(("Trade balance, goods and services", "Баланс торгівлі товарами та послугами", "Saldo de bens e serviços")),
                 ctx.col("trade/trade_na.csv", "balance_pct_gdp"), "pct_gdp_s"),
        ctx.stat(_lang(("Official reserves, year-end", "Офіційні резерви на кінець року", "Reservas oficiais no fim do ano")),
                 ctx.col("macro/reserves.csv", "usd_bn"), "usd_bn"),
    ]


def build(ctx) -> list[dict]:
    sources = _specs(ctx)
    chapters = []
    for cid, topic, family, title, blurb in CARDS:
        year_series, column, stats = sources.get(topic, (None, None, []))
        cards = [
            ctx.stat(_lang(label), ctx.col(path, col), spec)
            for label, path, col, spec in stats
        ]
        chapters.append({
            "id": cid,
            "topic": topic,
            "n": cid[:2],
            "family": family,
            "title": ctx.text(**_lang(title)),
            "blurb": ctx.text(**_lang(blurb)),
            "spark": ctx.col(year_series, column) if year_series else [],
            "stats": [c for c in cards if c],
            "alt": ctx.text(**_lang((
                f"{title[0]}: source-verified values are shown where available; other indicators remain under review.",
                f"{title[1]}: перевірені показники наведено за наявності; інші перевіряються.",
                f"{title[2]}: séries verificadas aparecem quando disponíveis; os demais indicadores seguem em análise.",
            ))),
        })
    return chapters
