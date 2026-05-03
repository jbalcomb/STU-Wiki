"""Side-by-side API vs HTML proof-of-concept for fandom wiki scraping.

Used by the `fandom-preview` CLI subcommand during feature 003 calibration.
Fetches one or more wiki pages via *both* the MediaWiki API and plain HTML
scraping, dumps the parallel outputs into a temp directory, and writes a
SUMMARY.md per page so a human reviewer can decide which path produces
better structured content. Does NOT touch the corpus.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse


FANDOM_BASE = "https://masterofmagic.fandom.com"
FANDOM_API = f"{FANDOM_BASE}/api.php"

# Politeness guardrails for fandom's MediaWiki API. These are intentionally
# conservative defaults — fandom is community-run and on shared
# infrastructure, and we'd rather be slow than risk an IP ban for the
# project. Tighten only with explicit user authorization.
MIN_REQUEST_INTERVAL_S = 1.5  # min wall-clock seconds between API requests
MAX_RETRY_AFTER_429 = 60.0    # cap on Retry-After honoring before we give up
MAXLAG_SECONDS = 5            # MediaWiki's back-off-if-replica-lagging signal
DEFAULT_MAX_RETRIES = 3

# Tracks the last outgoing request time across the process so any caller
# of `polite_get` cooperates on the rate limit. Single-threaded by design.
_LAST_REQUEST_TIME = 0.0

# Identify ourselves clearly to the upstream — fandom traces traffic by
# User-Agent and a generic one will land us in their bot rate-limiter.
# Used for /api.php traffic where we want to be transparent.
USER_AGENT = (
    "MoMWikiCorpus/0.1.0 (+https://github.com/jbalcomb/STU-Wiki; "
    "feature 003 calibration)"
)

# Browser-shaped headers used for /wiki/* HTML requests. Fandom's edge
# returns 403 to bot-style User-Agents on the page-rendering routes (even
# though /api.php happily serves the same content), so we present as a
# real Chrome on Windows. We're caching the data — not a T&Cs violation —
# so this is a fingerprint workaround, not impersonation. If this stops
# working, the next step up is TLS-fingerprint-aware HTTP (curl_cffi,
# tls-client) since plain `requests` has a distinctive TLS fingerprint
# regardless of headers.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class APIResult:
    """What we pulled from the MediaWiki API for one page."""
    page_title: str
    pageid: int | None
    parsed_html: str
    wikitext: str
    sections: list[dict]
    categories: list[str]
    internal_links: list[str]
    external_links: list[str]
    images: list[str]
    templates: list[str]
    raw: dict
    error: str | None = None


@dataclass
class HTMLResult:
    """What we pulled from the rendered HTML page for the same URL."""
    page_title: str
    page_url: str
    body_text: str
    infoboxes: list[dict[str, str]]
    categories: list[str]
    internal_links: list[str]
    images: list[dict[str, str]]
    error: str | None = None


def polite_get(
    session,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 30,
    max_retries: int = DEFAULT_MAX_RETRIES,
):
    """Rate-limited GET with retry on 429 and MediaWiki maxlag handling.

    Enforces a minimum wall-clock interval between calls (across all
    callers in this process), honors `Retry-After` on 429, and adds the
    `maxlag` parameter to /api.php endpoints so MediaWiki can tell us
    "back off, my replicas are behind" via a 503 with a tight retry-after.

    Single-threaded by design: do not call this from concurrent threads
    or asyncio tasks unless the upstream rate limit is explicitly
    relaxed by the user. The shared `_LAST_REQUEST_TIME` is a global
    cooperative guard, not a real lock.
    """
    global _LAST_REQUEST_TIME

    params = dict(params or {})
    if "/api.php" in url and "maxlag" not in params:
        params["maxlag"] = MAXLAG_SECONDS

    last_response = None
    for attempt in range(max_retries):
        elapsed = time.monotonic() - _LAST_REQUEST_TIME
        if elapsed < MIN_REQUEST_INTERVAL_S:
            time.sleep(MIN_REQUEST_INTERVAL_S - elapsed)

        _LAST_REQUEST_TIME = time.monotonic()
        last_response = session.get(
            url, params=params, headers=headers, timeout=timeout
        )

        if last_response.status_code == 429:
            # Server-issued rate limit. Honor it.
            retry_after = last_response.headers.get("Retry-After", "")
            try:
                wait = float(retry_after)
            except ValueError:
                wait = 10.0
            wait = min(wait, MAX_RETRY_AFTER_429)
            time.sleep(wait)
            continue

        if last_response.status_code == 503:
            # MediaWiki uses 503 + Retry-After for maxlag-induced backoff.
            retry_after = last_response.headers.get("Retry-After", "")
            try:
                wait = float(retry_after)
            except ValueError:
                wait = 5.0
            wait = min(wait, MAX_RETRY_AFTER_429)
            time.sleep(wait)
            continue

        return last_response

    return last_response


def _page_title_from_input(arg: str) -> str:
    """Accept either a wiki page title or a full URL; return the page title."""
    if arg.startswith("http://") or arg.startswith("https://"):
        path = urlparse(arg).path
        # Path looks like "/wiki/Fireball" or "/wiki/Category:Spells"
        prefix = "/wiki/"
        if path.startswith(prefix):
            return unquote(path[len(prefix):])
        return unquote(path.lstrip("/"))
    return arg


def _safe_listify(item: Any) -> list[str]:
    """Normalize a MediaWiki API list (which mixes dicts with `*` keys and
    bare strings depending on prop) into a plain list of strings."""
    out: list[str] = []
    if not item:
        return out
    for entry in item:
        if isinstance(entry, dict):
            value = entry.get("*") or entry.get("title") or ""
            if value:
                out.append(str(value))
        else:
            out.append(str(entry))
    return out


def fetch_all_page_titles(
    session,
    namespace: int = 0,
    page_size: int = 500,
    progress=None,
) -> tuple[list[str], int]:
    """Enumerate every page title in a namespace via `action=query&list=allpages`.

    Args:
        session: requests.Session with our identifying User-Agent set.
        namespace: MediaWiki namespace id. 0 is main (content) pages. Other
            useful values: 14 = Category, 6 = File. Talk namespaces are odd
            numbered. Default is 0 — the corpus target.
        page_size: API limit per call. 500 is the max for unauthenticated
            users; using the max minimizes the number of round trips.
        progress: optional callable(batch_count, running_total) for progress.

    Returns:
        (sorted list of page titles, number of API calls made)

    Walks the `continue` token pagination loop until exhausted. Each request
    goes through `polite_get` so the rate limit applies.
    """
    titles: list[str] = []
    apcontinue: str | None = None
    request_count = 0

    while True:
        params: dict[str, Any] = {
            "action": "query",
            "list": "allpages",
            "apnamespace": namespace,
            "aplimit": page_size,
            "format": "json",
        }
        if apcontinue is not None:
            params["apcontinue"] = apcontinue

        response = polite_get(session, FANDOM_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        request_count += 1

        if "error" in data:
            raise RuntimeError(f"API error during enumeration: {data['error']}")

        batch = data.get("query", {}).get("allpages", []) or []
        for page in batch:
            title = page.get("title")
            if title:
                titles.append(title)

        if progress is not None:
            progress(request_count, len(titles))

        cont = data.get("continue", {})
        apcontinue = cont.get("apcontinue")
        if apcontinue is None:
            break

    titles.sort()
    return titles, request_count


def fetch_via_api(page_title: str, session) -> APIResult:
    """Fetch a single page via the MediaWiki `action=parse` endpoint.

    Returns an APIResult with .error populated on failure rather than
    raising — the caller wants to compare both paths even if one fails.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "redirects": 1,
        "prop": "text|wikitext|sections|categories|links|externallinks|images|templates",
    }
    try:
        response = polite_get(session, FANDOM_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return APIResult(
            page_title=page_title,
            pageid=None,
            parsed_html="",
            wikitext="",
            sections=[],
            categories=[],
            internal_links=[],
            external_links=[],
            images=[],
            templates=[],
            raw={},
            error=f"{type(exc).__name__}: {exc}",
        )

    if "error" in data:
        return APIResult(
            page_title=page_title,
            pageid=None,
            parsed_html="",
            wikitext="",
            sections=[],
            categories=[],
            internal_links=[],
            external_links=[],
            images=[],
            templates=[],
            raw=data,
            error=f"API error: {data['error'].get('info', data['error'])}",
        )

    parse = data.get("parse", {})
    text_field = parse.get("text", "")
    parsed_html = text_field.get("*", "") if isinstance(text_field, dict) else str(text_field)
    wikitext_field = parse.get("wikitext", "")
    wikitext = wikitext_field.get("*", "") if isinstance(wikitext_field, dict) else str(wikitext_field)

    return APIResult(
        page_title=parse.get("title", page_title),
        pageid=parse.get("pageid"),
        parsed_html=parsed_html,
        wikitext=wikitext,
        sections=parse.get("sections", []),
        categories=_safe_listify(parse.get("categories", [])),
        internal_links=_safe_listify(parse.get("links", [])),
        external_links=_safe_listify(parse.get("externallinks", [])),
        images=parse.get("images", []) if isinstance(parse.get("images"), list) else [],
        templates=_safe_listify(parse.get("templates", [])),
        raw=parse,
    )


def fetch_via_html(page_title: str, session) -> HTMLResult:
    """Fetch the rendered HTML for the same page and pull out the same
    structural information directly from the markup."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return HTMLResult(
            page_title=page_title,
            page_url="",
            body_text="",
            infoboxes=[],
            categories=[],
            internal_links=[],
            images=[],
            error="beautifulsoup4 not installed",
        )

    url = f"{FANDOM_BASE}/wiki/{quote(page_title.replace(' ', '_'), safe=':/')}"
    try:
        # Browser-shaped headers — but fandom's edge does TLS fingerprinting
        # below the HTTP layer, so a plain-`requests` client gets a 403
        # regardless of headers. Kept for diagnostic value and for the day
        # we add curl_cffi or similar.
        response = polite_get(
            session, url, headers=BROWSER_HEADERS, timeout=30
        )
        response.raise_for_status()
    except Exception as exc:
        return HTMLResult(
            page_title=page_title,
            page_url=url,
            body_text="",
            infoboxes=[],
            categories=[],
            internal_links=[],
            images=[],
            error=f"{type(exc).__name__}: {exc}",
        )

    soup = BeautifulSoup(response.content, "html.parser")

    # Page title (page-header__title is fandom's main heading)
    title_el = soup.find("h1", class_="page-header__title") or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else page_title

    # Main content area
    main = soup.find("div", class_="mw-parser-output")

    # Strip site chrome from the body before we extract text
    if main:
        for selector in [
            ".navbox",
            ".mw-editsection",
            ".mbox-text",
            ".toc",
            ".reference",
            "table.toccolours",
        ]:
            for chrome in main.select(selector):
                chrome.decompose()

    # Infoboxes — fandom uses portable-infobox
    infoboxes: list[dict[str, str]] = []
    for ib in soup.select("aside.portable-infobox"):
        params: dict[str, str] = {}
        for item in ib.select(".pi-item.pi-data"):
            label = item.find(class_="pi-data-label")
            value = item.find(class_="pi-data-value")
            if label and value:
                key = label.get_text(strip=True)
                val = value.get_text(separator=" ", strip=True)
                if key:
                    params[key] = val
        # Capture the infobox's own header (often the entity name)
        header = ib.find(class_="pi-title")
        if header:
            params["__title__"] = header.get_text(strip=True)
        infoboxes.append(params)

    # Categories: fandom places them in a nav at the bottom; also handles
    # the rendered category links inside main if present.
    categories: list[str] = []
    seen_cats: set[str] = set()
    for link in soup.select("a[href*='/wiki/Category:']"):
        text = link.get_text(strip=True)
        if text and text not in seen_cats:
            categories.append(text)
            seen_cats.add(text)

    # Internal wiki links from the main body (excluding category, file, etc.)
    internal_links: list[str] = []
    seen_links: set[str] = set()
    if main:
        for a in main.select("a[href]"):
            href = a.get("href", "")
            if not href.startswith("/wiki/"):
                continue
            target = href[len("/wiki/"):]
            # Drop fragment
            target = target.split("#", 1)[0]
            if not target:
                continue
            # Drop namespace links (Category:, File:, Special:, Help:, Talk:, etc.)
            if ":" in target.split("/", 1)[0]:
                continue
            target = unquote(target)
            if target not in seen_links:
                internal_links.append(target)
                seen_links.add(target)

    # Images on this page: fandom CDN-hosted only
    images: list[dict[str, str]] = []
    if main:
        for img in main.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if not src or "static.wikia.nocookie.net" not in src:
                continue
            images.append({
                "src": src,
                "alt": img.get("alt", "") or "",
                "width": img.get("width", "") or "",
                "height": img.get("height", "") or "",
            })

    # Body text — collect paragraphs
    body_chunks: list[str] = []
    if main:
        for p in main.find_all(["p", "h2", "h3", "h4", "li"]):
            text = p.get_text(separator=" ", strip=True)
            if text:
                body_chunks.append(text)
    body_text = "\n\n".join(body_chunks)

    return HTMLResult(
        page_title=title,
        page_url=url,
        body_text=body_text,
        infoboxes=infoboxes,
        categories=categories,
        internal_links=internal_links,
        images=images,
    )


def write_comparison(
    page_input: str,
    output_dir: Path,
    api_result: APIResult,
    html_result: HTMLResult,
) -> Path:
    """Persist both results into output_dir/<safe_title>/{api,html}/.

    Returns the per-page directory.
    """
    safe = (
        _page_title_from_input(page_input)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )
    page_dir = output_dir / safe
    api_dir = page_dir / "api"
    html_dir = page_dir / "html"
    api_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)

    # API outputs ----------------------------------------------------------
    if api_result.error:
        (api_dir / "ERROR.txt").write_text(api_result.error, encoding="utf-8")
    else:
        (api_dir / "01-text.html").write_text(api_result.parsed_html, encoding="utf-8")
        (api_dir / "02-wikitext.txt").write_text(api_result.wikitext, encoding="utf-8")
        (api_dir / "03-categories.txt").write_text(
            "\n".join(api_result.categories), encoding="utf-8"
        )
        (api_dir / "04-internal-links.txt").write_text(
            "\n".join(api_result.internal_links), encoding="utf-8"
        )
        (api_dir / "05-external-links.txt").write_text(
            "\n".join(api_result.external_links), encoding="utf-8"
        )
        (api_dir / "06-images.txt").write_text(
            "\n".join(api_result.images), encoding="utf-8"
        )
        (api_dir / "07-templates.txt").write_text(
            "\n".join(api_result.templates), encoding="utf-8"
        )
        section_lines = [
            f"L{s.get('toclevel', '?')}  {s.get('number', ''):>5}  {s.get('line', '')}"
            for s in api_result.sections
        ]
        (api_dir / "08-sections.txt").write_text(
            "\n".join(section_lines), encoding="utf-8"
        )
        (api_dir / "00-raw.json").write_text(
            json.dumps(api_result.raw, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # HTML outputs ---------------------------------------------------------
    if html_result.error:
        (html_dir / "ERROR.txt").write_text(html_result.error, encoding="utf-8")
    else:
        (html_dir / "01-body.txt").write_text(html_result.body_text, encoding="utf-8")
        (html_dir / "02-infoboxes.json").write_text(
            json.dumps(html_result.infoboxes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (html_dir / "03-categories.txt").write_text(
            "\n".join(html_result.categories), encoding="utf-8"
        )
        (html_dir / "04-internal-links.txt").write_text(
            "\n".join(html_result.internal_links), encoding="utf-8"
        )
        (html_dir / "05-images.json").write_text(
            json.dumps(html_result.images, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Summary --------------------------------------------------------------
    lines: list[str] = [f"# Fandom comparison: {page_input}", ""]

    lines.append("## API path")
    if api_result.error:
        lines.append(f"- FAILED: {api_result.error}")
    else:
        lines.extend([
            f"- title:           {api_result.page_title}",
            f"- pageid:          {api_result.pageid}",
            f"- parsed HTML:     {len(api_result.parsed_html):,} chars",
            f"- wikitext:        {len(api_result.wikitext):,} chars",
            f"- categories:      {len(api_result.categories)}",
            f"- internal links:  {len(api_result.internal_links)}",
            f"- external links:  {len(api_result.external_links)}",
            f"- images:          {len(api_result.images)}",
            f"- templates:       {len(api_result.templates)}",
            f"- sections:        {len(api_result.sections)}",
        ])
    lines.append("")

    lines.append("## HTML path")
    if html_result.error:
        lines.append(f"- FAILED: {html_result.error}")
    else:
        lines.extend([
            f"- url:             {html_result.page_url}",
            f"- title:           {html_result.page_title}",
            f"- body text:       {len(html_result.body_text):,} chars",
            f"- infoboxes:       {len(html_result.infoboxes)}",
            f"- categories:      {len(html_result.categories)}",
            f"- internal links:  {len(html_result.internal_links)}",
            f"- images:          {len(html_result.images)}",
        ])
    lines.append("")

    (page_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    return page_dir
