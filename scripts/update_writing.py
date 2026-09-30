"""Add new Ground Truth posts from the Substack feed to writing.html.

Runs daily from .github/workflows/update-writing.yml. Rules:
- Only posts dated on or after the newest article already on the page are considered,
  and a post whose link is already on the page is never added twice.
- A post titled "Introducing ..." starts a new series section at the top, and
  adds a row for the series to the homepage Writing list.
- Any other post goes into the newest series, and that series' date label is
  extended to cover it.
- A post missing a title, link, or date is skipped rather than published.

Substack refuses requests from GitHub's servers, so the feed is read through a
Cloudflare Worker relay (SUBSTACK_FEED_URL, see scripts/substack-feed-worker.js)
when one is set, then directly from the RSS feed, then from Substack's archive data.

Usage: python scripts/update_writing.py [--feed FILE] [--page FILE]
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEED_URL = "https://byshannoncoleman.substack.com/feed"
ARCHIVE_URL = "https://byshannoncoleman.substack.com/api/v1/archive?sort=new&limit=25"
UTM = "utm_source=portfolio&amp;utm_medium=writing-page&amp;utm_campaign=site&amp;utm_content="
SEP = " &nbsp;&bull;&nbsp; "
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml;q=0.9, application/json;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def download(url, retries=0):
    """Fetch a URL, retrying rate limits and server errors with growing waits."""
    waits = [20, 60, 120][:retries]
    for attempt in range(len(waits) + 1):
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == len(waits):
                raise
            print(f"{url} returned {e.code}; retrying in {waits[attempt]} seconds")
            time.sleep(waits[attempt])


def get_posts(feed_path):
    """Read posts from a local file, the RSS feed, or Substack's archive data."""
    if feed_path:
        with open(feed_path, "rb") as f:
            return parse_feed(f.read())
    errors = []
    sources = [(FEED_URL, parse_feed), (ARCHIVE_URL, parse_archive)]
    relay = os.environ.get("SUBSTACK_FEED_URL", "").strip()
    if relay:  # the Cloudflare Worker relay, tried first
        sources.insert(0, (relay, parse_feed))
    for url, parse in sources:
        try:
            return parse(download(url, retries=3 if url == relay else 0))
        except Exception as e:  # try the next source
            errors.append(f"{url}: {e}")
            print(f"Could not read {url}: {e}")
    raise SystemExit("Substack could not be reached:\n" + "\n".join(errors))


def parse_feed(data):
    posts = []
    for item in ET.fromstring(data).iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        subtitle = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", item.findtext("description") or ""))).strip()
        m = re.search(r"substack\.com/p/([A-Za-z0-9-]+)", link)
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "")
        except (TypeError, ValueError):
            date = None
        if not (title and m and date):
            print(f"Skipping incomplete feed item: {title or link or '(untitled)'}")
            continue
        posts.append({"title": title, "slug": m.group(1), "subtitle": subtitle, "date": date.date()})
    return sorted(posts, key=lambda p: p["date"])


def parse_archive(data):
    posts = []
    for item in json.loads(data):
        title = (item.get("title") or "").strip()
        slug = item.get("slug") or ""
        try:
            date = datetime.fromisoformat((item.get("post_date") or "").replace("Z", "+00:00"))
        except ValueError:
            date = None
        if not (title and re.fullmatch(r"[A-Za-z0-9-]+", slug) and date):
            print(f"Skipping incomplete archive item: {title or slug or '(untitled)'}")
            continue
        subtitle = re.sub(r"\s+", " ", item.get("subtitle") or "").strip()
        posts.append({"title": title, "slug": slug, "subtitle": subtitle, "date": date.date()})
    return sorted(posts, key=lambda p: p["date"])


def esc(text):
    return html.escape(text, quote=False)


def fmt_date(d):
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def article_html(post, intro):
    meta = fmt_date(post["date"]) + (SEP + "Series Introduction" if intro else "")
    desc = f'\n          <div class="article-desc">{esc(post["subtitle"])}</div>' if post["subtitle"] else ""
    return (
        f'      <a href="https://byshannoncoleman.substack.com/p/{post["slug"]}?{UTM}{post["slug"]}" '
        f'class="article-link{" is-intro" if intro else ""}" target="_blank" rel="noopener">\n'
        f'        <div class="article-body">\n'
        f'          <div class="article-meta">{meta}</div>\n'
        f'          <div class="article-title">{esc(post["title"])}</div>{desc}\n'
        f'        </div>\n'
        f'        <div class="article-arrow" aria-hidden="true">Read &rarr;</div>\n'
        f'      </a>\n'
    )


def split_title(name):
    """Break a series name over two lines like the existing headings."""
    if ":" in name:
        head, tail = name.split(":", 1)
        return f"{esc(head)}:", esc(tail.strip())
    words = name.split()
    if len(words) < 2:
        return esc(name), ""
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) >= len(b) and (best is None or len(a) - len(b) < best[0]):
            best = (len(a) - len(b), a, b)
    if best is None:
        best = (0, " ".join(words[:-1]), words[-1])
    return esc(best[1]), esc(best[2])


def month_range(start, end):
    if (start.year, start.month) == (end.year, end.month):
        return f"{MONTHS[end.month - 1]} {end.year}"
    if start.year == end.year:
        return f"{MONTHS[start.month - 1]} &ndash; {MONTHS[end.month - 1]} {end.year}"
    return f"{MONTHS[start.month - 1]} {start.year} &ndash; {MONTHS[end.month - 1]} {end.year}"


def series_html(number, post):
    name = re.sub(r"^introducing\s+", "", post["title"], flags=re.I).strip()
    line1, line2 = split_title(name)
    heading = f"{line1}<br><em>{line2}</em>" if line2 else line1
    desc = f'\n      <p class="series-desc">{esc(post["subtitle"])}</p>' if post["subtitle"] else ""
    return (
        f"  <!-- SERIES {number} -->\n"
        f'  <div class="series-block">\n'
        f'    <div class="series-header">\n'
        f'      <div class="series-label">Series {number}{SEP}{month_range(post["date"], post["date"])}</div>\n'
        f'      <h2 class="series-title">{heading}</h2>{desc}\n'
        f"    </div>\n"
        f'    <div class="article-list">\n'
        f"{article_html(post, intro=True)}"
        f"    </div>\n"
        f"  </div>\n"
    )


def page_dates(block):
    return [datetime.strptime(d, "%b %d, %Y").date()
            for d in re.findall(r'<div class="article-meta">([A-Z][a-z]{2} \d{1,2}, \d{4})', block)]


def newest_block_span(page):
    """Return (start, end) offsets of the first (newest) series block."""
    start = page.index('<div class="series-block">')
    nxt = page.find("<!-- SERIES", start)
    return start, nxt if nxt != -1 else page.index("</main>")


def add_post(page, post):
    if post["title"].lower().startswith("introducing "):
        numbers = [int(n) for n in re.findall(r'<div class="series-label">Series (\d+)', page)]
        number = max(numbers, default=0) + 1
        anchor = page.index("  <!-- SERIES")
        return page[:anchor] + series_html(number, post) + page[anchor:], f"Series {number}"
    start, end = newest_block_span(page)
    block = page[start:end]
    marker = '<div class="article-list">\n'
    i = block.index(marker) + len(marker)
    block = block[:i] + article_html(post, intro=False) + block[i:]
    dates = page_dates(block)
    block = re.sub(r'(<div class="series-label">Series \d+) &nbsp;&bull;&nbsp; [^<]*',
                   lambda m: m.group(1) + SEP + month_range(min(dates), max(dates)), block, count=1)
    return page[:start] + block + page[end:], "newest series"


def home_row(post, number, name):
    slug = post["slug"]
    return (
        f'    <a href="https://byshannoncoleman.substack.com/p/{slug}?utm_source=portfolio&amp;utm_medium=homepage-writing&amp;utm_campaign=site&amp;utm_content={slug}" class="writing-link writing-link-viewall" target="_blank" rel="noopener">\n'
        f'      <div class="writing-pub">Series {number}{SEP}{esc(name)}</div>\n'
        f'      <div class="writing-title">{esc(post["title"])}</div>\n'
        f'    </a>\n'
    )


def add_home_row(home, post, number, name):
    """Put a new series at the top of the homepage Writing list."""
    if f"/p/{post['slug']}?" in home:
        return home
    anchor = home.index('    <a href="https://byshannoncoleman.substack.com/p/', home.index('id="writing"'))
    return home[:anchor] + home_row(post, number, name) + home[anchor:]


def bump_sitemap(path, pages):
    """Set the lastmod date for the given pages to today (UTC)."""
    if not os.path.exists(path):
        return
    today = datetime.now(timezone.utc).date().isoformat()
    with open(path, encoding="utf-8") as f:
        xml = f.read()
    for page in pages:
        loc = re.escape(f"https://shannonlcoleman.com/{page}")
        xml = re.sub(rf"(<loc>{loc}</loc>\s*<lastmod>)[^<]*(</lastmod>)", rf"\g<1>{today}\g<2>", xml)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", help="read the feed from a file instead of Substack")
    ap.add_argument("--page", default="writing.html")
    ap.add_argument("--home", default="index.html")
    ap.add_argument("--sitemap", default="sitemap.xml")
    args = ap.parse_args()

    with open(args.page, encoding="utf-8") as f:
        page = f.read()
    on_page = set(re.findall(r"substack\.com/p/([A-Za-z0-9-]+)", page))
    newest = max(page_dates(page))

    added, new_series, home_changes = 0, [], []
    for post in get_posts(args.feed):
        if post["slug"] in on_page or post["date"] < newest:
            continue
        page, where = add_post(page, post)
        on_page.add(post["slug"])
        added += 1
        if where != "newest series":
            name = re.sub(r"^introducing\s+", "", post["title"], flags=re.I).strip()
            new_series.append(f"{where}: {name}")
            home_changes.append((post, int(where.split()[-1]), name))
        print(f"Added {post['title']} ({fmt_date(post['date'])}) to {where}")

    if added:
        with open(args.page, "w", encoding="utf-8") as f:
            f.write(page)
    if added:
        bump_sitemap(args.sitemap, ["writing.html"] + ([""] if home_changes else []))
    if home_changes and os.path.exists(args.home):
        with open(args.home, encoding="utf-8") as f:
            home = f.read()
        for post, number, name in home_changes:
            home = add_home_row(home, post, number, name)
        with open(args.home, "w", encoding="utf-8") as f:
            f.write(home)
    print(f"{added} new post(s)")

    # Tell the workflow about new series so it can ask for a description.
    if new_series and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"new_series={'; '.join(new_series)}\n")


if __name__ == "__main__":
    sys.exit(main())
