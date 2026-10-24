"""Country timeline for Ukraine's statistical-coverage annotations.

These are dated historical context markers, not a national dataset or
causal model. Distinguish Ukraine's internationally recognized territory
from the changing actual scope of statistical measurement.
"""
from __future__ import annotations

# Short English labels translated at rendering time by i18n.json.
EVENTS = {
    2008: "Global financial crisis",
    2014: "Crimea occupied; conflict in Donbas",
    2020: "COVID-19 pandemic",
    2022: "Russia's full-scale invasion",
}

# Dataset-specific *measurement* seams. These are not a chronological
# claim that a territory joined or left Ukraine in law.
MEASUREMENT_BREAKS = {
    "macro/gdp_growth.csv": (2014, 2022),
    "macro/gdp_nominal.csv": (2014, 2022),
    "macro/cpi.csv": (2014, 2022),
    "trade/trade_na.csv": (2014, 2022),
    "spending/investment.csv": (2014, 2022),
}
