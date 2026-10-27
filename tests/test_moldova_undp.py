"""Moldova UNDP HDI 2025 source parser: no vintage splicing or fake years."""
import csv
import io

import pytest

from countries.moldova.fetch.fetch_undp import (
    ANCHORS, YEARS, parse_release, render_sidecar,
)


def fixture_csv(**changes):
    """Produce the 206-row/18-year header contract without network access."""
    headers = ["iso3", "country", "hdicode", "region"] + [
        f"hdi_{year}" for year in YEARS]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    base = {f"hdi_{y}": ("0.784" if y == 2022
                          else "0.785" if y == 2023 else "0.711")
            for y in YEARS}
    for i in range(205):
        # Long text fields produce a realistic complete-size fixture without
        # appending a spurious 207th CSV row after the final newline.
        writer.writerow({"iso3": f"ZZ{i:03d}",
                         "country": f"Country {i}" + (" " * 490),
                         **base})
    writer.writerow({"iso3": "MDA", "country": "Republic of Moldova",
                     **(base | changes)})
    return buf.getvalue().encode("cp1252")


def test_complete_moldova_isolation_exact_vintage_and_missing_years():
    data = fixture_csv()
    rows = parse_release(data)
    assert len(rows) == 18
    assert [y for y, _ in rows] == list(range(2006, 2024))
    assert dict(rows)[2022] == "0.784"
    assert dict(rows)[2023] == "0.785"
    txt = render_sidecar(rows, data)
    assert txt.count("\n2023,0.785\n") == 1
    assert "2024," not in txt and "2025," not in txt
    assert "SHA256" in txt and "2025" in txt


@pytest.mark.parametrize("changes", [
    {"hdi_2023": ""},
    {"hdi_2022": "0.763"},
    {"hdi_2023": "1.22"},
    {"hdi_2009": "NaN"},
    {"hdi_2010": "not_a_number"},
])
def test_invalid_or_mixed_vintage_is_rejected(changes):
    with pytest.raises(ValueError):
        parse_release(fixture_csv(**changes))


def test_html_and_truncated_response_are_not_csv():
    with pytest.raises(ValueError):
        parse_release(b"<html>503 proxy</html>")
    with pytest.raises(ValueError):
        parse_release(b"year,hdi\n2023,0.785\n")

def test_curated_hdr_2025_hdi_is_single_vintage_with_missing_later_years():
    """Published HDI panel uses all and only the audited official 2025 CSV."""
    import json
    from pathlib import Path
    import yaml

    root = Path(__file__).resolve().parents[1] / "countries/moldova"
    content = (root / "data/world/hdi.csv").read_text("utf-8")
    lines = [line for line in content.splitlines() if line and not line.startswith("#")]
    rows = list(csv.DictReader(lines))
    assert [int(r["year"]) for r in rows] == list(range(2006, 2026))
    assert len(rows) == 20
    got = {int(r["year"]): r["hdi"] for r in rows if r["hdi"]}
    assert len(got) == 18
    assert list(got) == list(range(2006, 2024))
    assert got[2006] == "0.711"
    assert got[2022] == "0.784"
    assert got[2023] == "0.785"
    assert float(got[2023]) - float(got[2022]) == pytest.approx(.001)
    assert not rows[-2]["hdi"] and not rows[-1]["hdi"]
    assert "61ed82e5b66c88dfca8ff9fac775c63981ecab6a254862af97acacc41c143117" in content

    sources = yaml.safe_load((root / "SOURCES.yaml").read_text("utf-8"))
    hdi = sources["world"]["hdi.csv"]
    assert hdi["official"] is True
    assert hdi["refreshed_by"] == "fetch/fetch_undp.py"
    assert "HDR25_Composite_indices_complete_time_series.csv" in hdi["url"]
    assert "2022=0.763" in hdi["notes"] and "2022=0.784" in hdi["notes"]
    plate = (root / "plates.py").read_text("utf-8")
    world = plate.split("def plate_world(", 1)[1].split("def plate_demography(", 1)[0]
    hdi_slot = world.split('ig.slot("world.hdi"', 1)[1].split('ig.slot("world.cpi"', 1)[0]
    assert '_series(ctx, "world/hdi.csv", "hdi")' in hdi_slot
    assert "_pending(" not in hdi_slot
    assert "UNDP HDR 2025 CSV" in hdi_slot
    chapters = (root / "chapters.py").read_text("utf-8")
    assert '"world/world.csv", "world/hdi.csv"' in chapters
    prov = json.loads((root / "provenance.json").read_text("utf-8"))
    assert prov["08-world"] == ["world/hdi.csv", "world/world.csv"]
    catalog = json.loads((root / "i18n.json").read_text("utf-8"))
    for label in ("UNDP HDR 2025 CSV; through 2023; see edition note",
                  "World Bank WDI; UNDP HDR 2025; TI CPI pending"):
        assert set(catalog[label]) == {"ro", "pt"}
    ui = json.loads((root / "ui.json").read_text("utf-8"))
    for lang, decimals in (("ro", ("0,784", "0,763")),
                           ("en", ("0.784", "0.763")),
                           ("pt", ("0,784", "0,763"))):
        assert any(all(token in note for token in decimals)
                   for note in ui[lang]["notes"])
        terms = [x["term"] for x in ui[lang]["unavailable"]]
        assert len(terms) == 10
        assert any(any(fragment in word.lower() for fragment in ("corup", "corrup"))
                   for word in terms)
