"""Fail closed on stale Moldova source-to-figure visual-review evidence."""
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image
import yaml

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
        f"{index:02d}-{topic}": [f"fixture/{topic}.csv"]
        for index, topic in enumerate(visual.TOPICS, 1)
    }
    provenance.update({
        key: sorted(values) for key, values in visual.REQUIRED_LINEAGE.items()
    })
    (country / "provenance.json").write_text(json.dumps(provenance))
    sources = {}
    for paths in provenance.values():
        for rel in paths:
            group, name = rel.split("/")
            path = country / "data" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("year,value\n2024,1\n", encoding="utf-8")
            sources.setdefault(group, {})[name] = {
                "official": True, "source": "Offline test publisher",
                "url": "https://example.org/official",
            }
    (country / "SOURCES.yaml").write_text(
        yaml.safe_dump(sources, sort_keys=True), encoding="utf-8")
    for rel in ("plates.py", "i18n.json", "ui.json",
                "research/country_candidate.yaml"):
        path = country / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test fixture\n", encoding="utf-8")
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
    assert len(result["render_config_sha256"]) == 5
    assert result["plates"][2]["source_sha256"] == {
        path: result["curated_source_sha256"][path]
        for path in sorted(visual.REQUIRED_LINEAGE["03-spending"])
    }
    assert all(len(s) == 64 for s in result["curated_source_sha256"].values())


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


def test_original_source_input_mutation_is_fingerprinted(tmp_path):
    country = _candidate(tmp_path)
    first = visual.build_review(country, tmp_path / "before")
    target = country / "data" / "fiscal/public_budget.csv"
    target.write_text("year,value\\n2024,2\\n", encoding="utf-8")
    second = visual.build_review(country, tmp_path / "after")
    assert first["curated_source_sha256"]["fiscal/public_budget.csv"] != (
        second["curated_source_sha256"]["fiscal/public_budget.csv"])
    assert first["plates"][2]["locales"][0]["png_sha256"] == (
        second["plates"][2]["locales"][0]["png_sha256"])


def test_invalid_or_unattributed_csv_refuses_release_evidence(tmp_path):
    country = _candidate(tmp_path)
    csv = country / "data" / "macro/national_lfs.csv"
    csv.unlink()
    with pytest.raises(AssertionError, match="missing curated source CSV"):
        visual.build_review(country, tmp_path / "review")
    csv.write_text("year,value\\n2025,3.8\\n", encoding="utf-8")
    manifest = country / "SOURCES.yaml"
    source = yaml.safe_load(manifest.read_text())
    del source["macro"]["national_lfs.csv"]
    manifest.write_text(yaml.safe_dump(source))
    with pytest.raises(AssertionError, match="missing publisher metadata"):
        visual.build_review(country, tmp_path / "review")
