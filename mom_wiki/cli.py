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


def cmd_extract_preview(args):
    """Run the new PDF extraction logic and write results to a temp directory.

    Does NOT touch the corpus. Used during feature 002 calibration so a human
    can walk through extracted output page by page and adjust thresholds.
    """
    from .scrapers.pdf_extraction import extract_pdf, write_extraction

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

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
    print(f"  min image dimension: {args.min_image_dim}px", file=sys.stderr)

    result = extract_pdf(
        pdf_path,
        page_range=page_range,
        min_image_dim=args.min_image_dim,
    )

    markdown_path, images_dir = write_extraction(result, output_dir)

    print("", file=sys.stderr)
    print(f"Pages extracted:  {len(result.pages)}", file=sys.stderr)
    print(f"Embedded images:  {result.total_images}", file=sys.stderr)
    print(f"Fallback renders: {result.total_fallbacks}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Markdown: {markdown_path}", file=sys.stderr)
    print(f"Images:   {images_dir}", file=sys.stderr)
    return 0


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

    # extract-preview command (feature 002 calibration tool)
    preview_parser = subparsers.add_parser(
        "extract-preview",
        help="Preview new PDF extraction without writing to corpus",
    )
    preview_parser.add_argument("pdf_path", help="Path to PDF file")
    preview_parser.add_argument(
        "--pages",
        help="Page range to extract, 1-indexed (e.g. '1-10' or '5'). Default: all pages.",
    )
    preview_parser.add_argument(
        "--output",
        help="Output directory (default: preview-<pdf-stem>/)",
    )
    preview_parser.add_argument(
        "--min-image-dim",
        type=int,
        default=200,
        help="Minimum image dimension (px) to be considered non-decorative (default: 200)",
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
