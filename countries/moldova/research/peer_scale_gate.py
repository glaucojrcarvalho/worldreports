"""Rebuild *only* peer trade/world plates affected by Moldova's shared axes.

The checkout's published peer data remain the source of truth. The default
mode writes isolated previews under --out, compares against checked-in
images, and produces side-by-side contact sheets plus machine-readable QA.
--stage-for-site changes peer images/thumbs ONLY in an ephemeral Actions
runner, never commits, merges or publishes them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

from core import render, spine
from core.country import Country
from core.thumbs import thumb

ROOT = Path(__file__).resolve().parents[3]
TOPICS = frozenset({"trade", "world"})
AXES = {
    "trade.balance": (-60, 40),
    "world.gdp": (1, 50_000),
    "world.reserves": (0.1, 5_000),
}
SHEET_WIDTH = 1000
ROW_HEIGHT = 254
PREVIEW_WIDTH = 460
PREVIEW_HEIGHT = 218


def verify_axes() -> None:
    """The review is invalid if the shared axis change has been reverted."""
    for name, expected in AXES.items():
        actual = tuple(spine.SLOTS[name].ref)
        if actual != expected:
            raise ValueError(f"{name}: expected shared {expected}, found {actual}")


def peer_plates(country: Country):
    """Locate exactly one shared-spine world and trade plate per peer."""
    selected = [p for p in render.load_plates(country) if p.topic in TOPICS]
    topics = [p.topic for p in selected]
    if sorted(topics) != sorted(TOPICS):
        raise ValueError(f"{country.slug}: expected trade+world, found {topics}")
    if any(not p.filename for p in selected):
        raise ValueError(f"{country.slug}: plate filename not declarative")
    return selected


def _name(plate, locale: str, ext: str) -> str:
    stem = Path(plate.filename).stem
    suffix = "" if locale == "en" else f".{locale}"
    return f"{stem}{suffix}.{ext}"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_png(baseline: Path, rebuilt: Path) -> dict:
    """Compare decoded pixels as well as bytes; file metadata isn't visual."""
    with Image.open(baseline) as b, Image.open(rebuilt) as n:
        # Matplotlib font metrics can add/subtract one raster pixel to
        # tight bounding boxes between runners. Compare the common canvas
        # without concealing a materially different aspect ratio.
        drift = (n.width - b.width, n.height - b.height)
        if any(abs(d) > 3 for d in drift):
            raise ValueError(f"Material image dimension drift: {baseline}: "
                             f"{b.size} vs {n.size}")
        w, height = min(b.width, n.width), min(b.height, n.height)
        box = (0, 0, w, height)
        changed = ImageChops.difference(
            b.convert("RGB").crop(box), n.convert("RGB").crop(box))
        # Luminosity conversion loses some one-channel RGB differences.
        # Compute a per-pixel maximum-channel difference instead: each
        # nonzero mask pixel represents at least one changed RGB channel.
        red, green, blue = changed.split()
        mask = ImageChops.lighter(red, ImageChops.lighter(green, blue))
        changed_pixels = (w * height) - mask.histogram()[0]
        ratio = round(changed_pixels / (w * height) * 100, 3)
        return {
            "baseline_size": list(b.size),
            "rebuilt_size": list(n.size),
            "dimension_drift_px": list(drift),
            "pixel_change_percent": ratio,
            "difference_bbox": list(mask.getbbox()) if mask.getbbox() else None,
            "old_sha256": _digest(baseline),
            "new_sha256": _digest(rebuilt),
        }


def _sheet(heading: str, count: int) -> Image.Image:
    canvas = Image.new("RGB", (SHEET_WIDTH, ROW_HEIGHT * (count + 1)), "#ffffff")
    ImageDraw.Draw(canvas).text((12, 12), heading, fill="#111111")
    ImageDraw.Draw(canvas).text((10, 38),
        "LEFT = committed peer plate | RIGHT = rebuilt with Moldova-compatible shared axes",
        fill="#333333")
    return canvas


def _sheet_row(canvas: Image.Image, row: int, slug: str,
               before: Path, after: Path) -> None:
    top = ROW_HEIGHT * (row + 1)
    draw = ImageDraw.Draw(canvas)
    draw.text((12, top + 5), slug, fill="#111111")
    for col, path in enumerate((before, after)):
        with Image.open(path) as original:
            picture = ImageOps.contain(original.convert("RGB"),
                                       (PREVIEW_WIDTH, PREVIEW_HEIGHT),
                                       Image.Resampling.LANCZOS)
            canvas.paste(picture, (12 + col * 490, top + 27))
    draw.line((0, top + ROW_HEIGHT - 2, SHEET_WIDTH, top + ROW_HEIGHT - 2),
              fill="#cccccc", width=1)


def run(output: Path, stage_for_site: bool = False) -> dict:
    verify_axes()
    if stage_for_site and os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("--stage-for-site is restricted to disposable GitHub Actions runners")
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("--out must be outside the tracked checkout")
    output.mkdir(parents=True, exist_ok=True)
    if (ROOT / "countries/moldova/country.yaml").exists():
        raise ValueError("Moldova was unexpectedly registered; audit published peers separately")

    peers = sorted(Country.all(), key=lambda c: c.slug)
    if len(peers) < 25 or any(c.slug == "moldova" for c in peers):
        raise ValueError(f"Unexpected published peer set: {[c.slug for c in peers]}")
    sheets = {t: _sheet(t, len(peers)) for t in TOPICS}
    observations = []
    for row, country in enumerate(peers):
        selected = peer_plates(country)
        fresh = output / "rebuilt" / country.slug
        problems = render.render_country(
            country, langs=country.locale_codes, out_dir=fresh,
            only={p.name for p in selected}, strict=True)
        if problems:
            raise RuntimeError(f"{country.slug}: {problems}")
        for plate in selected:
            for locale in country.locale_codes:
                filename = _name(plate, locale, "png")
                old = country.dir / "output" / filename
                new = fresh / filename
                old_svg = old.with_suffix(".svg")
                new_svg = new.with_suffix(".svg")
                if not all(p.is_file() for p in (old, new, old_svg, new_svg)):
                    raise FileNotFoundError(
                        f"{country.slug}/{plate.topic}/{locale}: missing baseline or rebuilt PNG/SVG")
                diff = compare_png(old, new)
                observations.append({
                    "country": country.slug,
                    "topic": plate.topic,
                    "locale": locale,
                    "asset": filename,
                    **diff,
                })
                if locale == "en":
                    _sheet_row(sheets[plate.topic], row, country.slug, old, new)
                if stage_for_site:
                    shutil.copy2(new, old)
                    shutil.copy2(new_svg, old_svg)
                    thumb(old, country.dir / "output/thumbs" / filename)

    for topic, canvas in sheets.items():
        canvas.save(output / f"before-after-{topic}.png", optimize=True)
    for topic in TOPICS:
        if not any(r["difference_bbox"] for r in observations if r["topic"] == topic):
            raise ValueError(f"Every {topic} image is unchanged: shared scale rebuild may be inert")
    expected = {(c.slug, p.topic, loc)
                for c in peers for p in peer_plates(c) for loc in c.locale_codes}
    observed = {(r["country"], r["topic"], r["locale"]) for r in observations}
    if expected != observed:
        raise ValueError(f"Coverage mismatch: {sorted(expected ^ observed)}")
    report = {
        "purpose": "Fork-only global peer-axis visual review; not publication approval",
        "old_axes_replaced_by": AXES,
        "published_peers": [c.slug for c in peers],
        "topics": sorted(TOPICS),
        "render_count": len(observations),
        "changed_decoded_images": sum(bool(r["difference_bbox"]) for r in observations),
        "staged_in_ephemeral_runner": stage_for_site,
        "observations": observations,
    }
    (output / "peer-scale-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"QA: {len(peers)} peers, {len(observations)} locale-specific trade/world plates "
          f"with PNG, SVG and pixel comparison; changed "
          f"{report['changed_decoded_images']} images")
    print("Contact sheets and full provenance-neutral rebuild saved to", output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage-for-site", action="store_true",
                        help="stage matching peer PNG/SVG/thumbs in CI only; never push")
    args = parser.parse_args()
    run(args.out, args.stage_for_site)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
