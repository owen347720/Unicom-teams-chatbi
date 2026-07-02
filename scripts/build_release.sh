#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
RELEASE_DIR="$ROOT_DIR/release"
ARCHIVE="$RELEASE_DIR/text2sql-images-$TAG.tar"

mkdir -p "$RELEASE_DIR"

docker build -t "text2sql-frontend:$TAG" "$ROOT_DIR/frontend"
docker build -t "text2sql-backend:$TAG" "$ROOT_DIR/backend"
docker build -t "text2sql-vanna:$TAG" "$ROOT_DIR/vanna-service"

docker save \
  "text2sql-frontend:$TAG" \
  "text2sql-backend:$TAG" \
  "text2sql-vanna:$TAG" \
  -o "$ARCHIVE"

cp "$ROOT_DIR/docker-compose.release.yml" "$RELEASE_DIR/"
cp "$ROOT_DIR/.env.example" "$RELEASE_DIR/.env.example"

cat > "$RELEASE_DIR/README.txt" <<EOF
Text2SQL release package

Image tag: $TAG

On the target server:
1. cp .env.example .env
2. edit .env and set IMAGE_TAG=$TAG plus MINIMAX_API_KEY
3. ./load_release.sh text2sql-images-$TAG.tar
4. docker compose -f docker-compose.release.yml --env-file .env up -d
EOF

cp "$ROOT_DIR/scripts/load_release.sh" "$RELEASE_DIR/"
cp "$ROOT_DIR/scripts/verify_release.sh" "$RELEASE_DIR/"

echo "Release package created at $RELEASE_DIR"
echo "Images archive: $ARCHIVE"
