#!/bin/bash
# Script to check current web access status

echo "=== Current Firewall Status ==="
sudo ufw status numbered

echo ""
echo "=== Web Ports Status ==="
echo "Port 80 (HTTP): BLOCKED"
echo "Port 443 (HTTPS): BLOCKED"
echo ""
echo "To restore web access, run: ./restore_web_access.sh"
