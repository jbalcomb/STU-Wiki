# Quickstart: Master of Magic Wiki Corpus

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend development)
- Git
- Google account (for Drive API access)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/[username]/simtexwiki.git
cd simtexwiki

# Python dependencies
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend dependencies (optional, for development)
cd frontend
npm install
cd ..
```

### 2. Configure Google Drive

```bash
# Place your Google Cloud credentials file
cp path/to/credentials.json config/google-credentials.json

# First run will prompt for OAuth consent
python -m mom_wiki.drive_setup
```

### 3. Add Your First Source

Edit `sources.json`:

```json
[
  {
    "id": "wiki-chaos",
    "type": "web",
    "name": "MoM Wiki - Chaos Spells",
    "location": "https://masterofmagic.fandom.com/wiki/Category:Chaos_spells",
    "enabled": true
  }
]
```

Or use the CLI:

```bash
python -m mom_wiki.cli add-source \
  --type web \
  --name "MoM Wiki - Chaos Spells" \
  --url "https://masterofmagic.fandom.com/wiki/Category:Chaos_spells"
```

### 4. Run Your First Scrape

```bash
# Scrape all enabled sources
python -m mom_wiki.cli scrape

# Scrape a specific source
python -m mom_wiki.cli scrape --source-id wiki-chaos

# Watch progress
python -m mom_wiki.cli status
```

### 5. Start the API Server

```bash
# Start REST API on localhost:8000
python -m mom_wiki.api

# Test it
curl http://localhost:8000/api/v1/search?q=fireball
```

### 6. Start the MCP Server

```bash
# Start MCP server (for AI agent integration)
python -m mom_wiki.mcp_server

# Or add to Claude Desktop config:
# ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "mom-wiki": {
      "command": "python",
      "args": ["-m", "mom_wiki.mcp_server"],
      "cwd": "/path/to/simtexwiki"
    }
  }
}
```

### 7. View the Graph UI

```bash
# Serve the frontend (development)
cd frontend
npm run dev

# Or build for GitHub Pages
npm run build
```

Open http://localhost:3000 to view the 3D graph.

---

## Adding LBX Game Data

```bash
# Copy your MoM game files
cp /path/to/mom/MAGIC.LBX data/lbx/
cp /path/to/mom/SPELLDAT.LBX data/lbx/
cp /path/to/mom/UNITDATA.LBX data/lbx/

# Add as source
python -m mom_wiki.cli add-source \
  --type lbx \
  --name "MoM Game Data" \
  --path "data/lbx/"

# Parse and ingest
python -m mom_wiki.cli scrape --source-id lbx-gamedata
```

---

## Project Structure

```
simtexwiki/
├── mom_wiki/              # Python package
│   ├── scrapers/          # Web, PDF, LBX scrapers
│   ├── api/               # REST API (FastAPI)
│   ├── mcp_server/        # MCP server
│   ├── cli.py             # Command-line interface
│   └── models/            # Data models
├── frontend/              # JavaScript 3D graph UI
│   ├── src/
│   └── public/
├── corpus/                # Scraped data (JSON/Markdown)
├── data/                  # Source files (LBX, PDFs)
├── config/                # Configuration files
├── sources.json           # Source definitions
└── specs/                 # Feature specifications
```

---

## Common Tasks

### Rebuild Search Index

```bash
python -m mom_wiki.cli rebuild-index
```

### Sync to Google Drive

```bash
python -m mom_wiki.cli sync-drive
```

### Export for GitHub Pages

```bash
# Build static frontend + copy corpus
./scripts/build-pages.sh

# Push to gh-pages branch
git push origin gh-pages
```

### Generate Animated Stats

```bash
# Generate SVG stats badge
python -m mom_wiki.cli generate-stats --format svg

# Output: docs/stats.svg (animated)
```

---

## Troubleshooting

### "Google Drive quota exceeded"

Wait 24 hours or use a different Google account.

### "LBX parse error"

Ensure you're using original MoM 1.31 LBX files, not modified versions.

### "Search returns no results"

Run `python -m mom_wiki.cli rebuild-index` to regenerate the search index.

---

## Next Steps

1. Add more sources (PDFs, wiki pages)
2. Review extracted nodes in `corpus/nodes/`
3. Add custom relationships in `corpus/relationships.json`
4. Deploy to GitHub Pages
5. Connect your AI agent via MCP
