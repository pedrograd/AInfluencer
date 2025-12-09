#!/bin/bash
# Application Update Script
# Safely updates the application in production

set -e

echo "=========================================="
echo "APPLICATION UPDATE PROCEDURE"
echo "=========================================="

# Step 1: Backup
echo "Step 1: Creating backup..."
./deployment/scripts/full_backup.sh

# Step 2: Pull updates
echo "Step 2: Pulling code updates..."
git fetch origin
git pull origin main || {
    echo "Error: Failed to pull updates"
    exit 1
}

# Step 3: Update dependencies
echo "Step 3: Updating dependencies..."

# Backend dependencies
if [ -f "backend/requirements.txt" ]; then
    cd backend
    pip install -r requirements.txt --upgrade
    cd ..
fi

# Web dependencies
if [ -f "web/package.json" ]; then
    cd web
    npm install
    npm run build
    cd ..
fi

# Step 4: Run database migrations
echo "Step 4: Running database migrations..."
# Add migration commands here
# python backend/manage.py migrate
# or
# alembic upgrade head

# Step 5: Restart services
echo "Step 5: Restarting services..."

# Docker Compose
if command -v docker-compose &> /dev/null; then
    docker-compose build
    docker-compose up -d
    docker-compose restart
fi

# Systemd (alternative)
if systemctl is-active --quiet ainfluencer; then
    systemctl restart ainfluencer
fi

# Step 6: Health check
echo "Step 6: Performing health check..."
sleep 10

# Check backend
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✓ Backend is healthy"
else
    echo "✗ Backend health check failed"
    echo "Rolling back..."
    ./deployment/scripts/rollback.sh
    exit 1
fi

# Check web
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Web is healthy"
else
    echo "✗ Web health check failed"
    echo "Rolling back..."
    ./deployment/scripts/rollback.sh
    exit 1
fi

echo ""
echo "=========================================="
echo "Update completed successfully"
echo "=========================================="
