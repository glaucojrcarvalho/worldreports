"""Read-only prerelease HTML Dataset JSON-LD integrity and release blockers.

This is NOT a deployment gate with implicit permission to publish.
It inventories source links in the three generated locale pages, and
requires a human-verified upstream source/data path before describing
those links as live; it does not call websites or modify the atlas.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path

from countries.moldova.research.audit_semantic_readiness import (
    COUNTRY, PENDING,
)

LOCALES = ("ro", "en", "pt")
ORIGIN = "https://worldreports.io/moldova"
UPSTREAM = "https://github.com/akitaonrails/worldreports/tree/main/countries/moldova/data"

class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.active = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type") == "application/ld+json":
            if self.active:
                raise AssertionError("Nested structured data scripts")
            self.active = True
            self.buffer = []

    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.entries.append(json.loads("".join(self.buffer)))
            self.active = False
            self.buffer = []


def inspect(site: Path, *, registered: bool = False,
            upstream_source_verified: bool = False) -> dict:
    urls = {}
    for locale in LOCALES:
        page = site / locale / "index.html"
        if not page.is_file():
            raise AssertionError(f"Missing {locale} prerelease page")
        parser = StructuredData()
        parser.feed(page.read_text(encoding="utf-8"))
        if len(parser.entries) != 1:
            raise AssertionError(f"{locale}: expected exactly one JSON-LD Dataset")
        obj = parser.entries[0]
        if obj.get("@context") != "https://schema.org" or obj.get("@type") != "Dataset":
            raise AssertionError(f"{locale}: invalid structured-data type")
        if obj.get("url") != f"{ORIGIN}/{locale}/":
            raise AssertionError(f"{locale}: wrong schema URL")
        if not obj.get("name") or not obj.get("description"):
            raise AssertionError(f"{locale}: missing translated Dataset name/description")
        if obj.get("temporalCoverage") != "2006/2026":
            raise AssertionError(f"{locale}: incorrect coverage years")
        dist = obj.get("distribution")
        if (not isinstance(dist, list) or len(dist) != 1 or
                not isinstance(dist[0], dict)):
            raise AssertionError(f"{locale}: malformed distribution")
        value = dist[0]
        if value.get("@type") != "DataDownload" or value.get("encodingFormat") != "text/csv":
            raise AssertionError(f"{locale}: wrong CSV description")
        url = value.get("contentUrl")
        if url != UPSTREAM:
            raise AssertionError(f"{locale}: unexpected dataset source URL {url}")
        if not obj.get("citation"):
            raise AssertionError(f"{locale}: no source publisher citations")
        urls[locale] = url
    if (COUNTRY / "country.yaml").exists() != registered:
        raise AssertionError("Incorrect branch-specific publication registration state")
    if not (COUNTRY / "research/country_candidate.yaml").exists():
        raise AssertionError("Original country candidate is absent")
    reasons = sorted(PENDING)
    blockers = []
    if not registered:
        blockers.append("research branch is deliberately not registered in the atlas")
    if not upstream_source_verified:
        blockers.append("future upstream Moldova data source URL is not verified live")
    blockers.append(f"{len(reasons)} canonical indicators require definition-compatible sources")
    # GitHub's /tree/.../data lists a directory, not a directly downloadable
    # CSV. This does not match the promised 'text/csv' DataDownload media type.
    blockers.append("schema DataDownload points to a GitHub directory, not a direct CSV")
    return {
        "decision": "BLOCKED_FOR_PUBLICATION",
        "preview_routes": list(LOCALES),
        "jsonld_source_urls": urls,
        "pending_canonical": reasons,
        "registered": registered,
        "upstream_data_source_verified": upstream_source_verified,
        "blockers": blockers,
        "merge_or_deploy_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=Path("/tmp/moldova-publication-blockers.json"))
    args = parser.parse_args()
    result = inspect(args.site)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    print(f"Moldova structured-data prerelease QA PASS: {len(result['preview_routes'])} "
          f"locales, {len(result['pending_canonical'])} source gaps; "
          f"publication remains BLOCKED")


if __name__ == "__main__":
    main()
