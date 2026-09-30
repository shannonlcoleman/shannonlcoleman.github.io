// Cloudflare Worker: relays the Ground Truth RSS feed to the Writing page job.
// Substack refuses requests from GitHub's servers, so the job reads the feed
// through this Worker instead. It only ever fetches this one feed.
// Nothing is cached, so an error from Substack is never saved and replayed.
// Rate limits and server errors are retried a few times before giving up.
const FEED = "https://byshannoncoleman.substack.com/feed";
const WAITS_MS = [2000, 6000];

export default {
  async fetch(request) {
    if (request.method !== "GET") {
      return new Response("Method not allowed", { status: 405 });
    }
    let upstream;
    for (let attempt = 0; attempt <= WAITS_MS.length; attempt++) {
      upstream = await fetch(FEED, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
          "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
        cf: { cacheTtl: 0 },
      });
      if (upstream.ok || ![429, 500, 502, 503, 504].includes(upstream.status)) break;
      if (attempt < WAITS_MS.length) {
        await new Promise((resolve) => setTimeout(resolve, WAITS_MS[attempt]));
      }
    }
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("Content-Type") || "application/rss+xml; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  },
};
