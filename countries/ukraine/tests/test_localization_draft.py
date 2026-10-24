"""Offline translation-contract tests for the Ukraine atlas draft.

No external rendering dependencies or network. Genuine Ukrainian text and
all canonical spine terms are required before country registration.
"""
from __future__ import annotations

import ast
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent


def module(name, filename):
    spec = spec_from_file_location(name, ROOT / filename)
    result = module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


plates = module("ukr_localized_plates", "plates.py")
chapters = module("ukr_localized_chapters", "chapters.py")
catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
ui = json.loads((ROOT / "ui.json").read_text(encoding="utf-8"))


class UkraineLocalizationTests(unittest.TestCase):
    def test_all_twelve_chapter_texts_are_native(self):
        self.assertEqual(len(chapters.CARDS), 12)
        for _, topic, _, title, blurb in chapters.CARDS:
            with self.subTest(topic=topic):
                self.assertTrue(all(title))
                self.assertTrue(all(blurb))
                self.assertNotEqual(title[0], title[1])
                self.assertNotEqual(title[0], title[2])
                self.assertEqual(set(chapters._lang(title)), {"en", "uk", "pt"})

    def test_plate_titles_subtitles_and_accessibility_copy_translated(self):
        for plate in plates.PLATES:
            with self.subTest(plate=plate["slug"]):
                for field in ("title", "subtitle", "alt", "source"):
                    key = plate[field]
                    self.assertIn(key, catalog, f"missing {field}: {key}")
                    self.assertTrue(catalog[key].get("uk"), key)
                    self.assertTrue(catalog[key].get("pt"), key)

    def test_spine_panel_indicators_and_units_have_both_locales(self):
        tree = ast.parse((REPO / "core" / "spine.py").read_text(encoding="utf-8"))
        required = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == "_c":
                indicator, unit = node.args[1:3]
                if isinstance(indicator, ast.Constant):
                    required.add(indicator.value)
                if isinstance(unit, ast.Constant):
                    required.add(unit.value)
            elif node.func.id == "_lens":
                for kw in node.keywords:
                    if kw.arg == "unit" and isinstance(kw.value, ast.Constant):
                        required.add(kw.value.value)
        for key in sorted(required):
            with self.subTest(text=key):
                self.assertIn(key, catalog)
                self.assertTrue(catalog[key].get("uk"))
                self.assertTrue(catalog[key].get("pt"))

    def test_ui_has_unavailable_evidence_in_every_language(self):
        self.assertEqual(set(ui), {"en", "uk", "pt"})
        for locale, doc in ui.items():
            with self.subTest(locale=locale):
                self.assertTrue(doc["line"])
                self.assertTrue(doc["dek"])
                self.assertGreaterEqual(len(doc["notes"]), 3)
                self.assertGreaterEqual(len(doc["colophon"]), 2)
                self.assertGreaterEqual(len(doc["unavailable"]), 5)
                for item in doc["unavailable"]:
                    self.assertTrue(item["term"])
                    self.assertTrue(item["detail"])

    def test_ukrainian_glyphs_are_real_text_not_english_placeholders(self):
        for key in ("Real GDP growth", "Research pending: definition or coverage not verified"):
            self.assertIn(key, catalog)
            self.assertRegex(catalog[key]["uk"], "[А-Яа-яІіЇїЄєҐґ]")
            self.assertNotEqual(catalog[key]["pt"], key)

    def test_no_mixed_or_lost_translation_entry(self):
        for key, translations in catalog.items():
            with self.subTest(key=key):
                self.assertIsInstance(key, str)
                self.assertEqual(set(translations), {"uk", "pt"})
                self.assertTrue(all(isinstance(v, str) and v.strip()
                                    for v in translations.values()))


if __name__ == "__main__":
    unittest.main()
