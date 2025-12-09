# Production Deployment Guide
## Complete Production Setup and Deployment

**Version:** 1.0  
**Date:** January 2025  
**Last Updated:** January 2025  
**Status:** Production Ready  
**Document Owner:** DevOps Team

---

## 📋 Document Metadata

### Purpose
Complete guide to production deployment including server setup, GPU optimization, database configuration, security hardening, monitoring, backups, scaling, performance tuning, and disaster recovery.

### Reading Order
**Read After:** [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md), [25-AUTOMATION-WORKFLOWS.md](./25-AUTOMATION-WORKFLOWS.md)  
**Read Before:** [30-TROUBLESHOOTING-COMPLETE.md](./30-TROUBLESHOOTING-COMPLETE.md), [31-BEST-PRACTICES-COMPLETE.md](./31-BEST-PRACTICES-COMPLETE.md)

### Related Documents
- [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md) - Architecture
- [18-AI-TOOLS-NVIDIA-SETUP.md](./18-AI-TOOLS-NVIDIA-SETUP.md) - GPU setup

---

## Table of Contents

1. [Introduction to Production Deployment](#introduction)
2. [Server Setup and Configuration](#server-setup)
3. [GPU Optimization](#gpu-optimization)
4. [Database Setup and Optimization](#database)
5. [Security Hardening](#security)
6. [Monitoring and Logging](#monitoring)
7. [Backup Strategies](#backups)
8. [Scaling Strategies](#scaling)
9. [Performance Tuning](#performance)
10. [Disaster Recovery](#disaster-recovery)
11. [Maintenance Procedures](#maintenance)

---

## Introduction to Production Deployment {#introduction}

Production deployment requires careful planning, configuration, and ongoing maintenance. This guide covers all aspects of deploying the AInfluencer platform to production.

### Deployment Goals

1. **Reliability:** 99.9% uptime
2. **Performance:** Fast response times
3. **Security:** Secure and hardened
4. **Scalability:** Handle growth
5. **Maintainability:** Easy to maintain

### Deployment Architecture

```
Load Balancer
    ↓
Application Servers (Multiple)
    ↓
GPU Servers (AI Generation)
    ↓
Database (Primary + Replica)
    ↓
Storage (Object Storage)
    ↓
Monitoring & Logging
```

---

## Server Setup and Configuration {#server-setup}

### Server Requirements

**Application Server:**
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- OS: Ubuntu 22.04 LTS

**GPU Server:**
- GPU: NVIDIA RTX 4090 or A6000
- VRAM: 24GB+
- CPU: 16+ cores
- RAM: 64GB+
- Storage: 2TB+ NVMe SSD

### Initial Setup

**1. Update System:**
```bash
sudo apt update
sudo apt upgrade -y
```

**2. Install Essential Tools:**
```bash
sudo apt install -y git curl wget vim htop
```

**3. Create Application User:**
```bash
sudo useradd -m -s /bin/bash appuser
sudo usermod -aG sudo appuser
```

**4. Setup SSH Keys:**
```bash
# On local machine
ssh-copy-id appuser@server_ip
```

### Docker Setup

**Install Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker appuser
```

**Install Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## GPU Optimization {#gpu-optimization}

### NVIDIA Driver Setup

**Install Drivers:**
```bash
sudo ubuntu-drivers autoinstall
sudo reboot
```

**Verify Installation:**
```bash
nvidia-smi
```

### CUDA Setup

**Install CUDA:**
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-1
```

### GPU Memory Management

**Monitor GPU:**
```bash
watch -n 1 nvidia-smi
```

**Optimize Memory:**
```python
import torch

# Set memory fraction
torch.cuda.set_per_process_memory_fraction(0.9)

# Clear cache
torch.cuda.empty_cache()
```

### Multi-GPU Setup

**Use Multiple GPUs:**
```python
import torch

if torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)
```

---

## Database Setup and Optimization {#database}

### PostgreSQL Setup

**Install PostgreSQL:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Create Database:**
```bash
sudo -u postgres psql
CREATE DATABASE ainfluencer;
CREATE USER appuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ainfluencer TO appuser;
```

### Database Optimization

**Configuration (`/etc/postgresql/14/main/postgresql.conf`):**
```
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 64MB
min_wal_size = 1GB
max_wal_size = 4GB
```

**Indexes:**
```sql
CREATE INDEX idx_character_id ON content(character_id);
CREATE INDEX idx_created_at ON content(created_at);
CREATE INDEX idx_status ON content(status);
```

### Database Backups

**Automated Backups:**
```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U appuser ainfluencer > /backups/db_$DATE.sql
```

**Cron Job:**
```bash
0 2 * * * /path/to/backup_db.sh
```

---

## Security Hardening {#security}

### Firewall Setup

**UFW Configuration:**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSH Hardening

**SSH Configuration (`/etc/ssh/sshd_config`):**
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Change default port
```

**Restart SSH:**
```bash
sudo systemctl restart sshd
```

### Application Security

**Environment Variables:**
```bash
# Use .env file (never commit)
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://..."
export API_KEYS="..."
```

**Secrets Management:**
- Use environment variables
- Use secret management services
- Never commit secrets
- Rotate regularly

### SSL/TLS Setup

**Let's Encrypt:**
```bash
sudo apt install certbot
sudo certbot --nginx -d yourdomain.com
```

---

## Monitoring and Logging {#monitoring}

### Application Monitoring

**Prometheus Setup:**
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

**Grafana Setup:**
```yaml
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Logging

**Centralized Logging:**
```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('ainfluencer')
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
logger.addHandler(handler)
```

**Log Rotation:**
```bash
# /etc/logrotate.d/ainfluencer
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### Alerting

**Alert Rules:**
```yaml
# prometheus/alerts.yml
groups:
  - name: ainfluencer
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
```

---

## Backup Strategies {#backups}

### Backup Types

**Database Backups:**
- Daily full backups
- Hourly incremental
- Retention: 30 days

**File Backups:**
- Generated content
- Character data
- Configuration files

**System Backups:**
- Full system snapshots
- Weekly backups
- Retention: 90 days

### Backup Implementation

**Automated Backup Script:**
```bash
#!/bin/bash
# full_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/$DATE"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U appuser ainfluencer > $BACKUP_DIR/db.sql

# File backup
tar -czf $BACKUP_DIR/files.tar.gz /app/data

# Upload to S3
aws s3 cp $BACKUP_DIR s3://backups/ --recursive

# Cleanup old backups
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

### Backup Testing

**Regular Testing:**
- Test restore monthly
- Verify backup integrity
- Document restore procedures

---

## Scaling Strategies {#scaling}

### Horizontal Scaling

**Load Balancer:**
```nginx
upstream app_servers {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    location / {
        proxy_pass http://app_servers;
    }
}
```

### Vertical Scaling

**Resource Upgrades:**
- Increase CPU/RAM
- Upgrade GPU
- Add storage
- Optimize configuration

### Auto-Scaling

**Kubernetes HPA:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ainfluencer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ainfluencer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Performance Tuning {#performance}

### Application Optimization

**Caching:**
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379)

@lru_cache(maxsize=100)
def cached_operation(key):
    return expensive_operation(key)
```

**Database Optimization:**
- Use connection pooling
- Optimize queries
- Add indexes
- Use read replicas

### GPU Optimization

**Batch Processing:**
```python
# Process multiple items together
batch = [item1, item2, item3]
results = model.process_batch(batch)
```

**Memory Management:**
```python
# Clear cache regularly
torch.cuda.empty_cache()

# Use mixed precision
from torch.cuda.amp import autocast
with autocast():
    output = model(input)
```

---

## Disaster Recovery {#disaster-recovery}

### Recovery Plan

**RTO (Recovery Time Objective):** 4 hours  
**RPO (Recovery Point Objective):** 1 hour

### Recovery Procedures

**1. Database Recovery:**
```bash
# Restore from backup
psql -U appuser ainfluencer < backup.sql
```

**2. Application Recovery:**
```bash
# Redeploy application
git pull
docker-compose up -d
```

**3. Full System Recovery:**
```bash
# Restore from snapshot
# Reconfigure services
# Verify functionality
```

### Testing

**Regular DR Tests:**
- Monthly recovery tests
- Document procedures
- Update plans

---

## Maintenance Procedures {#maintenance}

### Regular Maintenance

**Weekly:**
- Review logs
- Check disk space
- Verify backups
- Update dependencies

**Monthly:**
- Security updates
- Performance review
- Capacity planning
- DR testing

**Quarterly:**
- Full system review
- Architecture review
- Optimization
- Documentation update

### Update Procedures

**Application Updates:**
```bash
# 1. Backup
./backup.sh

# 2. Pull updates
git pull

# 3. Update dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Restart services
docker-compose restart
```

---

## Conclusion

Production deployment requires careful planning and ongoing maintenance. By following this guide, you can deploy and maintain a reliable, scalable, and secure production system.

**Key Takeaways:**
1. Plan deployment carefully
2. Implement security measures
3. Set up monitoring and logging
4. Create backup strategies
5. Plan for scaling and disaster recovery

**Next Steps:**
- Review [30-TROUBLESHOOTING-COMPLETE.md](./30-TROUBLESHOOTING-COMPLETE.md) for troubleshooting
- Review [31-BEST-PRACTICES-COMPLETE.md](./31-BEST-PRACTICES-COMPLETE.md) for best practices
- Deploy to staging first
- Test thoroughly before production

---

**Document Status:** ✅ Complete  
**Last Updated:** January 2025  
**Version:** 1.0
