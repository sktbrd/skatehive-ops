#!/usr/bin/env python3
"""
Health check script for automated monitoring
Returns exit code 0 if all services are healthy, 1 if any are down
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.service_monitor import ServiceMonitor

def main():
    monitor = ServiceMonitor()
    
    failed_services = []
    
    for service_name in monitor.services:
        health = monitor.check_service_health(service_name)
        
        if "🔴" in health['status']:
            failed_services.append({
                'name': service_name,
                'status': health['status'],
                'details': health.get('details', 'N/A')
            })
    
    if failed_services:
        print(f"❌ {len(failed_services)} service(s) are down:")
        for service in failed_services:
            print(f"   • {service['name']}: {service['details']}")
        sys.exit(1)
    else:
        print("✅ All services healthy")
        sys.exit(0)

if __name__ == "__main__":
    main()
