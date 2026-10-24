"""Feed sources. Each entry: (source name, category, url, is_top_stories_feed).

All are free, non-paywalled RSS feeds. Categories come from the feed itself,
so no text classification is needed. Items from "top" feeds get a ranking
boost because the outlet's editors put them there.
"""

CATEGORIES = ["world", "business", "technology", "science", "health", "culture", "sport"]

FEEDS = [
    # BBC
    ("BBC", "world", "https://feeds.bbci.co.uk/news/rss.xml", True),
    ("BBC", "world", "https://feeds.bbci.co.uk/news/world/rss.xml", False),
    ("BBC", "business", "https://feeds.bbci.co.uk/news/business/rss.xml", False),
    ("BBC", "technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", False),
    ("BBC", "science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", False),
    ("BBC", "health", "https://feeds.bbci.co.uk/news/health/rss.xml", False),
    ("BBC", "culture", "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", False),
    ("BBC", "sport", "https://feeds.bbci.co.uk/sport/rss.xml", False),
    # The Guardian
    ("The Guardian", "world", "https://www.theguardian.com/international/rss", True),
    ("The Guardian", "world", "https://www.theguardian.com/world/rss", False),
    ("The Guardian", "business", "https://www.theguardian.com/business/rss", False),
    ("The Guardian", "technology", "https://www.theguardian.com/technology/rss", False),
    ("The Guardian", "science", "https://www.theguardian.com/science/rss", False),
    ("The Guardian", "health", "https://www.theguardian.com/society/health/rss", False),
    ("The Guardian", "culture", "https://www.theguardian.com/culture/rss", False),
    ("The Guardian", "sport", "https://www.theguardian.com/sport/rss", False),
    # NPR
    ("NPR", "world", "https://feeds.npr.org/1001/rss.xml", True),
    ("NPR", "world", "https://feeds.npr.org/1004/rss.xml", False),
    ("NPR", "business", "https://feeds.npr.org/1006/rss.xml", False),
    ("NPR", "technology", "https://feeds.npr.org/1019/rss.xml", False),
    ("NPR", "science", "https://feeds.npr.org/1007/rss.xml", False),
    ("NPR", "health", "https://feeds.npr.org/1128/rss.xml", False),
    ("NPR", "culture", "https://feeds.npr.org/1008/rss.xml", False),
    ("NPR", "sport", "https://feeds.npr.org/1055/rss.xml", False),
    # World news
    ("Al Jazeera", "world", "https://www.aljazeera.com/xml/rss/all.xml", True),
    ("DW", "world", "https://rss.dw.com/rdf/rss-en-all", True),
    ("France 24", "world", "https://www.france24.com/en/rss", True),
    # Tech
    ("Ars Technica", "technology", "https://feeds.arstechnica.com/arstechnica/index", False),
    ("The Verge", "technology", "https://www.theverge.com/rss/index.xml", False),
]
