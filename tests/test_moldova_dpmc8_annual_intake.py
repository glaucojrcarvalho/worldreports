"""All numerical fixtures here are deliberately synthetic, NOT Moldova data."""
import hashlib
import json
import pytest
from countries.moldova.research.dpmc8_annual_intake import FILTER, audit, main


def sample():
    raw=b"FAKE publisher export used ONLY to exercise validation"
    selection=dict(FILTER)
    selection.update(start_year=2019,end_year=2025,
                     original_sha256=hashlib.sha256(raw).hexdigest(),
                     original_filename="original.csv",
                     reconciliation_note="Synthetic table; original/source reconciliation must be done later")
    data="year,weighted_nominal_rate_pct,new_loan_volume_mdl_mn\n"
    data+="".join(f"{y},7.25,12.5\n" for y in range(2019,2026))
    return selection,data.encode(),raw


def test_valid_shape_never_automatically_publishes():
    m,d,r=sample();v=audit(m,d,r)
    assert v["row_count"]==7
    assert v["status"]=="STRUCTURALLY_VALID_HUMAN_RECONCILIATION_REQUIRED"
    assert v["publication_authorized"] is False
    assert v["canonical_rows_promoted"]==0


@pytest.mark.parametrize("name,bad",[
    ("report_id","DPMC10"),("frequency","monthly"),
    ("currency","USD"),("borrower","businesses"),
    ("indicator","outstanding_rate"),("term","over_5_years"),
    ("source_url","https://example.invalid")])
def test_wrong_source_category_rejected(name,bad):
    m,d,r=sample();m[name]=bad
    with pytest.raises(AssertionError,match="Wrong DPMC8"):
        audit(m,d,r)


@pytest.mark.parametrize("bad",[
  "2022,7.25,12.5", "2022,0,12.5",
  "2022,NaN,12.5", "2022,-5,12.5",
  "2022,7,25,12.5", "2022,7.25,0"])
def test_bad_data_rejected(bad):
    m,d,r=sample();d=d.decode().replace("2022,7.25,12.5",bad).encode()
    with pytest.raises(AssertionError):
        audit(m,d,r)


@pytest.mark.parametrize("case",["hash","year","future","note","file","raw"])
def test_provenance_rejected(case):
    m,d,r=sample()
    if case=="hash":m["original_sha256"]="f"*64
    if case=="year":m["start_year"]=2020
    if case=="future":m["end_year"]=2026
    if case=="note":m["reconciliation_note"]="yes"
    if case=="file":m["original_filename"]="web.html"
    if case=="raw":r=b""
    with pytest.raises(AssertionError):
        audit(m,d,r)


def test_no_export_means_blocked_not_fiction(monkeypatch,tmp_path):
    p=tmp_path/"blockers.json"
    monkeypatch.setattr("sys.argv",["m","--output",str(p)])
    main(); report=json.loads(p.read_text())
    assert report["status"]=="AWAITING_OFFICIAL_DPMC8_ANNUAL_EXPORT"
    assert report["canonical_rows_promoted"]==0
    assert report["publication_authorized"] is False
