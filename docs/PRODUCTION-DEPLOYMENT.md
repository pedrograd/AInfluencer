# Production Deployment Guide

This guide provides step-by-step instructions for deploying AInfluencer to production.

## Quick Start

### Linux/Unix Deployment

```bash
# Clone repository
git clone <repository-url> /opt/AInfluencer
cd /opt/AInfluencer

# Run deployment script
sudo bash scripts/deploy/production.sh
```

### Docker Deployment

```bash
# Copy production environment file
cp .env.example .env.production

# Edit .env.production with your production values
nano .env.production

# Deploy with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Prerequisites

### Hardware Requirements

- **CPU**: 8+ cores (Intel/AMD)
- **RAM**: 32GB+
- **Storage**: 1TB+ NVMe SSD
- **GPU**: NVIDIA GPU with 24GB+ VRAM (RTX 3090, A6000, etc.)
- **Network**: High-speed internet (100+ Mbps)

### Software Requirements

- **OS**: Ubuntu 22.04 LTS or 24.04 LTS (recommended)
- **Python**: 3.11+
- **Node.js**: 20+ LTS
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Docker**: 24+ (optional)
- **Nginx**: Latest stable (for reverse proxy)

## Deployment Methods

### Method 1: Automated Script Deployment (Linux/Unix)

The automated deployment script handles:
- Directory setup
- Service user creation
- Backend and frontend setup
- Systemd service configuration
- Nginx reverse proxy setup
- SSL certificate setup (with Certbot)

**Usage:**

```bash
# Set environment variables (optional)
export DEPLOY_DIR=/opt/AInfluencer
export SERVICE_USER=ainfluencer
export DOMAIN=your-domain.com

# Run deployment script
sudo bash scripts/deploy/production.sh
```

**After deployment:**

1. Edit backend environment file:
   ```bash
   nano /opt/AInfluencer/backend/.env
   ```

2. Edit frontend environment file:
   ```bash
   nano /opt/AInfluencer/frontend/.env.local
   ```

3. Set up SSL (if domain is configured):
   ```bash
   certbot --nginx -d your-domain.com
   ```

4. Check service status:
   ```bash
   systemctl status ainfluencer-backend
   pm2 status
   systemctl status nginx
   ```

### Method 2: Docker Deployment

**Step 1: Prepare environment file**

```bash
cp .env.example .env.production
```

Edit `.env.production` with your production values:
- Database credentials
- Redis password
- API secret keys
- JWT secret keys
- ComfyUI URL
- Storage paths

**Step 2: Deploy**

```bash
# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f

# Check service status
docker-compose ps
```

**Step 3: Set up reverse proxy**

Configure Nginx or another reverse proxy to route traffic to:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

### Method 3: Manual Deployment

See `docs/15-DEPLOYMENT-DEVOPS.md` for detailed manual deployment instructions.

## Configuration

### Backend Environment Variables

Required variables in `backend/.env`:

```bash
# Database
AINFLUENCER_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ainfluencer

# Redis
AINFLUENCER_REDIS_URL=redis://localhost:6379/0

# API
AINFLUENCER_API_SECRET_KEY=<generate-secure-random-key>
AINFLUENCER_DEBUG=False

# JWT
AINFLUENCER_JWT_SECRET_KEY=<generate-secure-random-key>
AINFLUENCER_JWT_ALGORITHM=HS256
AINFLUENCER_JWT_EXPIRATION_HOURS=24

# ComfyUI
AINFLUENCER_COMFYUI_BASE_URL=http://localhost:8188

# Storage
AINFLUENCER_STORAGE_TYPE=local
AINFLUENCER_STORAGE_PATH=/storage/content
```

### Frontend Environment Variables

Required variables in `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Generating Secure Keys

```bash
# Generate API secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Service Management

### Systemd Services (Linux)

**Backend service:**

```bash
# Start
sudo systemctl start ainfluencer-backend

# Stop
sudo systemctl stop ainfluencer-backend

# Restart
sudo systemctl restart ainfluencer-backend

# Status
sudo systemctl status ainfluencer-backend

# Logs
sudo journalctl -u ainfluencer-backend -f
```

**Frontend service (PM2):**

```bash
# Start
pm2 start ecosystem.config.js

# Stop
pm2 stop ainfluencer-frontend

# Restart
pm2 restart ainfluencer-frontend

# Status
pm2 status

# Logs
pm2 logs ainfluencer-frontend
```

### Docker Services

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Restart a service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart backend

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already configured by Certbot)
sudo certbot renew --dry-run
```

### Manual SSL Certificate

1. Obtain SSL certificate from your provider
2. Place certificates in `/etc/letsencrypt/live/your-domain.com/`
3. Update Nginx configuration with certificate paths
4. Reload Nginx: `sudo systemctl reload nginx`

## Monitoring and Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:3000

# Service status
systemctl status ainfluencer-backend
pm2 status
```

### Logs

**Backend logs:**
```bash
sudo journalctl -u ainfluencer-backend -f
```

**Frontend logs:**
```bash
pm2 logs ainfluencer-frontend
```

**Nginx logs:**
```bash
tail -f /var/log/nginx/ainfluencer-access.log
tail -f /var/log/nginx/ainfluencer-error.log
```

### Database Backups

```bash
# Create backup
pg_dump -U ainfluencer_user -d ainfluencer > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U ainfluencer_user -d ainfluencer < backup_20231215.sql
```

### Updates

```bash
# Pull latest changes
cd /opt/AInfluencer
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart ainfluencer-backend

# Update frontend
cd ../frontend
npm ci
npm run build
pm2 restart ainfluencer-frontend
```

## Troubleshooting

### Service Won't Start

1. Check service logs:
   ```bash
   sudo journalctl -u ainfluencer-backend -n 50
   ```

2. Verify environment variables:
   ```bash
   cat /opt/AInfluencer/backend/.env
   ```

3. Check database connection:
   ```bash
   psql -U ainfluencer_user -d ainfluencer -c "SELECT 1;"
   ```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill process (if needed)
sudo kill -9 <PID>
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R ainfluencer:ainfluencer /opt/AInfluencer
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure API and JWT secret keys
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall (only allow necessary ports)
- [ ] Set up regular database backups
- [ ] Enable systemd service security settings
- [ ] Review and restrict file permissions
- [ ] Set up monitoring and alerting
- [ ] Keep system and dependencies updated

## Support

For issues or questions:
1. Check logs for error messages
2. Review `docs/15-DEPLOYMENT-DEVOPS.md` for detailed information
3. Check service status and health endpoints
4. Review troubleshooting section above

