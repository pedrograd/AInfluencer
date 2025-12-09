#!/bin/bash
# Rollback Script
# Rolls back to previous version after failed update

set -e

echo "=========================================="
echo "ROLLBACK PROCEDURE"
echo "=========================================="

# Get latest backup
LATEST_BACKUP=$(ls -1td /backups/*/ 2>/dev/null | head -1 | xargs basename)

if [ -z "$LATEST_BACKUP" ]; then
    echo "Error: No backup found for rollback"
    exit 1
fi

echo "Rolling back to backup: $LATEST_BACKUP"
echo "This will restore the system to the state before the last update."
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

# Restore from backup
./deployment/scripts/disaster_recovery.sh "$LATEST_BACKUP"

echo "Rollback completed"
