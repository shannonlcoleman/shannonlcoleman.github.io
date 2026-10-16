"""Tell Bing (and the other IndexNow search engines) which pages changed.

Run by .github/workflows/indexnow.yml after each GitHub Pages build.

With no arguments, it submits the pages from sitemap.xml whose files changed
in the latest commit. With --all, it submits every page in sitemap.xml.
Only pages listed in the sitemap are ever submitted, so unlisted pages stay
unlisted.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HOST = "shannonlcoleman.com"
KEY = "d5dc05d77f0dc5f91f8ec4d8ea7ae976"  # public by design; must match the .txt file at the site root
ENDPOINT = "https://api.indexnow.org/indexnow"
ROOT = Path(__file__).resolve().parent.parent


def sitemap_urls():
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(ROOT / "sitemap.xml")
    return [loc.text.strip() for loc in tree.findall(".//s:loc", ns)]


def url_for_file(path):
    """Map a repo file path to its public URL."""
    if not path.endswith(".html"):
        return None
    if path == "index.html":
        return f"https://{HOST}/"
    if path.endswith("/index.html"):
        return f"https://{HOST}/{path[: -len('index.html')]}"
    return f"https://{HOST}/{path}"


def changed_files():
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if out.returncode != 0:
        return None  # no parent commit available; caller falls back to everything
    return [line for line in out.stdout.splitlines() if line]


def main():
    listed = sitemap_urls()

    if "--all" in sys.argv:
        urls = listed
    else:
        files = changed_files()
        if files is None:
            urls = listed
        else:
            changed = {url_for_file(f) for f in files} - {None}
            urls = [u for u in listed if u in changed]

    if not urls:
        print("No listed pages changed. Nothing to submit.")
        return

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    print("Submitting:\n  " + "\n  ".join(urls))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow responded {resp.status}.")
    except urllib.error.HTTPError as e:
        print(f"IndexNow responded {e.code}: {e.read().decode('utf-8', 'replace')}")
        # 429 means too many submissions; not worth failing the job over.
        if e.code != 429:
            sys.exit(1)


if __name__ == "__main__":
    main()
