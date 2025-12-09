#!/bin/bash
# Maintenance Check Script
# Performs regular maintenance checks

set -e

echo "=========================================="
echo "MAINTENANCE CHECK"
echo "Date: $(date)"
echo "=========================================="

# Check disk space
echo ""
echo "1. Disk Space:"
df -h | grep -E '^/dev|Filesystem' || df -h

# Check memory
echo ""
echo "2. Memory Usage:"
free -h

# Check services
echo ""
echo "3. Service Status:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
elif systemctl is-active --quiet ainfluencer; then
    systemctl status ainfluencer --no-pager
else
    echo "Services not found"
fi

# Check database
echo ""
echo "4. Database Status:"
if command -v psql &> /dev/null; then
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST:-localhost}" \
        -U "${POSTGRES_USER:-appuser}" \
        -d "${POSTGRES_DB:-ainfluencer}" \
        -c "SELECT version();" 2>/dev/null && echo "✓ Database connected" || echo "✗ Database connection failed"
else
    echo "PostgreSQL client not found"
fi

# Check Redis
echo ""
echo "5. Redis Status:"
if command -v redis-cli &> /dev/null; then
    redis-cli -h "${REDIS_HOST:-localhost}" ping 2>/dev/null && echo "✓ Redis connected" || echo "✗ Redis connection failed"
else
    echo "Redis client not found"
fi

# Check backups
echo ""
echo "6. Backup Status:"
BACKUP_COUNT=$(ls -1d /backups/*/ 2>/dev/null | wc -l)
echo "Total backups: $BACKUP_COUNT"
if [ "$BACKUP_COUNT" -gt 0 ]; then
    LATEST_BACKUP=$(ls -1td /backups/*/ 2>/dev/null | head -1)
    echo "Latest backup: $(basename "$LATEST_BACKUP")"
    echo "Backup size: $(du -sh "$LATEST_BACKUP" | cut -f1)"
fi

# Check logs
echo ""
echo "7. Recent Errors (last 50 lines):"
if [ -f "logs/app.log" ]; then
    tail -50 logs/app.log | grep -i error || echo "No recent errors"
else
    echo "Log file not found"
fi

# Check application health
echo ""
echo "8. Application Health:"
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✓ Backend API is healthy"
    curl -s http://localhost:8000/api/health | jq '.' || curl -s http://localhost:8000/api/health
else
    echo "✗ Backend API is not responding"
fi

echo ""
echo "=========================================="
echo "Maintenance check completed"
echo "=========================================="
