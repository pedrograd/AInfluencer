#!/bin/bash
# Database Backup Script
# Usage: ./backup_db.sh [backup_directory]

set -e

# Configuration
BACKUP_DIR="${1:-/backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Database configuration from environment
DB_NAME="${POSTGRES_DB:-ainfluencer}"
DB_USER="${POSTGRES_USER:-appuser}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"

# Perform backup
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    --verbose \
    --format=custom \
    --file="$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3 if configured
if [ -n "$AWS_S3_BACKUP_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BACKUP_BUCKET/database/" || echo "S3 upload failed, but local backup succeeded"
fi

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "db_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup process completed successfully"
