#!/bin/bash
# SSH Hardening Script
# Secures SSH configuration for production

set -e

SSH_CONFIG="/etc/ssh/sshd_config"
BACKUP_CONFIG="${SSH_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "Hardening SSH configuration..."

# Backup original config
cp "$SSH_CONFIG" "$BACKUP_CONFIG"
echo "Backup created: $BACKUP_CONFIG"

# SSH Configuration changes
cat >> "$SSH_CONFIG" <<EOF

# Production SSH Hardening
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Change default port (update firewall accordingly)
Protocol 2
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowTcpForwarding no
PermitEmptyPasswords no
UsePAM yes
PrintMotd no
MaxStartups 10:30:60
Banner /etc/issue.net
EOF

echo "SSH configuration updated."
echo "IMPORTANT: Ensure you have SSH keys set up before restarting SSH!"
echo "Restart SSH with: sudo systemctl restart sshd"
echo "Test SSH connection before closing current session!"
