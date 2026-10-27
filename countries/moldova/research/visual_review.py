"""Build deterministic trilingual Moldova review sheets from validated assets.

Read-only: no source downloads, chart rerendering, registry edits or deploy.
The JSON report SHA256-pins each PNG, SVG and thumbnail for human review.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

TOPICS = (
    "economy", "fiscal", "spending", "trade", "markets", "credit",
    "people", "world", "demography", "security", "mortality", "migration",
)
LOCALES = ("ro", "en", "pt")
PANEL_WIDTH = 680
HEADER = 34
PADDING = 10
REQUIRED_LINEAGE = {
    "01-economy": {"macro/economy.csv", "macro/national_lfs.csv", "world/world.csv"},
    "03-spending": {
        "fiscal/public_budget.csv", "fiscal/nominal_gdp_bns.csv",
        "macro/economy.csv",
    },
    "12-migration": {
        "migration/foreign_born_census.csv", "migration/migration.csv",
        "demography/demography.csv",
    },
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_review(country: Path, destination: Path) -> dict:
    """Generate twelve same-scale RO/EN/PT triptychs and a hash manifest."""
    src = country / "output"
    proven = json.loads((country / "provenance.json").read_text(encoding="utf-8"))
    for plate, required in REQUIRED_LINEAGE.items():
        observed = set(proven.get(plate, ()))
        if not required <= observed:
            raise AssertionError(
                f"{plate}: missing original source(s): {sorted(required-observed)}")
    expected = {
        f"{i:02d}-{topic}{'' if lang == 'en' else '.' + lang}.{ext}"
        for i, topic in enumerate(TOPICS, 1)
        for lang in LOCALES for ext in ("png", "svg")
    }
    found = {
        p.name for p in src.iterdir()
        if p.is_file() and p.suffix in (".png", ".svg")
    }
    if expected != found:
        raise AssertionError(
            f"Plate inventory differs: missing {sorted(expected-found)}, "
            f"extra {sorted(found-expected)}")
    thumbs = {p.name for p in (src / "thumbs").glob("*.png")}
    expected_thumbs = {p for p in expected if p.endswith(".png")}
    if thumbs != expected_thumbs:
        raise AssertionError(
            f"Thumb inventory differs: missing {sorted(expected_thumbs-thumbs)}, "
            f"extra {sorted(thumbs-expected_thumbs)}")

    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "method": "same-scale PNG contact sheets; review only, no publication",
        "provenance_sha256": _digest(country / "provenance.json"),
        "plates": [],
    }
    for i, topic in enumerate(TOPICS, 1):
        stem = f"{i:02d}-{topic}"
        entries, dimensions, previews = [], [], []
        for locale in LOCALES:
            suffix = "" if locale == "en" else f".{locale}"
            name = f"{stem}{suffix}.png"
            png, svg = src / name, src / f"{stem}{suffix}.svg"
            thumb = src / "thumbs" / name
            with Image.open(png) as image:
                image.verify()
            with Image.open(thumb) as image:
                image.verify()
            with Image.open(png) as image:
                dimensions.append(image.size)
                scaled_height = round(image.height * PANEL_WIDTH / image.width)
                previews.append(image.convert("RGB").resize(
                    (PANEL_WIDTH, scaled_height), Image.Resampling.LANCZOS))
            entries.append({
                "locale": locale, "png": name, "png_sha256": _digest(png),
                "svg_sha256": _digest(svg), "thumb_sha256": _digest(thumb),
                "image_size": list(dimensions[-1]),
            })
        if (max(w for w, _ in dimensions) - min(w for w, _ in dimensions) > 2
                or max(h for _, h in dimensions) -
                min(h for _, h in dimensions) > 2):
            raise AssertionError(
                f"{stem}: locales rendered at unequal dimensions: {dimensions}")
        height = max(im.height for im in previews)
        contact = Image.new(
            "RGB",
            (len(LOCALES) * (PANEL_WIDTH + PADDING) + PADDING,
             HEADER + height + PADDING), "#e6e8ea")
        draw = ImageDraw.Draw(contact)
        for col, (locale, im) in enumerate(zip(LOCALES, previews)):
            x = PADDING + col * (PANEL_WIDTH + PADDING)
            draw.text(
                (x, 10), f"{stem} | {locale.upper()} | same x/y-scale",
                fill="#16212a")
            contact.paste(im, (x, HEADER))
        filename = f"{stem}-ro-en-pt.png"
        contact.save(destination / filename, optimize=True)
        manifest["plates"].append({
            "stem": stem, "sheet": filename,
            "observed_sources": proven[stem], "locales": entries,
        })
    (destination / "visual-review-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(
        f"Moldova visual QA: {len(manifest['plates'])} trilingual sheets / "
        "108 original assets hashed")
    return manifest


def main() -> None:
    build_review(
        Path(__file__).resolve().parents[1],
        Path("/tmp/moldova-visual-review"),
    )


if __name__ == "__main__":
    main()
