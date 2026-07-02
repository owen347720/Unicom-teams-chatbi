#!/usr/bin/env bash
set -euo pipefail

ARCHIVE="${1:-}"

if [[ -z "$ARCHIVE" ]]; then
  echo "Usage: ./load_release.sh text2sql-images-<tag>.tar" >&2
  exit 1
fi

if [[ ! -f "$ARCHIVE" ]]; then
  echo "Image archive not found: $ARCHIVE" >&2
  exit 1
fi

docker load -i "$ARCHIVE"
echo "Images loaded from $ARCHIVE"
