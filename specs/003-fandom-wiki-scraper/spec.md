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

## Open questions (resolve during calibration)

- **HTML scraping vs MediaWiki API.** Fandom exposes the standard MediaWiki API at `/api.php`. The API is more reliable and gives us structured data (page metadata, parsed wikitext, infobox templates) without HTML-parsing brittleness. HTML scraping is "what you see is what you get" but tied to fandom's UI changes. Probably API for content, but we should look at both during calibration. Specifically interesting: `action=parse&page=X&prop=text|sections|categories|links|images|templates|wikitext`.
- **Crawl strategy.** Three obvious options:
  - **Seed-and-follow:** start from a small set of root pages, follow internal wiki links, deduplicate, stop at depth or count limit.
  - **Category traversal:** walk all categories (Spells, Units, Wizards, Items, etc.) and ingest their members. Maps naturally to `Node.type`.
  - **`allpages` enumeration:** ask the API for every page in the main namespace, ingest each. Most exhaustive but least filtered.
  Likely category traversal is the best fit — the structure is meaningful and aligns with our node taxonomy.
- **Infobox parsing.** Fandom infoboxes are wiki templates that render as structured tables. They contain the data we most want for `Node.attributes` (realm, cost, upkeep, melee/ranged/defense for units, abilities, etc.). Decisions:
  - Parse via the API's `prop=parsetree` (gives the template invocation directly with parameter names) or via post-render HTML pattern-matching.
  - Map common parameter names (`realm`, `cost`, `rarity`, etc.) to `Node.attributes` keys.
- **Link extraction → Relationships.** Internal wiki links from one page to another are the natural source of graph relationships. A spell page that links to a realm page → `belongs_to` edge. A unit page that links to abilities → `has_ability` edges. Heuristic: link target's inferred type vs source page's type.
- **Image handling.** Fandom hosts images on its CDN (`static.wikia.nocookie.net`). Two options:
  - **Reference by URL:** link to the CDN; corpus stays small, but breaks if fandom changes URLs or goes away.
  - **Download:** persist into `corpus/images/` like PDF extraction does. More work, more disk, more durable.
- **Rate limiting + politeness.** Existing scraper uses 1.0s between requests. Fandom has no documented hard limit but typical convention is 1 req/sec for unauthenticated scraping. Decision: keep at 1s default; respect any 429s with backoff.
- **Robots.txt.** Existing config has `respect_robots_txt: true` but the scraper doesn't actually check it. Wire it up.
- **Caching.** During calibration we'll fetch the same page repeatedly. Worth a local HTTP cache (e.g. `requests-cache`) so re-runs don't re-hammer fandom?
- **Decoration filtering.** Like PDF extraction had drop caps, fandom has predictable site chrome (header banner, sidebar, "Explore properties" footer, edit links, "On this wiki" boxes, ads if any). The MediaWiki-aware `mw-parser-output` selector already cuts most of this; we'll see what leaks during calibration.
- **Disambiguation pages and redirects.** Skip disambiguation, follow redirects.

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
