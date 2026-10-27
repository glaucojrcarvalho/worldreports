"""Read-only site/asset/locale contract for Moldova's generated pages.

This checks real generated HTML links, not just source catalogue keys.
No network access, site changes, source edits, or deployment.
"""
from html.parser import HTMLParser
from pathlib import Path
import argparse

TOPICS = ("economy", "fiscal", "spending", "trade", "markets", "credit",
          "people", "world", "demography", "security", "mortality", "migration")
LOCALES = {"ro": ("ro-MD", "ro_MD"), "en": ("en", "en_US"),
           "pt": ("pt-BR", "pt_BR")}
BASE = "https://worldreports.io/moldova"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []

    def handle_starttag(self, name, attrs):
        self.rows.append((name, dict(attrs)))

    def find(self, tag):
        return [value for name, value in self.rows if name == tag]


def check(ok, reason):
    if not ok:
        raise AssertionError(reason)


def audit(site: Path, output: Path) -> dict:
    result = {}
    stems = [f"{number:02d}-{topic}"
             for number, topic in enumerate(TOPICS, 1)]
    for locale, (html_lang, og_locale) in LOCALES.items():
        document = site / locale / "index.html"
        check(document.is_file(), f"{locale}: no generated page")
        tags = Tags()
        tags.feed(document.read_text(encoding="utf-8"))
        check(len(tags.find("html")) == 1 and
              tags.find("html")[0].get("lang") == html_lang,
              f"{locale}: wrong HTML language")
        links = tags.find("link")
        canonicals = [link.get("href") for link in links
                      if link.get("rel") == "canonical"]
        check(canonicals == [f"{BASE}/{locale}/"],
              f"{locale}: incorrect canonical URL")
        alternates = {link.get("hreflang"): link.get("href") for link in links
                      if link.get("rel") == "alternate"}
        check(alternates == {
            "x-default": BASE + "/", "ro-MD": BASE + "/ro/",
            "en": BASE + "/en/", "pt-BR": BASE + "/pt/"},
            f"{locale}: invalid hreflang links")
        metas = tags.find("meta")
        og = [m.get("content") for m in metas if m.get("property") == "og:locale"]
        check(og == [og_locale], f"{locale}: invalid OpenGraph language")
        desc = [m.get("content", "") for m in metas
                if m.get("name") == "description"]
        check(len(desc) == 1 and len(desc[0]) >= 60,
              f"{locale}: missing translated SEO description")
        cards = [item for item in tags.find("li") if "data-id" in item]
        check([card["data-id"] for card in cards] == stems,
              f"{locale}: missing/reordered chart cards")
        imgs = [item for item in tags.find("img")
                if item.get("src", "").startswith("../output/thumbs/")]
        suffix = "" if locale == "en" else "." + locale
        thumbs = [f"../output/thumbs/{stem}{suffix}.png" for stem in stems]
        check([img["src"] for img in imgs] == thumbs,
              f"{locale}: missing or wrong-language thumbnail")
        for img in imgs:
            check(img.get("alt", "").strip() and img.get("width")
                  and img.get("height"),
                  f"{locale}: missing accessible image alt or size")
            check((output / "thumbs" / Path(img["src"]).name).is_file(),
                  f"{locale}: missing generated thumbnail")
        for stem, card in zip(stems, cards):
            svg = f"../output/{stem}{suffix}.svg"
            check(card.get("data-svg") == svg and
                  card.get("data-alt", "").strip(),
                  f"{locale}: SVG or card accessibility metadata mismatch")
            check((output / f"{stem}{suffix}.svg").is_file() and
                  (output / f"{stem}{suffix}.png").is_file(),
                  f"{locale}: missing complete SVG/PNG output")
        anchors = [a.get("href") for a in tags.find("a")
                   if a.get("href", "").startswith("../output/")
                   and a.get("href", "").endswith(".svg")]
        check(set(anchors) == {
            f"../output/{stem}{suffix}.svg" for stem in stems},
            f"{locale}: SVG download links differ from available plates")
        social = [m.get("content") for m in metas
                  if m.get("property") == "og:image"]
        check(social == [f"{BASE}/output/01-economy{suffix}.png"],
              f"{locale}: wrong-language social preview")
        result[locale] = {"plates": len(cards), "thumbs": len(imgs),
                          "svg_links": len(anchors)}
    print("Moldova route QA PASS: ro/en/pt, 12 plates each, 36 assets per kind")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    audit(args.site, args.output)


if __name__ == "__main__":
    main()
