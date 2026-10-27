"""Fail closed on Moldova's trilingual draft assets before archive.

Run after core.render, core.thumbs and core.provenance in an isolated runner.
This checks actual Matplotlib SVG text, all plate/thumbnail files, and data
lineage independently of the provenance tracer; it never deploys.
"""
from __future__ import annotations

import ast
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from PIL import Image
import yaml

COUNTRY = Path(__file__).resolve().parents[1]
OUTPUT = COUNTRY / "output"
LOCALES = ("en", "ro", "pt")
TOPICS = (
    "economy", "fiscal", "spending", "trade", "markets", "credit",
    "people", "world", "demography", "security", "mortality", "migration",
)
# Matplotlib renders text as glyph paths but keeps human-readable labels
# in <!-- ... --> comments. Inspect these, not merely the source catalog.
COMMENTS = re.compile(r"<!--\s*([^\r\n]*?)\s*-->")
ENGLISH_WORD = re.compile(r"[A-Za-z]")
CORE_FOOTER = "worldreports.io/moldova · "


def require(test: bool, why: str) -> None:
    if not test:
        raise AssertionError(why)


def names(locale: str, ext: str) -> set[str]:
    suffix = "" if locale == "en" else f".{locale}"
    return {f"{i:02d}-{topic}{suffix}.{ext}"
            for i, topic in enumerate(TOPICS, 1)}


def audit_files() -> None:
    """Require exactly 36 complete SVG/PNG plates and 36 useful thumbnails."""
    for ext in ("png", "svg"):
        expected = set().union(*(names(lang, ext) for lang in LOCALES))
        found = {p.name for p in OUTPUT.glob(f"*.{ext}")}
        require(found == expected,
                f"{ext} inventory differs: missing={sorted(expected-found)}, "
                f"unexpected={sorted(found-expected)}")
    expected = set().union(*(names(lang, "png") for lang in LOCALES))
    found = {p.name for p in (OUTPUT / "thumbs").glob("*.png")}
    require(found == expected,
            f"Thumbs differ: missing={sorted(expected-found)}, "
            f"unexpected={sorted(found-expected)}")
    for filename in sorted(expected):
        with Image.open(OUTPUT / filename) as plate, Image.open(
                OUTPUT / "thumbs" / filename) as thumb:
            w, h = plate.size
            sw, sh = thumb.size
            require(w >= 1000 and h >= 600 and 0 < sw < w and 0 < sh < h,
                    f"{filename}: plate/thumb sizes {plate.size}/{thumb.size}")
            plate.verify()
            thumb.verify()


def visible_svg(path: Path) -> tuple[set[str], set[str]]:
    """Return text labels and element IDs from one well-formed plate."""
    source = path.read_text(encoding="utf-8")
    visible = {html.unescape(m.group(1).strip())
               for m in COMMENTS.finditer(source)}
    svg = ET.fromstring(source)
    require(svg.tag.endswith("}svg"), f"{path.name}: not an SVG")
    require(svg.attrib.get("viewBox") == "0 0 1152 734.4",
            f"{path.name}: unexpected SVG coordinate system")
    ids = {element.attrib["id"] for element in svg.iter()
           if "id" in element.attrib}
    require(len(visible) >= 10,
            f"{path.name}: missing rendered text/glyph comments")
    return visible, ids


def audit_visible_locales() -> None:
    """Every English text token must be cataloged and actually translated."""
    catalog = json.loads((COUNTRY / "i18n.json").read_text(encoding="utf-8"))
    require(bool(catalog) and all(set(v) == {"ro", "pt"} for v in catalog.values()),
            "All Moldova catalog keys must have ro and pt translations")
    reviewed = 0
    for number, topic in enumerate(TOPICS, 1):
        stem = f"{number:02d}-{topic}"
        english, english_ids = visible_svg(OUTPUT / f"{stem}.svg")
        localized = {lang: visible_svg(OUTPUT / f"{stem}.{lang}.svg")
                     for lang in ("ro", "pt")}
        slots = {name for name in english_ids if name.startswith(f"{topic}.")}
        require(len(slots) >= 3, f"{stem}: incomplete spine panels: {sorted(slots)}")
        for lang, (_, ids) in localized.items():
            require(slots <= ids,
                    f"{stem}.{lang}: missing spine slots: {sorted(slots-ids)}")
        prose = {label for label in english if ENGLISH_WORD.search(label)
                 and not label.startswith(CORE_FOOTER)}
        require(prose <= catalog.keys(),
                f"{stem}: uncataloged visible English labels: {sorted(prose-catalog.keys())}")
        for label in prose:
            for lang, (labels, _) in localized.items():
                expected = catalog[label][lang]
                require(bool(expected), f"{stem}.{lang}: empty catalog value {label!r}")
                require(expected in labels,
                        f"{stem}.{lang}: absent translated text {expected!r} ({label!r})")
                if expected != label:
                    require(label not in labels,
                            f"{stem}.{lang}: untranslated English text {label!r}")
        reviewed += len(prose)
    print(f"SVG localization gate: 36 panels rendered; {reviewed} English "
          "text labels audited against Romanian and Portuguese SVG content")


def ast_sources() -> dict[str, set[str]]:
    """Independent data-lineage audit: literal table calls in each builder."""
    tree = ast.parse((COUNTRY / "plates.py").read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("plate_"):
            continue
        topic = node.name.removeprefix("plate_")
        if topic not in TOPICS:
            continue
        sources: set[str] = set()
        for call in ast.walk(node):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
                continue
            if call.func.id not in {"_series", "_aligned"}:
                continue
            require(len(call.args) > 1 and isinstance(call.args[1], ast.Constant)
                    and isinstance(call.args[1].value, str),
                    f"{node.name}: a dynamic CSV path escapes the static source audit")
            sources.add(call.args[1].value)
        found[topic] = sources
    require(set(found) == set(TOPICS),
            f"Missing data-lineage builders: {sorted(set(TOPICS)-set(found))}")
    return found


def audit_source_lineage() -> None:
    observed = json.loads((COUNTRY / "provenance.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((COUNTRY / "SOURCES.yaml").read_text(encoding="utf-8"))
    refs = ast_sources()
    expected = {f"{i:02d}-{topic}": sorted(refs[topic])
                for i, topic in enumerate(TOPICS, 1)}
    require(observed == expected,
            f"Rendered provenance disagrees with chart data reads: "
            f"observed={observed}, expected={expected}")
    traced = {file for paths in expected.values() for file in paths}
    for path in sorted(traced):
        group, name = path.split("/", 1)
        require((COUNTRY / "data" / path).is_file(),
                f"Referenced chart CSV missing: {path}")
        entry = manifest.get(group, {}).get(name)
        require(isinstance(entry, dict) and bool(entry.get("source"))
                and bool(entry.get("url")) and isinstance(entry.get("official"), bool),
                f"Missing publisher, URL, or official status in SOURCES.yaml: {path}")
        require("_from_" not in name,
                f"Unreviewed importer sidecar referenced by plate: {path}")
    print(f"Provenance gate: 12 exact source-to-plate mappings; "
          f"{len(traced)} traced CSVs with publisher metadata")


def main() -> None:
    active = COUNTRY / "country.yaml"
    if active.exists():
        draft = COUNTRY / "research" / "country_candidate.yaml"
        require(active.read_bytes() == draft.read_bytes(),
                "Only the temporary exact research candidate may be registered")
    audit_files()
    audit_visible_locales()
    audit_source_lineage()
    print("Moldova pre-publication asset gate PASS; no merge or deployment")


if __name__ == "__main__":
    main()
