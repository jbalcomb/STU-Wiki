"""Command-line interface for Master of Magic Wiki Corpus."""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from .models import Source, SourceType, SourceStatus
from .storage import CorpusStorage
from .scrapers import get_scraper
from .search import SearchIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cmd_scrape(args):
    """Run scraper for configured sources."""
    storage = CorpusStorage(args.base_dir)
    sources = storage.load_sources()

    if not sources:
        print("No sources configured. Use 'add-source' to add sources.")
        return 1

    # Filter sources if specific ID provided
    if args.source_id:
        sources = [s for s in sources if s.id == args.source_id]
        if not sources:
            print(f"Source not found: {args.source_id}")
            return 1

    # Filter by type if specified
    if args.type:
        source_type = SourceType(args.type)
        sources = [s for s in sources if s.type == source_type]

    # Skip already-scraped sources unless --force is specified
    if not args.force:
        skipped = []
        to_scrape = []
        for s in sources:
            if s.last_status == SourceStatus.SUCCESS:
                skipped.append(s)
            else:
                to_scrape.append(s)

        if skipped:
            print(f"Skipping {len(skipped)} already-scraped source(s). Use --force to rescrape.")
            for s in skipped:
                print(f"  [SKIP] {s.name}")

        sources = to_scrape

    if not sources:
        print("No sources to scrape.")
        return 0

    print(f"Scraping {len(sources)} source(s)...")

    success_count = 0
    error_count = 0

    for source in sources:
        try:
            print(f"\n[{source.type.value.upper()}] {source.name}: {source.location}")
            scraper = get_scraper(source, storage)
            result = scraper.process_source(source)

            print(f"  Documents: {result['documents_created']} created, {result['documents_unchanged']} unchanged")
            print(f"  Nodes: {result['nodes_created']} created")
            print(f"  Status: {result['status']}")

            success_count += 1

        except Exception as e:
            logger.error(f"Failed to scrape {source.name}: {e}")
            print(f"  ERROR: {e}")
            error_count += 1

    print(f"\nComplete: {success_count} succeeded, {error_count} failed")

    # Update stats
    stats = storage.update_stats()
    print(f"Corpus: {stats['document_count']} documents, {stats['node_count']} nodes")

    return 0 if error_count == 0 else 1


def cmd_add_source(args):
    """Add a new source to the configuration."""
    storage = CorpusStorage(args.base_dir)

    # Validate source type
    try:
        source_type = SourceType(args.type)
    except ValueError:
        print(f"Invalid source type: {args.type}")
        print(f"Valid types: {', '.join([t.value for t in SourceType])}")
        return 1

    # Validate location
    location = args.location
    if source_type in [SourceType.PDF, SourceType.LBX]:
        # Check if file exists for local files
        if not Path(location).exists():
            print(f"Warning: File not found: {location}")

    # Create source
    source = Source(
        name=args.name,
        type=source_type,
        location=location,
        enabled=True
    )

    storage.add_source(source)
    print(f"Added source: {source.name} ({source.type.value})")
    print(f"  ID: {source.id}")
    print(f"  Location: {source.location}")

    return 0


def cmd_status(args):
    """Show scrape status and corpus statistics."""
    storage = CorpusStorage(args.base_dir)

    # Sources
    sources = storage.load_sources()
    print(f"=== Sources ({len(sources)}) ===")

    if sources:
        for source in sources:
            if source.enabled:
                status_icon = "[OK]" if source.last_status == SourceStatus.SUCCESS else "[--]"
            else:
                status_icon = "[X]"
            print(f"  {status_icon} [{source.type.value}] {source.name}")
            print(f"      ID: {source.id}")
            print(f"      Location: {source.location}")
            print(f"      Status: {source.last_status.value}")
            if source.last_scraped:
                print(f"      Last scraped: {source.last_scraped}")
            if source.last_error:
                print(f"      Error: {source.last_error}")
    else:
        print("  No sources configured")

    # Documents
    documents = storage.list_documents()
    print(f"\n=== Documents ({len(documents)}) ===")

    if args.verbose and documents:
        for doc in documents[:10]:  # Show first 10
            print(f"  - {doc.title}")
        if len(documents) > 10:
            print(f"  ... and {len(documents) - 10} more")

    # Nodes
    nodes = storage.list_nodes()
    print(f"\n=== Nodes ({len(nodes)}) ===")

    if nodes:
        # Count by type
        by_type = {}
        by_realm = {}
        for node in nodes:
            type_key = node.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            if node.attributes.realm:
                realm_key = node.attributes.realm.value
                by_realm[realm_key] = by_realm.get(realm_key, 0) + 1

        print("  By type:")
        for type_name, count in sorted(by_type.items()):
            print(f"    {type_name}: {count}")

        if by_realm:
            print("  By realm:")
            for realm_name, count in sorted(by_realm.items()):
                print(f"    {realm_name}: {count}")

    # Relationships
    relationships = storage.load_relationships()
    print(f"\n=== Relationships ({len(relationships)}) ===")

    # Jobs (recent)
    jobs_dir = Path(args.base_dir) / "corpus" / "jobs"
    if jobs_dir.exists():
        job_files = sorted(jobs_dir.glob("*.json"), reverse=True)[:5]
        if job_files:
            print(f"\n=== Recent Jobs ({len(job_files)}) ===")
            for job_file in job_files:
                job = storage.get_job(job_file.stem)
                if job:
                    status_icon = "[OK]" if job.status.value == "success" else "[--]"
                    print(f"  {status_icon} {job.status.value}: {job.source_id[:8]}... @ {job.started_at}")

    return 0


def cmd_list_sources(args):
    """List all configured sources."""
    storage = CorpusStorage(args.base_dir)
    sources = storage.load_sources()

    if not sources:
        print("No sources configured.")
        return 0

    print(f"{'ID':<36} {'Type':<6} {'Status':<10} {'Name'}")
    print("-" * 80)

    for source in sources:
        print(f"{source.id} {source.type.value:<6} {source.last_status.value:<10} {source.name}")

    return 0


def cmd_remove_source(args):
    """Remove a source from configuration."""
    storage = CorpusStorage(args.base_dir)
    sources = storage.load_sources()

    # Find and remove
    new_sources = [s for s in sources if s.id != args.source_id]

    if len(new_sources) == len(sources):
        print(f"Source not found: {args.source_id}")
        return 1

    storage.save_sources(new_sources)
    print(f"Removed source: {args.source_id}")

    return 0


def cmd_rebuild_index(args):
    """Rebuild the search index."""
    storage = CorpusStorage(args.base_dir)
    index = SearchIndex(storage)

    print("Rebuilding search index...")
    count = index.build()
    print(f"Indexed {count} items")

    return 0


def cmd_serve(args):
    """Start the API server."""
    try:
        import uvicorn
    except ImportError:
        print("uvicorn not installed. Run: pip install uvicorn")
        return 1

    print(f"Starting API server on http://{args.host}:{args.port}")
    uvicorn.run(
        "mom_wiki.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def cmd_mcp_serve(args):
    """Start the MCP server."""
    import asyncio
    from .mcp_server import serve

    print("Starting MCP server...")
    asyncio.run(serve())


def cmd_fandom_preview(args):
    """Side-by-side API vs HTML PoC for one or more fandom wiki pages.

    Each page is fetched twice — through the MediaWiki API and through
    plain HTML scraping — and the two results are written to disk for
    human comparison. Does not touch the corpus.
    """
    import requests

    from .scrapers.fandom_preview import (
        USER_AGENT,
        fetch_via_api,
        fetch_via_html,
        write_comparison,
    )

    output_dir = Path(args.output) if args.output else Path("preview-fandom")
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for raw_page in args.pages:
        from .scrapers.fandom_preview import _page_title_from_input
        page_title = _page_title_from_input(raw_page)
        print(f"Fetching '{page_title}'...", file=sys.stderr)

        api_result = fetch_via_api(page_title, session)
        if api_result.error:
            print(f"  API:  FAILED — {api_result.error}", file=sys.stderr)
        else:
            print(
                f"  API:  {len(api_result.parsed_html):,} html / "
                f"{len(api_result.wikitext):,} wikitext / "
                f"{len(api_result.categories)} cats / "
                f"{len(api_result.internal_links)} links / "
                f"{len(api_result.images)} images / "
                f"{len(api_result.templates)} templates",
                file=sys.stderr,
            )

        html_result = fetch_via_html(page_title, session)
        if html_result.error:
            print(f"  HTML: FAILED — {html_result.error}", file=sys.stderr)
        else:
            print(
                f"  HTML: {len(html_result.body_text):,} body / "
                f"{len(html_result.infoboxes)} infoboxes / "
                f"{len(html_result.categories)} cats / "
                f"{len(html_result.internal_links)} links / "
                f"{len(html_result.images)} images",
                file=sys.stderr,
            )

        page_dir = write_comparison(raw_page, output_dir, api_result, html_result)
        print(f"  → {page_dir}", file=sys.stderr)

    return 0


def cmd_extract_preview(args):
    """Run the new PDF extraction logic and write results to a temp directory.

    Does NOT touch the corpus. Used during feature 002 calibration so a human
    can walk through extracted output page by page and adjust thresholds.

    Three modes:
      - default: extract pages and write markdown + images to a preview dir.
      - --catalog: emit only the image-frequency table (no extraction).
      - --debug-page N: dump page N's structural anatomy (text blocks,
        drawings, images, with positions) — for designing recovery logic
        for content that text extraction can't see (e.g. vector-drawn
        illuminated initials).
    """
    from .scrapers.pdf_extraction import (
        build_catalog,
        extract_pdf,
        format_catalog_table,
        write_extraction,
    )

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    if args.debug_page is not None:
        return _debug_page(pdf_path, args.debug_page)

    if args.catalog:
        print(f"Cataloging {pdf_path.name}...", file=sys.stderr)
        catalog = build_catalog(pdf_path)
        print("")
        print(format_catalog_table(catalog, top=args.catalog_top))
        return 0

    page_range = None
    if args.pages:
        spec = args.pages.strip()
        if "-" in spec:
            start_str, end_str = spec.split("-", 1)
            page_range = (int(start_str), int(end_str))
        else:
            page_num = int(spec)
            page_range = (page_num, page_num)

    output_dir = Path(args.output) if args.output else Path(f"preview-{pdf_path.stem}")

    print(f"Extracting {pdf_path.name}...", file=sys.stderr)
    if page_range:
        print(f"  pages {page_range[0]}-{page_range[1]}", file=sys.stderr)
    print(f"  repetition threshold: {args.repetition_threshold}", file=sys.stderr)
    print(f"  min image dimension:  {args.min_image_dim}px", file=sys.stderr)

    result = extract_pdf(
        pdf_path,
        page_range=page_range,
        repetition_threshold=args.repetition_threshold,
        min_image_dim=args.min_image_dim,
    )

    markdown_path, images_dir = write_extraction(result, output_dir)

    catalog = result.catalog
    repeating_xrefs = sum(
        1 for x, info in catalog.images.items()
        if catalog.is_repeating(x, info.sha256, args.repetition_threshold)
    ) if catalog else 0

    print("", file=sys.stderr)
    print(f"Pages extracted:        {len(result.pages)}", file=sys.stderr)
    print(f"Embedded images kept:   {result.total_images}", file=sys.stderr)
    print(f"Decoration filtered:    {repeating_xrefs} unique image(s) flagged as repeating", file=sys.stderr)
    print(f"Fallback page renders:  {result.total_fallbacks}", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"Markdown: {markdown_path}", file=sys.stderr)
    print(f"Images:   {images_dir}", file=sys.stderr)
    return 0


def _debug_page(pdf_path: Path, page_num: int) -> int:
    """Dump a page's structural anatomy. Used to figure out where lost
    content (e.g. vector-drawn illuminated initials) actually lives in
    the PDF object model."""
    try:
        import fitz
    except ImportError:
        print("PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
        return 1

    doc = fitz.open(str(pdf_path))
    try:
        if page_num < 1 or page_num > len(doc):
            print(f"Page {page_num} out of range (PDF has {len(doc)} pages)", file=sys.stderr)
            return 1

        page = doc[page_num - 1]
        print(f"=== {pdf_path.name} — page {page_num} ===")
        print(f"Page size: {page.rect.width:.0f} x {page.rect.height:.0f} pt")

        print("")
        print("--- TEXT BLOCKS ---")
        blocks = page.get_text("blocks")
        print(f"count: {len(blocks)}")
        for i, block in enumerate(blocks):
            x0, y0, x1, y1, text, block_no, block_type = block
            type_label = "image-block" if block_type == 1 else "text-block"
            preview = text[:80].replace("\n", " ").strip()
            ellipsis = "..." if len(text) > 80 else ""
            print(f"  [{i:>3}] {type_label}  bbox=({x0:>5.0f},{y0:>5.0f})-({x1:>5.0f},{y1:>5.0f})")
            if preview:
                print(f"        text: {preview!r}{ellipsis}")

        print("")
        print("--- DRAWINGS (vector graphics ops) ---")
        drawings = page.get_drawings()
        print(f"count: {len(drawings)}")
        # Aggregate: cluster drawings by approximate bbox to surface initial-cap-shaped clusters
        for i, drawing in enumerate(drawings[:40]):
            rect = drawing.get("rect")
            if rect is None:
                continue
            op = drawing.get("type", "?")
            items = len(drawing.get("items", []))
            fill = drawing.get("fill")
            stroke = drawing.get("color")
            print(
                f"  [{i:>3}] type={op} bbox=({rect.x0:>5.0f},{rect.y0:>5.0f})-({rect.x1:>5.0f},{rect.y1:>5.0f}) "
                f"items={items} fill={fill} stroke={stroke}"
            )
        if len(drawings) > 40:
            print(f"  ... and {len(drawings) - 40} more")

        print("")
        print("--- EMBEDDED IMAGES ---")
        images = page.get_images(full=True)
        print(f"count: {len(images)}")
        for i, img in enumerate(images):
            # img tuple: (xref, smask, width, height, bpc, colorspace, alt, name, filter, ...)
            xref = img[0]
            width = img[2]
            height = img[3]
            filt = img[8] if len(img) > 8 else "?"
            print(f"  [{i:>3}] xref={xref} {width}x{height} filter={filt}")

        print("")
        print("--- FONTS ---")
        fonts = page.get_fonts(full=True)
        print(f"count: {len(fonts)}")
        for font in fonts:
            # font tuple: (xref, ext, type, basefont, name, encoding, ...)
            xref = font[0]
            ftype = font[2] if len(font) > 2 else "?"
            basefont = font[3] if len(font) > 3 else "?"
            name = font[4] if len(font) > 4 else "?"
            print(f"  xref={xref} type={ftype} basefont={basefont!r} name={name!r}")

        return 0
    finally:
        doc.close()


def cmd_generate_stats(args):
    """Generate animated SVG stats badge."""
    storage = CorpusStorage(args.base_dir)
    stats = storage.update_stats()

    # Generate SVG
    svg = generate_stats_svg(stats)

    # Write to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Stats badge generated: {output_path}")
    return 0


def generate_stats_svg(stats: dict) -> str:
    """Generate animated SVG stats badge."""
    doc_count = stats.get("document_count", 0)
    node_count = stats.get("node_count", 0)
    source_count = stats.get("source_count", 0)

    # Realm colors and counts
    by_realm = stats.get("by_realm", {})
    realm_colors = {
        "Life": "#FFD700",
        "Death": "#800080",
        "Nature": "#228B22",
        "Sorcery": "#4169E1",
        "Chaos": "#FF4500",
        "Arcane": "#C0C0C0"
    }

    # Build realm circles
    realm_circles = ""
    for i, (realm, color) in enumerate(realm_colors.items()):
        count = by_realm.get(realm, 0)
        x = 50 + i * 60
        realm_circles += f'''
        <g transform="translate({x}, 80)">
            <circle cx="0" cy="0" r="20" fill="{color}" opacity="0.8">
                <animate attributeName="r" values="18;22;18" dur="2s" begin="{i * 0.3}s" repeatCount="indefinite"/>
            </circle>
            <text x="0" y="5" text-anchor="middle" fill="{"#000" if realm in ["Life", "Arcane"] else "#fff"}" font-size="10" font-weight="bold">{count}</text>
            <text x="0" y="35" text-anchor="middle" fill="#888" font-size="8">{realm}</text>
        </g>'''

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="420" height="150" viewBox="0 0 420 150">
    <defs>
        <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1a1a2e"/>
            <stop offset="100%" style="stop-color:#16213e"/>
        </linearGradient>
    </defs>

    <!-- Background -->
    <rect width="420" height="150" fill="url(#bg-gradient)" rx="10"/>

    <!-- Title -->
    <text x="210" y="25" text-anchor="middle" fill="#4169E1" font-family="sans-serif" font-size="14" font-weight="bold">
        Master of Magic Wiki Corpus
    </text>

    <!-- Stats Row -->
    <g transform="translate(0, 35)">
        <text x="70" y="15" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="20" font-weight="bold">
            {doc_count}
            <animate attributeName="opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
        </text>
        <text x="70" y="30" text-anchor="middle" fill="#888" font-family="sans-serif" font-size="10">Documents</text>

        <text x="210" y="15" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="20" font-weight="bold">
            {node_count}
            <animate attributeName="opacity" values="0.7;1;0.7" dur="3s" begin="0.5s" repeatCount="indefinite"/>
        </text>
        <text x="210" y="30" text-anchor="middle" fill="#888" font-family="sans-serif" font-size="10">Nodes</text>

        <text x="350" y="15" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="20" font-weight="bold">
            {source_count}
            <animate attributeName="opacity" values="0.7;1;0.7" dur="3s" begin="1s" repeatCount="indefinite"/>
        </text>
        <text x="350" y="30" text-anchor="middle" fill="#888" font-family="sans-serif" font-size="10">Sources</text>
    </g>

    <!-- Realm Circles -->
    {realm_circles}

</svg>'''

    return svg


def cmd_sync_drive(args):
    """Sync files to/from Google Drive."""
    from .storage import DriveStorage

    drive = DriveStorage()
    if not drive.is_available():
        print("Google Drive not configured. Add credentials to config/google-credentials.json")
        return 1

    if args.list:
        files = drive.list_files()
        print(f"Files in MoMWikiCorpus folder ({len(files)}):")
        for f in files:
            print(f"  {f['name']} ({f.get('size', 'unknown')} bytes)")
        return 0

    if args.upload:
        file_id = drive.upload_file(args.upload)
        if file_id:
            link = drive.get_share_link(file_id)
            print(f"Uploaded: {args.upload}")
            print(f"Share link: {link}")
        else:
            print("Upload failed")
            return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="mom-wiki",
        description="Master of Magic Wiki Corpus CLI"
    )
    parser.add_argument(
        "--base-dir", "-d",
        default=".",
        help="Base directory for corpus (default: current directory)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Run scrapers on configured sources")
    scrape_parser.add_argument("--source-id", "-s", help="Scrape specific source by ID")
    scrape_parser.add_argument("--type", "-t", choices=["web", "pdf", "lbx"], help="Filter by source type")
    scrape_parser.add_argument("--force", "-f", action="store_true", help="Rescrape even if already successful")
    scrape_parser.set_defaults(func=cmd_scrape)

    # add-source command
    add_parser = subparsers.add_parser("add-source", help="Add a new source")
    add_parser.add_argument("name", help="Display name for the source")
    add_parser.add_argument("type", choices=["web", "pdf", "lbx"], help="Source type")
    add_parser.add_argument("location", help="URL or file path")
    add_parser.set_defaults(func=cmd_add_source)

    # status command
    status_parser = subparsers.add_parser("status", help="Show corpus status")
    status_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")
    status_parser.set_defaults(func=cmd_status)

    # list-sources command
    list_parser = subparsers.add_parser("list-sources", help="List configured sources")
    list_parser.set_defaults(func=cmd_list_sources)

    # remove-source command
    remove_parser = subparsers.add_parser("remove-source", help="Remove a source")
    remove_parser.add_argument("source_id", help="Source ID to remove")
    remove_parser.set_defaults(func=cmd_remove_source)

    # rebuild-index command
    index_parser = subparsers.add_parser("rebuild-index", help="Rebuild search index")
    index_parser.set_defaults(func=cmd_rebuild_index)

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload")
    serve_parser.set_defaults(func=cmd_serve)

    # mcp-serve command
    mcp_parser = subparsers.add_parser("mcp-serve", help="Start MCP server")
    mcp_parser.set_defaults(func=cmd_mcp_serve)

    # fandom-preview command (feature 003 calibration tool)
    fandom_parser = subparsers.add_parser(
        "fandom-preview",
        help="Side-by-side API vs HTML PoC for fandom wiki pages",
    )
    fandom_parser.add_argument(
        "pages",
        nargs="+",
        help="Wiki page titles or full URLs (e.g. 'Fireball' or "
             "'https://masterofmagic.fandom.com/wiki/Fireball')",
    )
    fandom_parser.add_argument(
        "--output",
        help="Output directory (default: preview-fandom/)",
    )
    fandom_parser.set_defaults(func=cmd_fandom_preview)

    # extract-preview command (feature 002 calibration tool)
    preview_parser = subparsers.add_parser(
        "extract-preview",
        help="Preview new PDF extraction without writing to corpus",
    )
    preview_parser.add_argument("pdf_path", help="Path to PDF file")
    preview_parser.add_argument(
        "--catalog",
        action="store_true",
        help="Emit the image-frequency table only — no extraction, no files written.",
    )
    preview_parser.add_argument(
        "--debug-page",
        type=int,
        default=None,
        help="Dump structural anatomy of one page (text blocks, drawings, images, fonts).",
    )
    preview_parser.add_argument(
        "--catalog-top",
        type=int,
        default=None,
        help="With --catalog, show only the top N most-frequent images.",
    )
    preview_parser.add_argument(
        "--pages",
        help="Page range to extract, 1-indexed (e.g. '1-10' or '5'). Default: all pages.",
    )
    preview_parser.add_argument(
        "--output",
        help="Output directory (default: preview-<pdf-stem>/)",
    )
    preview_parser.add_argument(
        "--repetition-threshold",
        type=int,
        default=3,
        help="Filter images appearing >= this many times in the doc (default: 3)",
    )
    preview_parser.add_argument(
        "--min-image-dim",
        type=int,
        default=50,
        help="Safety floor: minimum image dimension in px (default: 50)",
    )
    preview_parser.set_defaults(func=cmd_extract_preview)

    # generate-stats command
    stats_parser = subparsers.add_parser("generate-stats", help="Generate stats SVG badge")
    stats_parser.add_argument("--output", "-o", default="docs/stats.svg", help="Output file path")
    stats_parser.set_defaults(func=cmd_generate_stats)

    # sync-drive command
    drive_parser = subparsers.add_parser("sync-drive", help="Sync with Google Drive")
    drive_parser.add_argument("--list", "-l", action="store_true", help="List files in Drive")
    drive_parser.add_argument("--upload", "-u", help="Upload a file to Drive")
    drive_parser.set_defaults(func=cmd_sync_drive)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
