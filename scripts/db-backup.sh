#!/usr/bin/env bash
# Back up Neo4j database to Hetzner Object Storage.
# Usage: bash scripts/db-backup.sh [tag]
# Tag defaults to ISO timestamp. Stored as: s3://prove-backups/neo4j/YYYY-MM-DD-HHMMSS.dump

set -euo pipefail

S3_ENDPOINT="https://hel1.your-objectstorage.com"
S3_BUCKET="s3://prove-backups"
COMPOSE_FILE="docker-compose.prod.yml"
DUMP_DIR="/tmp/neo4j-backup"
TAG="${1:-$(date -u +%Y-%m-%d-%H%M%S)}"
DUMP_FILE="$DUMP_DIR/$TAG.dump"

mkdir -p "$DUMP_DIR"

echo "==> Stopping app to ensure clean dump..."
docker compose -f "$COMPOSE_FILE" stop app

echo "==> Stopping neo4j for clean dump..."
docker compose -f "$COMPOSE_FILE" stop neo4j

echo "==> Dumping Neo4j database..."
chmod 777 "$DUMP_DIR"
docker compose -f "$COMPOSE_FILE" run --rm --user "$(id -u):$(id -g)" -v "$DUMP_DIR:/dumps" neo4j \
    neo4j-admin database dump neo4j --to-path=/dumps --overwrite-destination

echo "==> Moving dump file..."
mv "$DUMP_DIR/neo4j.dump" "$DUMP_FILE"

echo "==> Restarting services..."
docker compose -f "$COMPOSE_FILE" up -d

SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo "==> Uploading $DUMP_FILE ($SIZE) to $S3_BUCKET/neo4j/$TAG.dump..."
aws --endpoint-url "$S3_ENDPOINT" s3 cp "$DUMP_FILE" "$S3_BUCKET/neo4j/$TAG.dump"

echo "==> Cleaning up local dump..."
rm -f "$DUMP_FILE"

echo "==> Done. Backup: $S3_BUCKET/neo4j/$TAG.dump"

# List recent backups
echo ""
echo "Recent backups:"
aws --endpoint-url "$S3_ENDPOINT" s3 ls "$S3_BUCKET/neo4j/" | tail -5
