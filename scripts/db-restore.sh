#!/usr/bin/env bash
# Restore Neo4j database from Hetzner Object Storage.
# Usage: bash scripts/db-restore.sh [tag]
# If no tag, lists available backups. With tag, downloads and restores.

set -euo pipefail

S3_ENDPOINT="https://hel1.your-objectstorage.com"
S3_BUCKET="s3://prove-backups"
COMPOSE_FILE="docker-compose.prod.yml"
DUMP_DIR="/tmp/neo4j-backup"

if [ -z "${1:-}" ]; then
    echo "Available backups:"
    aws --endpoint-url "$S3_ENDPOINT" s3 ls "$S3_BUCKET/neo4j/"
    echo ""
    echo "Usage: bash scripts/db-restore.sh <tag>"
    echo "  e.g. bash scripts/db-restore.sh 2026-03-22-013000"
    exit 0
fi

TAG="$1"
DUMP_FILE="$DUMP_DIR/$TAG.dump"
mkdir -p "$DUMP_DIR"

echo "==> Downloading $S3_BUCKET/neo4j/$TAG.dump..."
aws --endpoint-url "$S3_ENDPOINT" s3 cp "$S3_BUCKET/neo4j/$TAG.dump" "$DUMP_FILE"

echo "==> Stopping app and neo4j..."
docker compose -f "$COMPOSE_FILE" stop app neo4j

echo "==> Loading dump into Neo4j..."
cp "$DUMP_FILE" "$DUMP_DIR/neo4j.dump"
docker compose -f "$COMPOSE_FILE" run --rm -v "$DUMP_DIR:/dumps" neo4j \
    neo4j-admin database load neo4j --from-path=/dumps --overwrite-destination

echo "==> Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "==> Cleaning up..."
rm -f "$DUMP_FILE"

echo "==> Done. Restored from $TAG."
