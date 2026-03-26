#!/bin/bash
# Flatten the project structure for arXiv submission
# arXiv prefers flat file uploads

set -e

SUBMISSION_DIR="submission"
rm -rf "$SUBMISSION_DIR"
mkdir -p "$SUBMISSION_DIR"

# Copy main.tex and rewrite \input paths
sed 's|sections/||g' main.tex > "$SUBMISSION_DIR/main.tex"

# Copy all section files
cp sections/*.tex "$SUBMISSION_DIR/"

# Copy bibliography
cp references.bib "$SUBMISSION_DIR/"

# Copy compiled bibliography if it exists
[ -f main.bbl ] && cp main.bbl "$SUBMISSION_DIR/"

# Copy figures if any exist
if ls figures/* 1>/dev/null 2>&1; then
  cp figures/* "$SUBMISSION_DIR/"
fi

# Create tar.gz
cd "$SUBMISSION_DIR"
tar -czf ../arxiv-submission.tar.gz *
cd ..

echo "Submission archive created: arxiv-submission.tar.gz"
echo "Contents:"
tar -tzf arxiv-submission.tar.gz
