"""Guarded official XLSX CPI parser: 2012 method boundary and source anchors."""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape

import pytest

from countries.moldova.fetch.fetch_ti import YEARS, parse_release, render_sidecar


def fixture_xlsx(*, changes=None, header_change=None, sheet="CPI Timeseries 2012 - 2025"):
    """Build a real ZIP/OOXML workbook with inline strings and cached numbers."""
    changes = changes or {}
    headers = ["Country / Territory"] + [f"CPI Score {year}" for year in YEARS]
    if header_change is not None:
        headers[1] = header_change
    countries = [f"Country {n}" for n in range(181)] + ["Moldova"]
    grid = [headers]
    for c in countries:
        scores = [42 if year != 2024 else 43 for year in YEARS]
        if c == "Moldova":
            scores = [changes.get(year, v) for year, v in zip(YEARS, scores)]
        grid.append([c, *scores])
    def letter(index):
        name = ""
        while index:
            index, digit = divmod(index - 1, 26)
            name = chr(65 + digit) + name
        return name
    cells = []
    for i, row in enumerate(grid, start=1):
        cols = []
        for j, value in enumerate(row, start=1):
            ref = f"{letter(j)}{i}"
            if isinstance(value, str):
                xml = f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            elif value is None:
                xml = f'<c r="{ref}"></c>'
            else:
                xml = f'<c r="{ref}"><v>{value}</v></c>'
            cols.append(xml)
        cells.append(f'<row r="{i}">' + "".join(cols) + "</row>")
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    workbook = (f'<workbook xmlns="{ns}" xmlns:r="{relns}"><sheets>'
                f'<sheet name="{escape(sheet)}" sheetId="1" r:id="rId1"/>'
                "</sheets></workbook>")
    rel = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
           '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
           'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
           '</Relationships>')
    sheetxml = f'<worksheet xmlns="{ns}"><sheetData>' + "".join(cells) + "</sheetData></worksheet>"
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", rel)
        z.writestr("xl/worksheets/sheet1.xml", sheetxml)
    return stream.getvalue()


def test_official_release_contract_and_review_only_sidecar():
    source = fixture_xlsx()
    result = parse_release(source)
    assert [y for y, _ in result] == list(YEARS)
    assert [x for x in result if x[0] >= 2023] == [(2023, 42), (2024, 43), (2025, 42)]
    out = render_sidecar(result, source)
    assert out.count("\n2025,42\n") == 1
    assert "\n2011," not in out and "\n2006," not in out
    assert "SHA256" in out and "CC BY-ND" in out


@pytest.mark.parametrize("changed", [
    {2025: 43}, {2024: 42}, {2023: 41},
    {2016: None}, {2019: 101}, {2020: -1},
    {2022: 35.25}, {2012: "NaN"},
])
def test_missing_invalid_and_mismatched_publisher_values_fail_closed(changed):
    with pytest.raises(ValueError):
        parse_release(fixture_xlsx(changes=changed))


def test_cannot_confuse_rank_or_method_break_with_scores():
    with pytest.raises(ValueError):
        parse_release(fixture_xlsx(header_change="CPI Rank 2012"))
    with pytest.raises(ValueError):
        parse_release(fixture_xlsx(sheet="CPI Historical"))
    with pytest.raises(ValueError):
        parse_release(b"<html>502 bad gateway</html>")


def test_source_is_not_implicitly_published():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "countries/moldova"
    # The full regression suite temporarily registers the candidate in CI;
    # the separate candidate-only guard enforces absence in the checkout.
    assert not (root / "data/world/cpi.csv").exists()
    plate = (root / "plates.py").read_text(encoding="utf-8")
    assert '_pending(ctx, ig, ax, "Transparency International annual scores' in plate
