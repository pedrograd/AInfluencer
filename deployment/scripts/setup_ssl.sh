#!/bin/bash
# SSL/TLS Setup Script using Let's Encrypt
# Usage: ./setup_ssl.sh <domain>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 yourdomain.com"
    exit 1
fi

DOMAIN="$1"
EMAIL="${SSL_EMAIL:-admin@$DOMAIN}"

echo "Setting up SSL for domain: $DOMAIN"
echo "Email: $EMAIL"

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily
systemctl stop nginx || true

# Obtain certificate
certbot certonly --standalone \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# Create SSL directory for nginx
mkdir -p /etc/nginx/ssl

# Copy certificates
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/ssl/cert.pem
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /etc/nginx/ssl/key.pem

# Set permissions
chmod 600 /etc/nginx/ssl/key.pem
chmod 644 /etc/nginx/ssl/cert.pem

# Setup auto-renewal
cat > /etc/cron.d/certbot-renew <<EOF
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

echo "SSL certificate installed successfully"
echo "Certificates are in: /etc/nginx/ssl/"
echo "Auto-renewal configured in cron"
