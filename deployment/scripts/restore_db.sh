#!/bin/bash
# Database Restore Script
# Usage: ./restore_db.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /backups/db_20250101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Database configuration
DB_NAME="${POSTGRES_DB:-ainfluencer}"
DB_USER="${POSTGRES_USER:-appuser}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "WARNING: This will restore the database from backup."
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Decompress if needed
TEMP_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.gz ]]; then
    TEMP_FILE="${BACKUP_FILE%.gz}"
    echo "Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
fi

# Restore database
echo "Restoring database..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    "$TEMP_FILE" || {
    # If pg_restore fails, try pg_dump format
    echo "Trying SQL format restore..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$TEMP_FILE"
}

# Cleanup temp file if we created it
if [ "$TEMP_FILE" != "$BACKUP_FILE" ]; then
    rm -f "$TEMP_FILE"
fi

echo "Database restore completed successfully"
