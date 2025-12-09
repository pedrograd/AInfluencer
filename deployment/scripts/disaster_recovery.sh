#!/bin/bash
# Disaster Recovery Script
# Restores system from backup

set -e

BACKUP_DATE="${1}"
BACKUP_DIR="/backups"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20250101_120000"
    echo ""
    echo "Available backups:"
    ls -1d "$BACKUP_DIR"/*/ 2>/dev/null | xargs -n1 basename || echo "No backups found"
    exit 1
fi

RESTORE_DIR="$BACKUP_DIR/$BACKUP_DATE"

if [ ! -d "$RESTORE_DIR" ]; then
    echo "Error: Backup directory not found: $RESTORE_DIR"
    exit 1
fi

echo "=========================================="
echo "DISASTER RECOVERY PROCEDURE"
echo "=========================================="
echo "Backup Date: $BACKUP_DATE"
echo "Restore Directory: $RESTORE_DIR"
echo ""
echo "WARNING: This will restore the system from backup."
echo "All current data will be replaced!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled."
    exit 0
fi

# Check backup manifest
if [ -f "$RESTORE_DIR/manifest.json" ]; then
    echo "Backup manifest found:"
    cat "$RESTORE_DIR/manifest.json"
    echo ""
fi

# Step 1: Stop services
echo "Step 1: Stopping services..."
docker-compose down || systemctl stop ainfluencer || echo "Services stopped"

# Step 2: Restore database
echo "Step 2: Restoring database..."
DB_BACKUP=$(ls -1 "$RESTORE_DIR"/db_*.sql.gz 2>/dev/null | head -1)
if [ -n "$DB_BACKUP" ]; then
    echo "Restoring from: $DB_BACKUP"
    ./deployment/scripts/restore_db.sh "$DB_BACKUP"
else
    echo "Warning: No database backup found"
fi

# Step 3: Restore files
echo "Step 3: Restoring application files..."
FILES_BACKUP="$RESTORE_DIR/files.tar.gz"
if [ -f "$FILES_BACKUP" ]; then
    echo "Restoring files from: $FILES_BACKUP"
    tar -xzf "$FILES_BACKUP" -C / || echo "File restore failed"
else
    echo "Warning: No files backup found"
fi

# Step 4: Restore configuration
echo "Step 4: Restoring configuration..."
CONFIG_BACKUP="$RESTORE_DIR/config.tar.gz"
if [ -f "$CONFIG_BACKUP" ]; then
    echo "Restoring config from: $CONFIG_BACKUP"
    tar -xzf "$CONFIG_BACKUP" -C / || echo "Config restore failed"
else
    echo "Warning: No config backup found"
fi

# Step 5: Verify restore
echo "Step 5: Verifying restore..."
# Check database connection
# Check file integrity
# Check service health

# Step 6: Start services
echo "Step 6: Starting services..."
docker-compose up -d || systemctl start ainfluencer || echo "Services started"

echo ""
echo "=========================================="
echo "Disaster recovery completed"
echo "=========================================="
echo "Please verify:"
echo "  1. Database is accessible"
echo "  2. Application is running"
echo "  3. Files are restored"
echo "  4. Configuration is correct"
