# Deployment & DevOps

## Deployment Strategy

### Deployment Model
**Self-Hosted (Primary)**
- **Why**: Privacy, control, no vendor lock-in, free
- **Target**: Single server (can scale to multiple)
- **Hardware**: User's own hardware (local GPU required)

### Alternative: Cloud Deployment (Future)
- **Option**: Docker containers on cloud providers
- **Providers**: AWS, GCP, Azure, DigitalOcean, Hetzner
- **Consideration**: GPU instances are expensive

---

## Infrastructure Requirements

### Hardware Requirements

#### Minimum (Development)
- **CPU**: 4+ cores
- **RAM**: 16GB
- **Storage**: 500GB SSD
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **Network**: Stable internet connection

#### Recommended (Production)
- **CPU**: 8+ cores (Intel/AMD)
- **RAM**: 32GB+
- **Storage**: 1TB+ NVMe SSD
- **GPU**: NVIDIA GPU with 24GB+ VRAM (RTX 3090, A6000, etc.)
- **Network**: High-speed internet (100+ Mbps)

#### Optimal (Scale)
- **CPU**: 16+ cores
- **RAM**: 64GB+
- **Storage**: 2TB+ NVMe SSD (or multiple drives)
- **GPU**: Multiple GPUs or A100/H100
- **Network**: Gigabit internet

---

### Software Requirements

#### Operating System
- **Primary**: Ubuntu 22.04 LTS or 24.04 LTS
- **Alternatives**: Debian 12+, CentOS Stream 9+
- **Why**: Best NVIDIA driver support, stable, widely used

#### Core Software
- **Python**: 3.11+ (via pyenv or system package)
- **Node.js**: 20+ LTS (via nvm or system package)
- **PostgreSQL**: 15+ (via apt or Docker)
- **Redis**: 7+ (via apt or Docker)
- **Docker**: 24+ (optional, for containerization)
- **Docker Compose**: 2.20+ (optional)

#### NVIDIA Software
- **NVIDIA Drivers**: Latest stable (535+)
- **CUDA**: 12.0+ (for GPU acceleration)
- **cuDNN**: 8.9+ (for deep learning)
- **PyTorch**: 2.1+ (with CUDA support)

#### AI/ML Software
- **Stable Diffusion**: Automatic1111 WebUI or ComfyUI
- **Ollama**: Latest version (for LLM)
- **Coqui TTS**: Latest version (for voice)

---

## Deployment Architecture

### Single Server Architecture
```
┌─────────────────────────────────────────┐
│         Ubuntu Server                   │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Frontend (Next.js)              │  │
│  │  Port: 3000                      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Backend API (FastAPI)            │  │
│  │  Port: 8000                       │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  PostgreSQL                       │  │
│  │  Port: 5432                       │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Redis                            │  │
│  │  Port: 6379                       │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Celery Workers                  │  │
│  │  (Content Generation, Automation)│  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Stable Diffusion (Automatic1111)│  │
│  │  Port: 7860                      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Ollama (LLM Server)              │  │
│  │  Port: 11434                      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Storage (Local Filesystem)       │  │
│  │  /storage/content/                │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  NVIDIA GPU                       │  │
│  │  (Shared by all services)         │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Installation Steps

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    nvidia-driver-535 \
    nvidia-cuda-toolkit \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-15 \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx
```

### Step 2: Install NVIDIA Drivers & CUDA

```bash
# Verify GPU detection
nvidia-smi

# Install CUDA (if not already installed)
# Follow NVIDIA's official installation guide for your GPU
```

### Step 3: Install Node.js

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

### Step 4: Set Up PostgreSQL

```bash
# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE ainfluencer;
CREATE USER ainfluencer_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ainfluencer TO ainfluencer_user;
\q
```

### Step 5: Set Up Redis

```bash
# Redis should be running after installation
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping
# Should return: PONG
```

### Step 6: Install Stable Diffusion

```bash
# Option 1: Automatic1111 WebUI
cd /opt
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui
./webui.sh --api --listen 0.0.0.0 --port 7860

# Option 2: ComfyUI
cd /opt
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py --listen 0.0.0.0 --port 8188
```

### Step 7: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3:8b
ollama pull mistral:7b
ollama pull phi3:mini
```

### Step 8: Clone and Set Up Application

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/AInfluencer.git
cd AInfluencer

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Frontend setup
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
```

### Step 9: Set Up Systemd Services

#### Backend Service
```bash
sudo nano /etc/systemd/system/ainfluencer-backend.service
```

```ini
[Unit]
Description=AInfluencer Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/AInfluencer/backend
Environment="PATH=/opt/AInfluencer/backend/venv/bin"
ExecStart=/opt/AInfluencer/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service
```bash
sudo nano /etc/systemd/system/ainfluencer-worker.service
```

```ini
[Unit]
Description=AInfluencer Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/AInfluencer/backend
Environment="PATH=/opt/AInfluencer/backend/venv/bin"
ExecStart=/opt/AInfluencer/backend/venv/bin/celery -A tasks worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Frontend Service (PM2)
```bash
# Install PM2
npm install -g pm2

# Start frontend
cd /opt/AInfluencer/frontend
pm2 start npm --name "ainfluencer-frontend" -- start
pm2 save
pm2 startup
```

### Step 10: Set Up Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/ainfluencer
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ainfluencer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Set up SSL (Let's Encrypt)
sudo certbot --nginx -d your-domain.com
```

### Step 11: Enable Services

```bash
# Enable and start services
sudo systemctl enable ainfluencer-backend
sudo systemctl enable ainfluencer-worker
sudo systemctl start ainfluencer-backend
sudo systemctl start ainfluencer-worker

# Check status
sudo systemctl status ainfluencer-backend
sudo systemctl status ainfluencer-worker
```

---

## Docker Deployment (Alternative)

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ainfluencer
      POSTGRES_USER: ainfluencer_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://ainfluencer_user:secure_password@postgres:5432/ainfluencer
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - content_storage:/storage

  worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://ainfluencer_user:secure_password@postgres:5432/ainfluencer
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - content_storage:/storage

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

volumes:
  postgres_data:
  redis_data:
  content_storage:
```

**Note**: GPU access in Docker requires `nvidia-docker` or Docker with GPU support.

---

## Environment Configuration

### Backend Environment Variables

```bash
# .env
# Database
DATABASE_URL=postgresql://ainfluencer_user:password@localhost:5432/ainfluencer

# Redis
REDIS_URL=redis://localhost:6379

# API
API_SECRET_KEY=your-secret-key-here
API_DEBUG=False

# Stable Diffusion
STABLE_DIFFUSION_URL=http://localhost:7860
STABLE_DIFFUSION_API_KEY=

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Storage
STORAGE_TYPE=local
STORAGE_PATH=/storage/content

# Security
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Platform APIs (if using official APIs)
INSTAGRAM_API_KEY=
TWITTER_API_KEY=
TWITTER_API_SECRET=
FACEBOOK_ACCESS_TOKEN=
```

### Frontend Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## Monitoring & Logging

### Application Logging

#### Backend Logging
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            '/var/log/ainfluencer/backend.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
```

### System Monitoring

#### Prometheus & Grafana (Optional)
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Install Grafana
sudo apt install -y grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### Health Checks

#### Backend Health Endpoint
```python
# Already defined in API: GET /api/v1/system/health
```

#### Systemd Health Check Script
```bash
#!/bin/bash
# /opt/AInfluencer/scripts/health-check.sh

BACKEND_URL="http://localhost:8000/api/v1/system/health"
response=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL)

if [ $response != "200" ]; then
    echo "Backend health check failed"
    systemctl restart ainfluencer-backend
fi
```

```bash
# Add to crontab (check every 5 minutes)
*/5 * * * * /opt/AInfluencer/scripts/health-check.sh
```

---

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
# /opt/AInfluencer/scripts/backup-db.sh

BACKUP_DIR="/backups/ainfluencer"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

pg_dump -U ainfluencer_user -d ainfluencer > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /opt/AInfluencer/scripts/backup-db.sh
```

### Content Backups

```bash
# Backup content storage
#!/bin/bash
# /opt/AInfluencer/scripts/backup-content.sh

SOURCE="/storage/content"
BACKUP_DIR="/backups/ainfluencer/content"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

rsync -av --delete $SOURCE $BACKUP_DIR/$DATE/
```

---

## Security Hardening

### Firewall Configuration

```bash
# UFW (Uncomplicated Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSH Hardening

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use key-based authentication
# Set: PasswordAuthentication no

sudo systemctl restart sshd
```

### Application Security

- **HTTPS**: Use Let's Encrypt SSL certificates
- **API Keys**: Store securely, never commit to git
- **Database**: Use strong passwords, limit access
- **Updates**: Keep system and dependencies updated

---

## Scaling Considerations

### Vertical Scaling
- **More RAM**: For larger models, more concurrent operations
- **Better GPU**: For faster content generation
- **More Storage**: For more content
- **Better CPU**: For faster processing

### Horizontal Scaling (Future)
- **Multiple Workers**: Scale Celery workers
- **Load Balancer**: Multiple backend instances
- **Database Replication**: Read replicas
- **CDN**: For content delivery

---

## Troubleshooting

### Common Issues

#### GPU Not Detected
```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall drivers if needed
sudo apt install --reinstall nvidia-driver-535
```

#### Out of Memory
```bash
# Check memory usage
free -h

# Check GPU memory
nvidia-smi

# Reduce batch sizes, use model quantization
```

#### Service Won't Start
```bash
# Check logs
sudo journalctl -u ainfluencer-backend -n 50
sudo journalctl -u ainfluencer-worker -n 50

# Check configuration
sudo systemctl status ainfluencer-backend
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U ainfluencer_user -d ainfluencer -h localhost
```

---

## Maintenance

### Regular Updates
- **System Updates**: Weekly security updates
- **Dependencies**: Monthly dependency updates
- **Models**: Update AI models as needed
- **Backups**: Verify backups regularly

### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/ainfluencer
```

```
/var/log/ainfluencer/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 your_user your_user
}
```

---

## Next Steps

1. **Set Up Development Environment**: Follow installation steps
2. **Configure Services**: Set up systemd services
3. **Set Up Monitoring**: Configure logging and monitoring
4. **Set Up Backups**: Implement backup strategy
5. **Security Hardening**: Apply security measures
6. **Test Deployment**: Verify everything works
7. **Documentation**: Document your specific setup

---

## Deployment Checklist

- [ ] System prepared (Ubuntu, drivers, etc.)
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and running
- [ ] Stable Diffusion installed and running
- [ ] Ollama installed with models
- [ ] Backend installed and configured
- [ ] Frontend installed and configured
- [ ] Systemd services configured
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Security hardening applied
- [ ] Services tested and verified
