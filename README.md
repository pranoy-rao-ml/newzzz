# NewsFeed

A clean, mobile-first page of the top news by category, built only from free,
non-paywalled RSS feeds. It's a static site: a GitHub Actions job rebuilds
`news.json` every 30 minutes and deploys it to GitHub Pages, so there's no
server to run or pay for.

**Sources:** BBC, The Guardian, NPR, Al Jazeera, DW, France 24, Ars Technica,
The Verge. Edit `scripts/feeds.py` to add or remove feeds.

## How it works

`scripts/build_news.py`:

1. Fetches every feed in parallel. A failed feed is skipped, not fatal.
2. Cleans each item: strips HTML and entities, drops "Continue reading…"
   boilerplate, trims the summary to ~280 characters, and blanks summaries that
   just repeat the title. Items older than 48 hours are dropped.
3. Groups duplicates: the same link (ignoring tracking params) or headlines that
   share most of their key words become one story, with the other outlets
   listed as "Also covered by".
4. Ranks stories by how many outlets cover them, how high the outlet placed
   them (top-stories feeds count double), and how fresh they are.
5. Writes `site/news.json` with a "Top" list plus one list per category.

The page (`site/index.html` + `site/app.js`) shows the cards with a sticky
category bar and re-fetches `news.json` every 5 minutes and when you return to
the tab.

## Run locally

```bash
./start.sh            # builds news.json from live feeds, serves http://localhost:8000
python -m pytest -q   # tests use fixture feeds, no network needed
```

## Deploy to GitHub Pages

1. Push this folder to a GitHub repository (default branch `main`).
2. In the repo, go to **Settings → Pages** and set **Source** to **GitHub Actions**.
3. Run the **Update news** workflow once from the Actions tab (or push to `main`).

After that it refreshes on its own every 30 minutes. GitHub can delay scheduled
runs by a few minutes, and pauses schedules in repos with no activity for 60
days; re-enable from the Actions tab if that happens.

## Styling

Styles are plain Tailwind classes compiled to `site/styles.css`, so the page
loads with no CDN or build step at request time. After changing classes, rebuild it:

```bash
npx tailwindcss@3.4.17 -c tailwind.config.js -i tailwind.input.css -o site/styles.css --minify
```
