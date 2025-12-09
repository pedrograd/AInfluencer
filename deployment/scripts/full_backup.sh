#!/bin/bash
# Full System Backup Script
# Backs up database, files, and configuration

set -e

# Configuration
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/$DATE"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Directories to backup
APP_DATA_DIR="${APP_DATA_DIR:-/app/data}"
MEDIA_DIR="${MEDIA_DIR:-/app/media_library}"
CHARACTERS_DIR="${CHARACTERS_DIR:-/app/characters}"
CONFIG_DIR="${CONFIG_DIR:-/app/deployment}"

echo "Starting full system backup..."
echo "Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "Backing up database..."
./backup_db.sh "$BACKUP_DIR" || echo "Database backup failed, continuing..."

# File backup
echo "Backing up application files..."
if [ -d "$APP_DATA_DIR" ]; then
    tar -czf "$BACKUP_DIR/files.tar.gz" \
        -C "$(dirname "$APP_DATA_DIR")" \
        "$(basename "$APP_DATA_DIR")" \
        "$(basename "$MEDIA_DIR")" \
        "$(basename "$CHARACTERS_DIR")" \
        2>/dev/null || echo "File backup failed, continuing..."
fi

# Configuration backup
echo "Backing up configuration..."
if [ -d "$CONFIG_DIR" ]; then
    tar -czf "$BACKUP_DIR/config.tar.gz" \
        -C "$(dirname "$CONFIG_DIR")" \
        "$(basename "$CONFIG_DIR")" \
        2>/dev/null || echo "Config backup failed, continuing..."
fi

# Create backup manifest
cat > "$BACKUP_DIR/manifest.json" <<EOF
{
    "backup_date": "$DATE",
    "backup_type": "full",
    "database_backup": "$(ls -1 $BACKUP_DIR/db_*.sql.gz 2>/dev/null | head -1 || echo 'none')",
    "files_backup": "$(ls -1 $BACKUP_DIR/files.tar.gz 2>/dev/null | head -1 || echo 'none')",
    "config_backup": "$(ls -1 $BACKUP_DIR/config.tar.gz 2>/dev/null | head -1 || echo 'none')"
}
EOF

# Upload to S3 if configured
if [ -n "$AWS_S3_BACKUP_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR" "s3://$AWS_S3_BACKUP_BUCKET/full/$DATE/" --recursive || echo "S3 upload failed, but local backup succeeded"
fi

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find /backups -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

echo "Full backup completed: $BACKUP_DIR"
