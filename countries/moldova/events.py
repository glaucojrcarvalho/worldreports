"""Only observed publication events: no inferred annual-recession dates.

Events are optional and not painted as causal annotations without matching
verified quarterly recession dating. The 2024 census has a reference date
different from WDI's midyear population; the BNS budget marks 2025 preliminary.
"""
EVENTS = {
    2024: "Census usual residents, 8 April; separate from WDI midyear",
    2025: "National budget execution labelled preliminary",
}
