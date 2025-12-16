#!/bin/bash
# Production Deployment Script for AInfluencer
# This script automates the production deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="${DEPLOY_DIR:-/opt/AInfluencer}"
SERVICE_USER="${SERVICE_USER:-ainfluencer}"
DOMAIN="${DOMAIN:-your-domain.com}"

echo -e "${GREEN}=== AInfluencer Production Deployment ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Create deployment directory
echo -e "${YELLOW}Step 1: Creating deployment directory...${NC}"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Step 2: Clone or update repository
echo -e "${YELLOW}Step 2: Setting up repository...${NC}"
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest changes..."
    git pull
else
    echo "Please clone the repository to $DEPLOY_DIR first"
    exit 1
fi

# Step 3: Create service user if it doesn't exist
echo -e "${YELLOW}Step 3: Creating service user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$DEPLOY_DIR" "$SERVICE_USER"
    echo "Service user created: $SERVICE_USER"
else
    echo "Service user already exists: $SERVICE_USER"
fi

# Step 4: Set up backend
echo -e "${YELLOW}Step 4: Setting up backend...${NC}"
cd "$DEPLOY_DIR/backend"

# Create virtual environment
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit $DEPLOY_DIR/backend/.env with your production configuration${NC}"
    else
        echo -e "${YELLOW}Creating .env file template...${NC}"
        cat > .env << EOF
# Database
AINFLUENCER_DATABASE_URL=postgresql+asyncpg://ainfluencer_user:CHANGE_ME@localhost:5432/ainfluencer

# Redis
AINFLUENCER_REDIS_URL=redis://localhost:6379/0

# API
AINFLUENCER_API_SECRET_KEY=CHANGE_ME_GENERATE_SECURE_KEY
AINFLUENCER_DEBUG=False

# JWT
AINFLUENCER_JWT_SECRET_KEY=CHANGE_ME_GENERATE_SECURE_KEY
AINFLUENCER_JWT_ALGORITHM=HS256
AINFLUENCER_JWT_EXPIRATION_HOURS=24

# ComfyUI
AINFLUENCER_COMFYUI_BASE_URL=http://localhost:8188

# Storage
AINFLUENCER_STORAGE_TYPE=local
AINFLUENCER_STORAGE_PATH=/storage/content
EOF
        echo -e "${YELLOW}Please edit $DEPLOY_DIR/backend/.env with your production configuration${NC}"
    fi
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Step 5: Set up frontend
echo -e "${YELLOW}Step 5: Setting up frontend...${NC}"
cd "$DEPLOY_DIR/frontend"

# Install dependencies
npm ci --production=false

# Build frontend
npm run build

# Set up environment variables
if [ ! -f ".env.local" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
    else
        cat > .env.local << EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF
    fi
    echo -e "${YELLOW}Please edit $DEPLOY_DIR/frontend/.env.local with your production configuration${NC}"
fi

# Step 6: Set up systemd services
echo -e "${YELLOW}Step 6: Setting up systemd services...${NC}"

# Backend service
cat > /etc/systemd/system/ainfluencer-backend.service << EOF
[Unit]
Description=AInfluencer Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR/backend
Environment="PATH=$DEPLOY_DIR/backend/venv/bin"
ExecStart=$DEPLOY_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Frontend service (using PM2)
echo "Installing PM2 globally..."
npm install -g pm2

# Create PM2 ecosystem file
cat > "$DEPLOY_DIR/frontend/ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: 'ainfluencer-frontend',
    script: 'npm',
    args: 'start',
    cwd: '$DEPLOY_DIR/frontend',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    }
  }]
};
EOF

# Step 7: Set up Nginx
echo -e "${YELLOW}Step 7: Setting up Nginx reverse proxy...${NC}"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# Create Nginx configuration
cat > /etc/nginx/sites-available/ainfluencer << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/ainfluencer /etc/nginx/sites-enabled/
nginx -t

# Step 8: Set permissions
echo -e "${YELLOW}Step 8: Setting permissions...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR"

# Step 9: Enable and start services
echo -e "${YELLOW}Step 9: Enabling and starting services...${NC}"
systemctl daemon-reload
systemctl enable ainfluencer-backend
systemctl start ainfluencer-backend

# Start frontend with PM2
cd "$DEPLOY_DIR/frontend"
sudo -u "$SERVICE_USER" pm2 start ecosystem.config.js
sudo -u "$SERVICE_USER" pm2 save
pm2 startup systemd -u "$SERVICE_USER" --hp "$DEPLOY_DIR"

# Reload Nginx
systemctl reload nginx

# Step 10: SSL Setup (optional)
echo -e "${YELLOW}Step 10: SSL Setup (optional)...${NC}"
if command -v certbot &> /dev/null; then
    echo "Certbot is installed. To set up SSL, run:"
    echo "  certbot --nginx -d $DOMAIN"
else
    echo "To set up SSL with Let's Encrypt:"
    echo "  1. Install certbot: apt-get install certbot python3-certbot-nginx"
    echo "  2. Run: certbot --nginx -d $DOMAIN"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit $DEPLOY_DIR/backend/.env with your production configuration"
echo "  2. Edit $DEPLOY_DIR/frontend/.env.local with your production configuration"
echo "  3. Set up SSL: certbot --nginx -d $DOMAIN"
echo "  4. Check service status:"
echo "     - systemctl status ainfluencer-backend"
echo "     - pm2 status"
echo "     - systemctl status nginx"

