"""Fetch RSS feeds, clean, deduplicate and rank stories, and write site/news.json.

Run: python scripts/build_news.py [--out site/news.json]
"""

import argparse
import calendar
import html
import json
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser

sys.path.insert(0, str(Path(__file__).parent))
from feeds import CATEGORIES, FEEDS  # noqa: E402

USER_AGENT = "NewsFeedAggregator/1.0 (+https://github.com/)"
MAX_AGE_HOURS = 48
SUMMARY_MAX = 280
STORIES_PER_CATEGORY = 40
TOP_STORIES = 40
SIMILARITY_THRESHOLD = 0.5

STOPWORDS = set(
    "a an the and or but of to in on at for from by with as is are was were be been "
    "it its this that these those after over into about says say said new how why what "
    "who will can could has have had not no up out more than amid us uk".split()
)
BOILERPLATE = re.compile(
    r"(continue reading\.*|read more\.*|the post .* appeared first on .*|\[…\]|\[\.\.\.\])\s*$",
    re.IGNORECASE,
)
TRACKING_PARAMS = re.compile(r"^(utm_|at_|cmp|ns_|ito$|ref$|fbclid$|gclid$)", re.IGNORECASE)


def clean_summary(raw: str) -> str:
    """Strip HTML, entities, boilerplate and whitespace; truncate on a word boundary."""
    if not raw:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = BOILERPLATE.sub("", text).strip()
    if len(text) > SUMMARY_MAX:
        cut = text[:SUMMARY_MAX].rsplit(" ", 1)[0].rstrip(",;:-")
        text = cut + "…"
    return text


def canonical_url(url: str) -> str:
    """Drop tracking params, fragments, and scheme/host case so the same link matches."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not TRACKING_PARAMS.match(k)])
    path = parts.path.rstrip("/")
    return urlunsplit(("https", parts.netloc.lower().removeprefix("www."), path, query, ""))


def title_tokens(title: str) -> frozenset:
    words = re.findall(r"[a-z0-9]+", html.unescape(title).lower())
    return frozenset(w for w in words if w not in STOPWORDS and len(w) > 1)


def similarity(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    # Overlap coefficient copes better than Jaccard with short vs long headlines.
    return len(a & b) / min(len(a), len(b))


def parse_time(entry) -> float | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return float(calendar.timegm(value))
    return None


def fetch_feed(feed):
    source, category, url, is_top = feed
    try:
        parsed = feedparser.parse(url, agent=USER_AGENT)
    except Exception as exc:  # network errors should not break the whole build
        print(f"WARN {source} {url}: {exc}", file=sys.stderr)
        return feed, []
    if parsed.bozo and not parsed.entries:
        print(f"WARN {source} {url}: {parsed.get('bozo_exception')}", file=sys.stderr)
    return feed, parsed.entries


def normalize(feed, entries, now: float) -> list[dict]:
    source, category, _url, is_top = feed
    items = []
    total = max(len(entries), 1)
    for position, entry in enumerate(entries):
        title = clean_summary(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
            continue
        published = parse_time(entry) or now
        if now - published > MAX_AGE_HOURS * 3600:
            continue
        summary = clean_summary(entry.get("summary") or entry.get("description") or "")
        if summary.lower() == title.lower():
            summary = ""
        items.append(
            {
                "title": title,
                "summary": summary,
                "source": source,
                "url": link,
                "category": category,
                "published_at": published,
                "image": extract_image(entry),
                # 1.0 for the first item in a feed, falling towards 0 for the last.
                "prominence": (1 - position / total) * (2.0 if is_top else 1.0),
                "is_top": is_top,
            }
        )
    return items


def extract_image(entry) -> str | None:
    for key in ("media_thumbnail", "media_content"):
        for media in entry.get(key) or []:
            if media.get("url"):
                return media["url"]
    for link in entry.get("links", []):
        if link.get("type", "").startswith("image/"):
            return link.get("href")
    return None


def cluster(items: list[dict]) -> list[list[dict]]:
    """Group items that are the same story: same canonical URL or similar headline."""
    clusters: list[dict] = []
    by_url: dict[str, int] = {}
    for item in sorted(items, key=lambda i: -i["prominence"]):
        url = canonical_url(item["url"])
        tokens = title_tokens(item["title"])
        index = by_url.get(url)
        if index is None:
            for i, c in enumerate(clusters):
                if abs(c["time"] - item["published_at"]) < 36 * 3600 and similarity(tokens, c["tokens"]) >= SIMILARITY_THRESHOLD and len(tokens & c["tokens"]) >= 3:
                    index = i
                    break
        if index is None:
            clusters.append({"items": [], "tokens": tokens, "time": item["published_at"]})
            index = len(clusters) - 1
        clusters[index]["items"].append(item)
        by_url[url] = index
    return [c["items"] for c in clusters]


def score(items: list[dict], now: float) -> float:
    """Importance = how many outlets cover it + editorial prominence + freshness."""
    sources = {i["source"] for i in items}
    prominence = max(i["prominence"] for i in items)
    newest = max(i["published_at"] for i in items)
    age_hours = max(now - newest, 0) / 3600
    freshness = math.exp(-age_hours / 12)
    return 3.0 * (len(sources) - 1) + 2.0 * prominence + 4.0 * freshness


def to_story(items: list[dict], now: float) -> dict:
    # Lead with the most prominent item that has a summary.
    lead = max(items, key=lambda i: (bool(i["summary"]), i["prominence"]))
    categories = sorted({i["category"] for i in items}, key=CATEGORIES.index)
    also = []
    seen = {lead["source"]}
    for item in sorted(items, key=lambda i: -i["prominence"]):
        if item["source"] not in seen:
            seen.add(item["source"])
            also.append({"source": item["source"], "url": item["url"]})
    return {
        "title": lead["title"],
        "summary": lead["summary"],
        "source": lead["source"],
        "url": lead["url"],
        "category": categories[0],
        "categories": categories,
        "published_at": datetime.fromtimestamp(max(i["published_at"] for i in items), timezone.utc).isoformat(),
        "image": lead["image"] or next((i["image"] for i in items if i["image"]), None),
        "also": also,
        "score": round(score(items, now), 3),
    }


def build(feed_results, now: float | None = None) -> dict:
    now = now or time.time()
    items = [item for feed, entries in feed_results for item in normalize(feed, entries, now)]
    stories = sorted((to_story(c, now) for c in cluster(items)), key=lambda s: -s["score"])
    by_category = {
        cat: [s for s in stories if cat in s["categories"]][:STORIES_PER_CATEGORY] for cat in CATEGORIES
    }
    return {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "categories": ["top"] + [c for c in CATEGORIES if by_category[c]],
        "stories": {"top": stories[:TOP_STORIES], **{c: v for c, v in by_category.items() if v}},
        "sources": sorted({f[0] for f in FEEDS}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).parent.parent / "site" / "news.json"))
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_feed, FEEDS))
    ok = sum(1 for _, entries in results if entries)
    print(f"Fetched {ok}/{len(FEEDS)} feeds", file=sys.stderr)
    if ok == 0:
        sys.exit("No feeds could be fetched; keeping the previous news.json")

    data = build(results)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {len(data['stories']['top'])} top stories to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
