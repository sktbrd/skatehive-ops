#!/usr/bin/env python3
"""
Quick status check for all Raspberry Pi services via Tailscale Funnel
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.service_monitor import ServiceMonitor
from datetime import datetime

def main():
    monitor = ServiceMonitor()
    
    print("🍓 Raspberry Pi Service Status via Tailscale Funnel")
    print(f"🌐 Public URL: {monitor.base_url}")
    print(f"⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_healthy = True
    
    for service_name, service_config in monitor.services.items():
        health = monitor.check_service_health(service_name)
        
        # Service header
        service_display = {
            "nas": "🗄️  NAS (OpenMediaVault/nginx)",
            "ytipfs-worker": "📱 Instagram Downloader (ytipfs-worker)",
            "video-worker": "📹 Video Transcoder (video-worker)"
        }
        
        print(f"\n{service_display.get(service_name, service_name)}")
        print(f"   Endpoint: {service_config['url']}")
        print(f"   Status: {health['status']}")
        print(f"   Response: {health['response_time']}")
        print(f"   Details: {health.get('details', 'N/A')}")
        
        if "🔴" in health['status']:
            all_healthy = False
    
    print("\n" + "=" * 70)
    if all_healthy:
        print("✅ All services are healthy and responding correctly!")
    else:
        print("⚠️  Some services are having issues. Check the details above.")
    
    print("\n💡 To start the full dashboard: python3 dashboard.py")

if __name__ == "__main__":
    main()
