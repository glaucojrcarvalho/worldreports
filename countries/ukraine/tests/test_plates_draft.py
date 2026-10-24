"""Offline checks for the research-stage Ukraine 12-plate spine builders.

No Matplotlib, external API, or incomplete country registration is needed.
"""
from __future__ import annotations

import ast
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "plates.py"
SPEC = spec_from_file_location("ukraine_plate_draft", PATH)
plates = module_from_spec(SPEC)
SPEC.loader.exec_module(plates)

EXPECTED = (
    ("01_economy", "economy"),
    ("02_fiscal", "fiscal"),
    ("03_spending", "spending"),
    ("04_trade", "trade"),
    ("05_markets", "markets"),
    ("06_credit", "credit"),
    ("07_people", "people"),
    ("08_world", "world"),
    ("09_demographics", "demography"),
    ("10_security", "security"),
    ("11_mortality", "mortality"),
    ("12_migration", "migration"),
)


class UkrainePlateDraftTests(unittest.TestCase):
    def test_exact_twelve_canonical_chapter_declarations(self):
        items = [(x["slug"], x["topic"]) for x in plates.PLATES]
        self.assertEqual(items, list(EXPECTED))
        self.assertEqual(len(items), len(set(items)))
        for plate in plates.PLATES:
            self.assertTrue(callable(plate["builder"]))
            self.assertTrue(plate["title"].startswith("Ukraine"))
            self.assertTrue(plate["subtitle"])
            self.assertTrue(plate["alt"])
            self.assertTrue(plate["source"].startswith("Sources:"))

    def test_no_early_or_cross_country_file_access(self):
        tree = ast.parse(PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("countries."))
            if isinstance(node, ast.Import):
                for name in node.names:
                    self.assertFalse(name.name.startswith("countries."))
        self.assertNotIn("countries/", PATH.read_text(encoding="utf-8"))

    def test_breaks_split_real_measurements(self):
        groups = plates._segments(
            [2012, 2013, 2014, 2015, 2021, 2022, 2024],
            [10, 20, 30, 40, 50, 60, 70],
        )
        self.assertEqual(groups, [
            ([2012, 2013], [10, 20]),
            ([2014, 2015], [30, 40]),
            ([2021], [50]),
            ([2022], [60]),
            ([2024], [70]),
        ])

    def test_only_verified_measurements_have_render_handlers(self):
        import inspect
        src = inspect.getsource(plates._plot)
        for key in (
            "economy.growth",
            "economy.inflation",
            "spending.investment",
            "trade.exports_imports",
            "trade.balance",
            "markets.currency",
        ):
            with self.subTest(key=key):
                self.assertIn(f'key == "{key}"', src)
        self.assertIn("return _missing(ctx, ax)", src)
        # Current-price GDP in million UAH must never masquerade as USD.
        self.assertNotIn('key == "world.gdp"', src)
        self.assertNotIn('key == "spending.public_investment"', src)

    def test_currency_uses_canonical_inverted_2006_index(self):
        import inspect
        src = inspect.getsource(plates._plot)
        self.assertIn('ctx.fx_index((years, values))', src)
        self.assertIn('"avg_uah_per_usd"', src)
        self.assertNotIn('ctx.index_2006((years, values))', src)

    def test_no_country_configuration_until_draft_is_source_complete(self):
        self.assertFalse((ROOT / "country.yaml").exists())
        self.assertTrue((ROOT / "READINESS.md").exists())


if __name__ == "__main__":
    unittest.main()
