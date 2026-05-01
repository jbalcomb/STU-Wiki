#!/bin/bash
# Build script for GitHub Pages deployment

set -e

echo "Building MoM Wiki for GitHub Pages..."

# Create docs directory if it doesn't exist
mkdir -p docs

# Copy frontend files
echo "Copying frontend files..."
cp -r frontend/src/* docs/

# Generate stats badge if possible
if command -v python &> /dev/null; then
    echo "Generating stats badge..."
    python -m mom_wiki.cli generate-stats --output docs/stats.svg 2>/dev/null || echo "Stats generation skipped"
fi

echo "Build complete! Files are in docs/"
echo "To deploy, commit and push the docs/ directory"
