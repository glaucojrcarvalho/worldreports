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
