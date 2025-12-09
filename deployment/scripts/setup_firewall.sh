#!/bin/bash
# Firewall Setup Script for Ubuntu/Debian
# Configures UFW firewall with production rules

set -e

echo "Setting up firewall..."

# Enable UFW
ufw --force enable

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH (change port if needed)
SSH_PORT=${SSH_PORT:-22}
ufw allow $SSH_PORT/tcp comment 'SSH'

# HTTP and HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Application ports (if exposed directly)
# ufw allow 8000/tcp comment 'Backend API'
# ufw allow 3000/tcp comment 'Web Frontend'

# Monitoring ports (restrict to internal network)
# ufw allow from 10.0.0.0/8 to any port 9090 comment 'Prometheus'
# ufw allow from 10.0.0.0/8 to any port 3001 comment 'Grafana'

# Database (restrict to internal network only)
# ufw allow from 10.0.0.0/8 to any port 5432 comment 'PostgreSQL'

# Redis (restrict to internal network only)
# ufw allow from 10.0.0.0/8 to any port 6379 comment 'Redis'

# Show status
echo "Firewall rules configured:"
ufw status numbered

echo "Firewall setup completed"
