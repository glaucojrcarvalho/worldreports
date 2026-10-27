"""Fail closed on stale Moldova source-to-figure visual-review evidence."""
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

SOURCE = Path(__file__).resolve().parents[1] / (
    "countries/moldova/research/visual_review.py")
spec = importlib.util.spec_from_file_location("moldova_visual_review", SOURCE)
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)


def _candidate(tmp_path):
    country = tmp_path / "moldova"
    output = country / "output"
    (output / "thumbs").mkdir(parents=True)
    for index, topic in enumerate(visual.TOPICS, 1):
        for locale in visual.LOCALES:
            suffix = "" if locale == "en" else "." + locale
            name = f"{index:02d}-{topic}{suffix}.png"
            Image.new("RGB", (100, 64), "white").save(output / name)
            Image.new("RGB", (32, 20), "white").save(
                output / "thumbs" / name)
            (output / name.replace(".png", ".svg")).write_text("<svg/>")
    provenance = {
        f"{index:02d}-{topic}": []
        for index, topic in enumerate(visual.TOPICS, 1)
    }
    provenance.update({
        key: sorted(values) for key, values in visual.REQUIRED_LINEAGE.items()
    })
    (country / "provenance.json").write_text(json.dumps(provenance))
    return country


def test_twelve_trilingual_sheets_and_108_sha256_checksums(tmp_path):
    country = _candidate(tmp_path)
    destination = tmp_path / "review"
    result = visual.build_review(country, destination)
    assert len(result["plates"]) == 12
    assert len(list(destination.glob("*.png"))) == 12
    assert all(len(p["locales"]) == 3 for p in result["plates"])
    archived = json.loads(
        (destination / "visual-review-manifest.json").read_text())
    assert archived["plates"][2]["observed_sources"] == sorted(
        visual.REQUIRED_LINEAGE["03-spending"])
    assert len(result["plates"][11]["locales"][0]["png_sha256"]) == 64


def test_stale_bns_lineage_and_missing_locale_block_visual_review(tmp_path):
    country = _candidate(tmp_path)
    path = country / "provenance.json"
    values = json.loads(path.read_text())
    values["03-spending"] = ["macro/economy.csv"]
    path.write_text(json.dumps(values))
    with pytest.raises(AssertionError, match="missing original source"):
        visual.build_review(country, tmp_path / "review")
    values["03-spending"] = sorted(
        visual.REQUIRED_LINEAGE["03-spending"])
    path.write_text(json.dumps(values))
    (country / "output/03-spending.ro.png").unlink()
    with pytest.raises(AssertionError, match="Plate inventory differs"):
        visual.build_review(country, tmp_path / "review")
