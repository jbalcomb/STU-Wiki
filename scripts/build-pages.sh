#!/bin/bash
# Build script for GitHub Pages deployment.
#
# Cleans docs/ before each build so stale files from previous builds don't
# linger and so we don't accidentally overwrite hand-maintained content.

set -e

echo "Building MoM Wiki for GitHub Pages..."

rm -rf docs
mkdir -p docs

echo "Copying frontend files..."
cp -r frontend/src/* docs/

if command -v python &> /dev/null; then
    echo "Generating stats badge..."
    python -m mom_wiki.cli generate-stats --output docs/stats.svg 2>/dev/null || echo "Stats generation skipped"
fi

echo "Build complete! Files are in docs/"
echo "To deploy, commit and push the docs/ directory"
