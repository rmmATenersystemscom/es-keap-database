#!/bin/bash
# Script to restore web access (ports 80 and 443)
# Run this tomorrow to re-enable web traffic

echo "Restoring web access (ports 80 and 443)..."

# Add allow rules for ports 80 and 443
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Show current status
echo "Current firewall status:"
sudo ufw status numbered

echo "Web access restored! Ports 80 and 443 are now accessible."
