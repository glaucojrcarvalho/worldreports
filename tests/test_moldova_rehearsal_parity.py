"""Test the research/rehearsal attestation against unsafe source drift."""
import pytest
from countries.moldova.research.verify_rehearsal_parity import (
 CANDIDATE,REGISTERED,PROVENANCE,TOPICS,CRITICAL,expected_graphics,check)

def sample():
    s={"core/country.py":"a"*40,"site/page.py":"b"*40,
       "requirements.txt":"c"*40,CANDIDATE:"d"*40}
    s.update({f"countries/moldova/data/x/a{i}.csv":f"{i:040d}" for i in range(55)})
    refs={f"{i:02d}-{topic}":[f"x/a{i}.csv"]
          for i,topic in enumerate(TOPICS,1)}
    refs.update({k:sorted(v) for k,v in CRITICAL.items()})
    n=0
    while len(set(sum([list(v) for v in refs.values()],[])))<23:
        key=f"{(n%8)+1:02d}-{TOPICS[n%8]}"
        p=f"x/a{n+15}.csv"
        if p not in refs[key]: refs[key].append(p)
        n+=1
    for paths in refs.values():
        for p in paths: s["countries/moldova/data/"+p]="e"*40
    for p in expected_graphics(): s[p]="f"*40
    s[PROVENANCE]="g"*40
    rehearsal=dict(s);rehearsal[REGISTERED]=s[CANDIDATE]
    return s,rehearsal,refs

def test_complete_parity():
    s,r,p=sample();a=check(s,r,p)
    assert a["graphics"]==108 and a["curated_csvs"]==23

@pytest.mark.parametrize("path",["core/country.py","site/page.py",
    "countries/moldova/data/x/a0.csv","countries/moldova/plates.py",
    "countries/moldova/i18n.json"])
def test_source_change_rejected(path):
    s,r,p=sample();s[path]="changed"
    with pytest.raises(AssertionError,match="source drift"):check(s,r,p)

def test_registered_config_and_image_inventory_rejected():
    s,r,p=sample();r[REGISTERED]="incorrect"
    with pytest.raises(AssertionError,match="differs"):check(s,r,p)
    r[REGISTERED]=s[CANDIDATE]
    s.pop("countries/moldova/output/03-spending.ro.svg")
    with pytest.raises(AssertionError,match="graphics"):check(s,r,p)

def test_source_maps_and_publication_rejected():
    s,r,p=sample();p["03-spending"]=["macro/economy.csv"]
    with pytest.raises(AssertionError):check(s,r,p)
    s,r,p=sample();s[REGISTERED]=s[CANDIDATE]
    with pytest.raises(AssertionError,match="unexpectedly registered"):check(s,r,p)
