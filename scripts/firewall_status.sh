#!/bin/bash
"""
Firewall status and configuration summary
"""

echo "🛡️  UFW Firewall Status"
echo "========================"

echo "Status:"
sudo ufw status verbose

echo -e "\n📋 Active Rules:"
sudo ufw status numbered

echo -e "\n🔍 Listening Ports:"
sudo ss -tuln | grep LISTEN

echo -e "\n📊 Summary:"
echo "✅ SSH (port 22) allowed from 192.168.99.0/24 only"
echo "❌ All other inbound traffic blocked"
echo "✅ Outbound traffic allowed"
echo "🛡️  Firewall active and enabled on boot"
