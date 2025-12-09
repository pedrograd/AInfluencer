#!/bin/bash
# Production Startup Script
# Starts all production services with proper checks

set -e

echo "=========================================="
echo "AInfluencer Production Startup"
echo "=========================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy deployment/env.example to .env and configure it"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Create necessary directories
echo "Creating directories..."
mkdir -p logs backups media_library characters

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Build images
echo "Building Docker images..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Health checks
echo "Performing health checks..."

# Check backend
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✓ Backend is healthy"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "Waiting for backend... ($RETRY/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "✗ Backend health check failed"
    echo "Check logs: docker-compose logs backend"
    exit 1
fi

# Check web
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✓ Web is healthy"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "Waiting for web... ($RETRY/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "✗ Web health check failed"
    echo "Check logs: docker-compose logs web"
    exit 1
fi

# Check database
if docker-compose exec -T postgres pg_isready -U "${POSTGRES_USER:-appuser}" > /dev/null 2>&1; then
    echo "✓ Database is healthy"
else
    echo "✗ Database health check failed"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is healthy"
else
    echo "✗ Redis health check failed"
fi

echo ""
echo "=========================================="
echo "Production startup completed successfully"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Web Frontend: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
