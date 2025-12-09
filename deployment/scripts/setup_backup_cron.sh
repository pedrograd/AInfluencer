#!/bin/bash
# Setup Automated Backup Cron Jobs
# This script sets up daily database backups and weekly full backups

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

echo "Setting up automated backup cron jobs..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Make scripts executable
chmod +x "$SCRIPT_DIR/backup_db.sh"
chmod +x "$SCRIPT_DIR/full_backup.sh"

# Daily database backup (2 AM)
(crontab -l 2>/dev/null | grep -v "backup_db.sh" || true; echo "0 2 * * * $SCRIPT_DIR/backup_db.sh $BACKUP_DIR >> $BACKUP_DIR/backup.log 2>&1") | crontab -

# Weekly full backup (Sunday 3 AM)
(crontab -l 2>/dev/null | grep -v "full_backup.sh" || true; echo "0 3 * * 0 $SCRIPT_DIR/full_backup.sh >> $BACKUP_DIR/backup.log 2>&1") | crontab -

echo "Backup cron jobs configured:"
echo "  - Daily database backup: 2:00 AM"
echo "  - Weekly full backup: Sunday 3:00 AM"
echo ""
echo "Backup logs: $BACKUP_DIR/backup.log"
crontab -l | grep backup
