# Feature 003: Fandom Wiki Scraper

**Branch**: `003-fandom-wiki-scraper` | **Status**: scaffolding; calibration pending.

## Goal

Build a real scraper for the [Master of Magic Fandom Wiki](https://masterofmagic.fandom.com/) that produces high-quality, structured corpus content for the project's primary knowledge target. Today's `mom_wiki/scrapers/web_scraper.py` fetches a single URL per source and emits flat markdown; that's not enough to ingest a community wiki of a few thousand pages with structured infoboxes, categories, and inter-page links.

## Why

Per the project's content priorities: the corpus's high-value content is community sources (fandom wiki, realms-beyond, usenet), not strategy guide PDFs. The fandom wiki is the most structured of those sources — predictable templates, explicit categories, infoboxes that map cleanly onto our `Node.attributes`, and a stable MediaWiki-based URL scheme. Getting it right unlocks most of the wiki's value with one scraper, and produces a baseline pattern (calibration → spec → ship) we can re-apply to realms-beyond and usenet next.

## Process: calibration-driven (per feature 002 pattern)

Same shape that worked well for 002:

1. **Scaffold a preview tool** that runs the new fandom scraping logic and writes results to a temp directory without touching `corpus/`.
2. **Walk through real wiki pages** (a spell, a unit, a wizard, a race, a category index) with a human reviewer. For each, decide what's right; adjust the heuristics.
3. **Codify findings** into the scraper module + this spec.
4. **Ship** by wiring into the production `WebScraper` (or a new `FandomScraper`) and re-scraping fandom-wiki sources.

The existing `web_scraper.py` is a usable starting point but not the destination — its single-page model and its `_extract_content` boil-everything-down-to-markdown approach lose the structured information we want from fandom (infoboxes, categories as tags, inter-page links as relationships).

## Out of scope

- **Realms Beyond and usenet sources.** Separate features (004, 005) — different platforms, different decoration patterns, different harvest mechanisms.
- **General-purpose web scraping.** Fandom-specific patterns are fine; we don't need to make the scraper generic across arbitrary wikis.
- **Edit-history harvesting.** We capture the current rendered state, not revision history.
- **Talk / discussion pages.** Editorial-side artifacts, not corpus content.
- **User pages.** Same.

## Decisions

- **HTML scraping vs MediaWiki API → PoC both, then decide.** Don't pre-commit. First calibration step is a side-by-side proof of concept on a handful of seed pages: fetch each via fandom's MediaWiki API (`/api.php?action=parse&page=X&prop=text|sections|categories|links|images|templates|wikitext`) *and* via plain HTML scraping, dump both outputs, eyeball the difference. Pick the winner based on what we actually see — content quality, infobox fidelity, decoration leakage, brittleness under change.
- **Crawl strategy → all of `masterofmagic.fandom.com`.** We want the whole sub-domain, not a curated subset. Preferred enumeration path: the MediaWiki API's `action=query&list=allpages&apnamespace=0` gives every content page in one paginated walk. If for some reason the API path is unavailable or unsuitable (decided in the PoC step), fall back to seed-and-follow from the wiki home page (`https://masterofmagic.fandom.com/wiki/Master_of_Magic_Wiki`), enqueueing every internal wiki link, deduplicating, and respecting the same-subdomain constraint.
- **Image handling → download + track attribution.** Fandom hosts images on its CDN (`static.wikia.nocookie.net`); the URLs change and content can be removed, so we must keep our own copy. Persist into `corpus/images/` per the existing pattern. **Track attribution metadata** alongside each image — original CDN URL, source page URL, license (CC-BY-SA 3.0 by default for fandom content), uploader if exposed by the API, and modification date. This is a license requirement (CC-BY-SA 3.0 mandates attribution and share-alike), not a nice-to-have, if the corpus is going to be redistributable. Schema for this: per-image JSON sidecar in `corpus/images/<name>.json`, or a top-level `corpus/attributions.json` keyed by filename. To decide.

## Open questions (resolve during calibration)

- **Infobox parsing.** Fandom infoboxes are wiki templates that render as structured tables. They contain the data we most want for `Node.attributes` (realm, cost, upkeep, melee/ranged/defense for units, abilities, etc.). Decisions to make:
  - Parse via the API's `prop=parsetree` / `prop=wikitext` (gives the template invocation with parameter names directly) or via post-render HTML pattern-matching against `aside.portable-infobox` / `table.infobox` selectors.
  - Map common parameter names (`realm`, `cost`, `rarity`, etc.) to `Node.attributes` keys. Need a real survey of which names appear; the PoC's first job is to dump infobox params for each seed page so we can see the real keyspace.
- **Link extraction → Relationships.** Internal wiki links from one page to another are the natural source of graph relationships. A spell page that links to a realm page → `belongs_to` edge. A unit page that links to abilities → `has_ability` edges. Heuristic: link target's inferred type vs source page's type.
- **Attribution storage shape.** Per-image JSON sidecars vs a single `corpus/attributions.json` index vs extending `Document.metadata`. Per-image is robust to deletion; a single index is easier to query. Decide once we see how many images we're actually pulling.
- **Rate limiting + politeness.** Existing scraper uses 1.0s between requests. Fandom has no documented hard limit but typical convention is 1 req/sec for unauthenticated scraping. Decision: keep at 1s default; respect any 429s with backoff.
- **Robots.txt.** Existing config has `respect_robots_txt: true` but the scraper doesn't actually check it. Wire it up before going wide.
- **Caching.** During calibration we'll fetch the same page repeatedly. Worth a local HTTP cache (e.g. `requests-cache`) so re-runs don't re-hammer fandom?
- **Decoration filtering.** Like PDF extraction had drop caps, fandom has predictable site chrome (header banner, sidebar, "Explore properties" footer, edit links, "On this wiki" boxes, ads if any). The MediaWiki-aware `mw-parser-output` selector already cuts most of this; we'll see what leaks during calibration.
- **Disambiguation pages and redirects.** Skip disambiguation pages; follow redirects.

## What to learn from feature 002 (PDF extraction)

The PDF feature taught a few things worth carrying forward:

- **Verify before pinning numeric thresholds.** Don't commit to "scrape pages with > N category members" or similar without seeing the actual distribution.
- **Generate a debug-mode output for a single page** so the human can inspect the raw structural breakdown (categories, links, infobox params, sections) before designing extraction heuristics.
- **Curation gaps are real and OK.** Some fandom-wiki content (editorial decisions about which inter-page links are meaningful relationships vs incidental cross-references) won't be auto-extractable. Document those gaps; keep them out of scope for the extractor.
- **Tests should be golden-file + property tests.** Capture a few representative pages as fixtures, assert specific properties (e.g. "spell pages have a `realm` attribute"), and use `xfail(strict=True)` for known curation gaps.

## Test corpus

Calibration uses live fandom URLs. Seed set, ordered roughly simple → complex:

- `https://masterofmagic.fandom.com/wiki/Fireball` — a Chaos spell with a simple infobox.
- `https://masterofmagic.fandom.com/wiki/Magic_Spirit` — an Arcane summoning spell, the very first one anyone learns.
- `https://masterofmagic.fandom.com/wiki/Ariel` — a wizard with a complex infobox (spell ranks, special ability) + biographical text.
- `https://masterofmagic.fandom.com/wiki/Halflings` — a race with stats, special abilities, food/production properties.
- `https://masterofmagic.fandom.com/wiki/Chaos` — a realm page; should parse as `type=realm` and act as the target of `belongs_to` edges from many spells.
- `https://masterofmagic.fandom.com/wiki/Category:Spells` — a category index, exercises the traversal path.

Local caching (per the "caching" open question) will keep re-runs of the calibration tool from re-hitting fandom on every iteration.

## Success criteria

- For a spell page (e.g. Fireball): extracted markdown is the page's prose; `Node.attributes` has `realm`, `cost`, `rarity` from the infobox; categories are tags on the document.
- For a wizard page (e.g. Ariel): infobox parameters end up structured (spell ranks per realm, special ability, banner color); links to wizards / abilities / realms become Relationships.
- For a category page (Category:Spells): scraper enumerates members and ingests each; doesn't ingest the category page itself as a content document.
- Re-running the scraper on a previously-scraped fandom source produces no diff (idempotent ingestion still works — feature 001's storage layer should already handle this).
- Decoration-free: no fandom site chrome, edit links, "On this wiki" boxes, or sidebar elements in body markdown.
- Polite: respects robots.txt; ≤1 req/sec by default; backs off on 429.

## Notes on the existing `web_scraper.py`

It's not throwaway — it works for single-page Wikipedia-style ingestion (sources.json already has a successful Wikipedia MoM scrape). The fandom feature should either (a) extend it with fandom-specific subclassing/branching or (b) ship a new `FandomScraper` that registers for a new `SourceType.FANDOM` (or a `domain == fandom.com` check on `SourceType.WEB`). Decide during calibration based on how much overlap remains.
