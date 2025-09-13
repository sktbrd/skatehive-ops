#!/usr/bin/env python3
"""
Test script to verify Tailscale Funnel endpoint monitoring
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.service_monitor import ServiceMonitor

async def test_endpoints():
    """Test all three service endpoints"""
    monitor = ServiceMonitor()
    
    print("🔍 Testing Tailscale Funnel Endpoints...")
    print(f"Base URL: {monitor.base_url}")
    print("-" * 60)
    
    for service_name, service_config in monitor.services.items():
        print(f"\n📊 Testing {service_name}:")
        print(f"   URL: {service_config['url']}")
        print(f"   Check Type: {service_config['check_type']}")
        
        health = monitor.check_service_health(service_name)
        
        print(f"   Status: {health['status']}")
        print(f"   Response Time: {health['response_time']}")
        print(f"   Details: {health.get('details', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Endpoint test complete!")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
