"""Offline generated Moldova page link, SEO and accessibility audit."""
from pathlib import Path
import pytest
from countries.moldova.research.site_route_audit import audit, TOPICS, LOCALES, BASE


def fixture(tmp_path):
    site = tmp_path / "site"
    output = tmp_path / "output"
    (output / "thumbs").mkdir(parents=True)
    for lang, (html_lang, og) in LOCALES.items():
        suffix = "" if lang == "en" else "." + lang
        page = site / lang / "index.html"
        page.parent.mkdir(parents=True)
        head = f'''<html lang="{html_lang}"><head>
        <link rel="canonical" href="{BASE}/{lang}/">
        <link rel="alternate" hreflang="x-default" href="{BASE}/">
        <link rel="alternate" hreflang="ro-MD" href="{BASE}/ro/">
        <link rel="alternate" hreflang="en" href="{BASE}/en/">
        <link rel="alternate" hreflang="pt-BR" href="{BASE}/pt/">
        <meta property="og:locale" content="{og}">
        <meta property="og:image" content="{BASE}/output/01-economy{suffix}.png">
        <meta name="description" content="Moldova statistical evidence and official source limitations are visible in twelve auditable chapters.">
        </head><body>'''
        cards = ""
        for i, topic in enumerate(TOPICS, 1):
            stem = f"{i:02d}-{topic}"
            svg = f"../output/{stem}{suffix}.svg"
            thumb = f"../output/thumbs/{stem}{suffix}.png"
            cards += (f'<li data-id="{stem}" data-svg="{svg}" data-alt="Chart">'
                      f'<a href="{svg}"><img src="{thumb}" alt="Chart"'
                      f' width="560" height="357"></a></li>')
            (output / f"{stem}{suffix}.svg").write_text("<svg/>")
            (output / f"{stem}{suffix}.png").write_bytes(b"PNG")
            (output / "thumbs" / f"{stem}{suffix}.png").write_bytes(b"PNG")
        page.write_text(head + cards + "</body></html>")
    return site, output


def test_all_three_page_lanes_and_36_thumbnails(tmp_path):
    site, output = fixture(tmp_path)
    result = audit(site, output)
    assert set(result) == set(LOCALES)
    assert sum(x["plates"] for x in result.values()) == 36


def test_wrong_locale_svg_and_hreflang_are_blocked(tmp_path):
    site, output = fixture(tmp_path)
    (output / "03-spending.pt.svg").unlink()
    with pytest.raises(AssertionError, match="SVG/PNG"):
        audit(site, output)
    (output / "03-spending.pt.svg").write_text("<svg/>")
    path = site / "en/index.html"
    path.write_text(path.read_text().replace('hreflang="pt-BR"', 'hreflang="pt-PT"'))
    with pytest.raises(AssertionError, match="hreflang"):
        audit(site, output)


def test_accessibility_and_wrong_language_thumbnails_are_blocked(tmp_path):
    site, output = fixture(tmp_path)
    page = site / "ro/index.html"
    original = page.read_text()
    page.write_text(original.replace(' alt="Chart" width="560"', ' alt="" width="560"', 1))
    with pytest.raises(AssertionError, match="accessible"):
        audit(site, output)
    page.write_text(original.replace("thumbs/03-spending.ro.png",
                                     "thumbs/03-spending.png"))
    with pytest.raises(AssertionError, match="wrong-language"):
        audit(site, output)
