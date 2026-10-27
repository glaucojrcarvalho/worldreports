"""Offline BNS unemployment PxWeb identity and 2025 break safeguards."""
import pytest
from countries.moldova.fetch import fetch_bns_lfs as src


def fixture():
    return {"title": "Unemployment rate by sex, area and quarters, 2019-2025",
            "variables": [
                {"code": "Sex", "text": "Sex",
                 "values": ["T", "M", "F"],
                 "valueTexts": ["Total", "Men", "Women"]},
                {"code": "Area", "text": "Area",
                 "values": ["T", "U", "R"],
                 "valueTexts": ["Total", "Urban", "Rural"]},
                {"code": "Years", "text": "Years",
                 "values": list(map(str, src.YEARS)),
                 "valueTexts": list(map(str, src.YEARS))},
                {"code": "Quarters", "text": "Quarters",
                 "values": ["Y", "1", "2", "3", "4"],
                 "valueTexts": ["Annual", "Q1", "Q2", "Q3", "Q4"]},
            ]}


def test_official_table_is_metadata_only_and_all_years_present():
    assert src.TABLE == "MUN160100_2025.px"
    assert src.YEARS == tuple(range(2019, 2026))
    assert src.OUT.name.endswith("_from_bns.json")
    dims = src.validate_metadata(fixture())
    assert len(dims) == 4
    assert set(item["label"] for item in dims[2]["categories"]) == {
        str(y) for y in src.YEARS}
    assert not hasattr(src, "promote_curated_data")


def test_fail_closed_on_missing_year_malformed_axes_and_wrong_topic():
    p = fixture()
    p["variables"][2]["values"].remove("2025")
    p["variables"][2]["valueTexts"].remove("2025")
    with pytest.raises(ValueError, match="2019"):
        src.validate_metadata(p)
    p = fixture()
    p["variables"][3]["text"] = "Other"
    with pytest.raises(ValueError, match="sex, area and quarter"):
        src.validate_metadata(p)
    p = fixture()
    p["title"] = "Exports of goods"
    with pytest.raises(ValueError, match="unemployment"):
        src.validate_metadata(p)
    p = fixture()
    p["variables"][2]["values"].append("2026")
    p["variables"][2]["valueTexts"].append("2026")
    with pytest.raises(ValueError, match="2026"):
        src.validate_metadata(p)


def test_discovery_requires_true_publisher_metadata_not_path_match():
    fixture_url = src.API + "/03%20FM/03%20MUN/MUN060/" + src.TABLE
    def fetch(url):
        if url == fixture_url:
            return fixture(), "a" * 64
        raise OSError("Not a publisher response")
    url, variables, sha = src.discover(fetch)
    assert url == fixture_url and sha == "a"*64 and len(variables) == 4
    def bad(url):
        if url == fixture_url:
            return {"variables": []}, "b"*64
        raise OSError("metadata not available")
    with pytest.raises(OSError):
        src.discover(bad)


def test_no_ilo_modelled_splicing_or_publication():
    text = src.__doc__.lower()
    assert "2019" in text and "2025" in text
    assert "wdi" in text and "modelled" in text
    assert "not a curated annual unemployment series" in text
