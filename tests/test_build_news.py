import sys
import time
from email.utils import formatdate
from pathlib import Path

import feedparser

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import build_news  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    xml = (FIXTURES / name).read_text().replace("{NOW}", formatdate(time.time() - 600, usegmt=True))
    return feedparser.parse(xml).entries


def test_clean_summary_strips_html_entities_and_boilerplate():
    raw = '<p>Hello &amp; <b>world</b></p> <a href="x">Continue reading...</a>'
    assert build_news.clean_summary(raw) == "Hello & world"


def test_clean_summary_truncates_on_word_boundary():
    out = build_news.clean_summary("word " * 200)
    assert len(out) <= build_news.SUMMARY_MAX + 1
    assert out.endswith("…") and not out.endswith(" …")


def test_canonical_url_drops_tracking():
    a = build_news.canonical_url("https://www.bbc.co.uk/news/x/?at_medium=RSS&id=3#top")
    assert a == "https://bbc.co.uk/news/x?id=3"


def test_build_dedups_ranks_and_filters():
    results = [
        (("BBC", "world", "u1", True), load("bbc.xml")),
        (("The Guardian", "technology", "u2", False), load("guardian.xml")[1:]),
        (("The Guardian", "world", "u3", False), load("guardian.xml")[:1]),
    ]
    data = build_news.build(results)
    top = data["stories"]["top"]
    titles = [s["title"] for s in top]

    # Old story dropped, quake stories merged and ranked first.
    assert "Very old story" not in titles
    assert len(top) == 3
    lead = top[0]
    assert "Japan" in lead["title"]
    assert lead["also"][0]["source"] in {"BBC", "The Guardian"}
    assert lead["image"] == "https://ichef.bbci.co.uk/x.jpg"

    # Summary identical to title is blanked.
    bakery = next(s for s in top if s["title"] == "Local bakery wins award")
    assert bakery["summary"] == ""

    assert data["categories"] == ["top", "world", "technology"]
    assert [s["title"] for s in data["stories"]["technology"]] == ["New chip startup raises funding round"]


def test_unrelated_headlines_not_merged():
    a = build_news.title_tokens("Earthquake strikes central Japan")
    b = build_news.title_tokens("Japan election results announced")
    assert build_news.similarity(a, b) < build_news.SIMILARITY_THRESHOLD
