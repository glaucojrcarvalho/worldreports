"""Moldova prerelease schema must not misrepresent unmerged datasets."""
import json
from pathlib import Path

import pytest

from countries.moldova.research.audit_prerelease_metadata import (
    LOCALES, ORIGIN, UPSTREAM, inspect,
)


def make_site(tmp_path, override=None):
    for loc in LOCALES:
        target = tmp_path / loc / "index.html"
        target.parent.mkdir(parents=True)
        obj = {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Moldova",
            "description": "National economic and demographic data",
            "url": f"{ORIGIN}/{loc}/",
            "temporalCoverage": "2006/2026",
            "distribution": [{"@type": "DataDownload",
                              "encodingFormat": "text/csv",
                              "contentUrl": UPSTREAM}],
            "citation": ["National Bureau of Statistics"],
        }
        if override and loc == "en":
            override(obj)
        target.write_text(
            '<html><head><script type="application/ld+json">'+
            json.dumps(obj)+'</script></head></html>', encoding="utf-8")
    return tmp_path


def test_three_locale_schema_is_structurally_valid_but_not_publishable(tmp_path):
    a=inspect(make_site(tmp_path))
    assert a["decision"] == "BLOCKED_FOR_PUBLICATION"
    assert a["merge_or_deploy_authorized"] is False
    assert len(a["jsonld_source_urls"]) == 3
    assert len(a["pending_canonical"]) == 9
    assert any("not a direct CSV" in x for x in a["blockers"])


@pytest.mark.parametrize("field,value", [
    ("url", "https://wrong.invalid"),
    ("temporalCoverage", "2006/2099"),
    ("distribution", []),
    ("citation", []),
])
def test_misleading_or_broken_structured_data_is_rejected(tmp_path, field, value):
    p=make_site(tmp_path, lambda obj: obj.__setitem__(field,value))
    with pytest.raises(AssertionError):
        inspect(p)


def test_untrusted_source_directory_link_is_rejected(tmp_path):
    p=make_site(tmp_path,lambda obj: obj["distribution"][0].update(
        contentUrl="https://github.com/attacker/worldreports/tree/main/countries/moldova/data"))
    with pytest.raises(AssertionError,match="unexpected dataset source URL"):
        inspect(p)


def test_build_does_not_prematurely_claim_registration(tmp_path):
    p=make_site(tmp_path)
    with pytest.raises(AssertionError,match="registration state"):
        inspect(p,registered=True)


def test_missing_one_locale_is_error(tmp_path):
    p=make_site(tmp_path)
    (p/"pt/index.html").unlink()
    with pytest.raises(AssertionError,match="Missing pt"):
        inspect(p)
