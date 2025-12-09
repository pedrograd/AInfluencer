# Production Deployment Guide

This directory contains all production deployment configurations, scripts, and documentation.

## Directory Structure

```
deployment/
├── scripts/           # Deployment and maintenance scripts
├── kubernetes/        # Kubernetes configurations
├── nginx.conf         # Nginx main configuration
├── nginx-site.conf    # Nginx site configuration
├── postgresql.conf    # PostgreSQL optimization config
├── prometheus.yml     # Prometheus configuration
├── alerts.yml         # Prometheus alert rules
└── env.example        # Environment variables template
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp deployment/env.example .env

# Edit .env with your production values
nano .env
```

### 2. Build and Start Services

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Setup SSL (Let's Encrypt)

```bash
# Run SSL setup script
./deployment/scripts/setup_ssl.sh yourdomain.com
```

### 4. Setup Firewall

```bash
# Configure firewall
sudo ./deployment/scripts/setup_firewall.sh
```

### 5. Setup Automated Backups

```bash
# Setup backup cron jobs
./deployment/scripts/setup_backup_cron.sh
```

## Scripts

### Backup Scripts

- `backup_db.sh` - Database backup
- `full_backup.sh` - Full system backup
- `restore_db.sh` - Database restore
- `setup_backup_cron.sh` - Setup automated backups

### Security Scripts

- `setup_firewall.sh` - Configure UFW firewall
- `harden_ssh.sh` - Harden SSH configuration
- `setup_ssl.sh` - Setup SSL/TLS certificates

### Maintenance Scripts

- `update_application.sh` - Update application safely
- `rollback.sh` - Rollback to previous version
- `maintenance_check.sh` - Perform maintenance checks
- `disaster_recovery.sh` - Disaster recovery procedure

## Monitoring

### Prometheus

- Access: http://localhost:9090
- Configuration: `deployment/prometheus.yml`
- Alerts: `deployment/alerts.yml`

### Grafana

- Access: http://localhost:3001
- Default credentials: admin / (from .env GRAFANA_PASSWORD)

## Scaling

### Docker Compose

Use production override:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes

Apply Kubernetes configurations:

```bash
kubectl apply -f deployment/kubernetes/
```

## Backup and Recovery

### Manual Backup

```bash
# Database only
./deployment/scripts/backup_db.sh

# Full backup
./deployment/scripts/full_backup.sh
```

### Restore

```bash
# Restore database
./deployment/scripts/restore_db.sh /backups/db_20250101_120000.sql.gz

# Disaster recovery
./deployment/scripts/disaster_recovery.sh 20250101_120000
```

## Maintenance

### Regular Maintenance

```bash
# Run maintenance checks
./deployment/scripts/maintenance_check.sh

# Update application
./deployment/scripts/update_application.sh
```

### Health Checks

- Backend: http://localhost:8000/api/health
- Web: http://localhost:3000
- Metrics: http://localhost:8000/metrics

## Troubleshooting

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f web
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Security Checklist

- [ ] Change all default passwords in .env
- [ ] Setup SSL/TLS certificates
- [ ] Configure firewall
- [ ] Harden SSH
- [ ] Enable automated backups
- [ ] Setup monitoring and alerts
- [ ] Review and restrict access
- [ ] Enable log rotation
- [ ] Setup disaster recovery plan

## Performance Tuning

### Database

- Connection pooling configured
- Indexes created automatically
- Query optimization enabled

### Caching

- Redis caching enabled
- Cache TTL configured
- Cache invalidation strategies

### GPU

- Memory fraction: 0.9
- Batch processing enabled
- Mixed precision support

## Support

For issues or questions, refer to:
- [Troubleshooting Guide](../docs/30-TROUBLESHOOTING-COMPLETE.md)
- [Best Practices](../docs/31-BEST-PRACTICES-COMPLETE.md)
