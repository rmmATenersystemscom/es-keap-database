#!/bin/bash
# Keap Exporter Server Hardening - Backup and Rollback Script
# This script creates backups of all configurations before making changes
# and provides rollback functionality

set -euo pipefail

BACKUP_DIR="/opt/es-keap-database/backups/$(date +%Y%m%d_%H%M%S)"
SUDO_PASS="St. Theo doret"

echo "=== Keap Exporter Server Hardening Backup/Rollback Script ==="

create_backup() {
    echo "Creating backup in: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Backup UFW status
    echo "$SUDO_PASS" | sudo -S ufw status > "$BACKUP_DIR/ufw_status.txt" 2>/dev/null || true
    
    # Backup nginx configuration
    if [ -f /etc/nginx/sites-available/keapdb.conf ]; then
        echo "$SUDO_PASS" | sudo -S cp /etc/nginx/sites-available/keapdb.conf "$BACKUP_DIR/nginx_keapdb.conf"
    fi
    
    # Backup nginx.conf
    echo "$SUDO_PASS" | sudo -S cp /etc/nginx/nginx.conf "$BACKUP_DIR/nginx.conf"
    
    # Backup systemd service
    if [ -f /etc/systemd/system/keap-oauth.service ]; then
        echo "$SUDO_PASS" | sudo -S cp /etc/systemd/system/keap-oauth.service "$BACKUP_DIR/keap-oauth.service"
    fi
    
    # Backup current firewall rules
    echo "$SUDO_PASS" | sudo -S iptables-save > "$BACKUP_DIR/iptables_rules.txt" 2>/dev/null || true
    
    # Backup current nftables rules
    echo "$SUDO_PASS" | sudo -S nft list ruleset > "$BACKUP_DIR/nftables_rules.txt" 2>/dev/null || true
    
    echo "Backup created successfully in: $BACKUP_DIR"
    echo "$BACKUP_DIR" > /opt/es-keap-database/latest_backup.txt
}

rollback() {
    if [ ! -f /opt/es-keap-database/latest_backup.txt ]; then
        echo "No backup found. Cannot rollback."
        exit 1
    fi
    
    BACKUP_DIR=$(cat /opt/es-keap-database/latest_backup.txt)
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    echo "Rolling back from: $BACKUP_DIR"
    
    # Rollback UFW
    echo "$SUDO_PASS" | sudo -S ufw --force reset 2>/dev/null || true
    if [ -f "$BACKUP_DIR/ufw_status.txt" ]; then
        echo "UFW status backed up (manual restoration may be needed)"
    fi
    
    # Rollback nginx
    if [ -f "$BACKUP_DIR/nginx_keapdb.conf" ]; then
        echo "$SUDO_PASS" | sudo -S cp "$BACKUP_DIR/nginx_keapdb.conf" /etc/nginx/sites-available/keapdb.conf
    else
        echo "$SUDO_PASS" | sudo -S rm -f /etc/nginx/sites-available/keapdb.conf
        echo "$SUDO_PASS" | sudo -S rm -f /etc/nginx/sites-enabled/keapdb.conf
    fi
    
    if [ -f "$BACKUP_DIR/nginx.conf" ]; then
        echo "$SUDO_PASS" | sudo -S cp "$BACKUP_DIR/nginx.conf" /etc/nginx/nginx.conf
    fi
    
    # Rollback systemd service
    if [ -f "$BACKUP_DIR/keap-oauth.service" ]; then
        echo "$SUDO_PASS" | sudo -S cp "$BACKUP_DIR/keap-oauth.service" /etc/systemd/system/keap-oauth.service
        echo "$SUDO_PASS" | sudo -S systemctl daemon-reload
    fi
    
    # Reload nginx
    echo "$SUDO_PASS" | sudo -S nginx -t && echo "$SUDO_PASS" | sudo -S systemctl reload nginx
    
    echo "Rollback completed. Services may need manual restart."
}

case "${1:-}" in
    "backup")
        create_backup
        ;;
    "rollback")
        rollback
        ;;
    *)
        echo "Usage: $0 {backup|rollback}"
        echo "  backup   - Create backup of current configurations"
        echo "  rollback - Restore from latest backup"
        exit 1
        ;;
esac
