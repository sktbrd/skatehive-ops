#!/usr/bin/env python3
"""
Quick Instagram Test - Test specific URL
Easy maintenance test for Instagram downloads
"""

import requests
import json
from datetime import datetime

# Test URL - Easy to maintain
TEST_URL = "https://www.instagram.com/p/DOCCkdVj0Iy/"
BASE_URL = "https://raspberrypi.tail83ea3e.ts.net/download"

def quick_test():
    """Quick test of the Instagram downloader with test URL"""
    print("🧪 Quick Instagram Download Test")
    print("=" * 50)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Test URL: {TEST_URL}")
    print(f"🌐 Endpoint: {BASE_URL}")
    print("=" * 50)
    
    # Health check first
    print("\n🔍 Health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Service healthy: {health.get('status')}")
            print(f"   Version: {health.get('version')}")
            print(f"   Cookies valid: {health.get('authentication', {}).get('cookies_valid')}")
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test download
    print(f"\n📥 Testing download...")
    try:
        payload = {"url": TEST_URL}
        response = requests.post(f"{BASE_URL}/", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Download successful!")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            if 'ipfs_hash' in result:
                print(f"   📦 IPFS Hash: {result['ipfs_hash']}")
            if 'filename' in result:
                print(f"   📄 Filename: {result['filename']}")
            if 'size' in result:
                print(f"   📊 Size: {result['size']} bytes")
                
        elif response.status_code == 400:
            print(f"❌ Bad request: {response.json().get('error', 'Unknown error')}")
        elif response.status_code == 404:
            print(f"❌ Post not found or private")
        else:
            print(f"❌ Download failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:100]}...")
                
    except Exception as e:
        print(f"❌ Download error: {e}")
    
    # Check recent logs
    print(f"\n📋 Checking recent logs...")
    try:
        response = requests.get(f"{BASE_URL}/logs", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            print(f"   Found {len(logs)} total log entries")
            
            # Show last 3 logs
            for log in logs[-3:]:
                timestamp = log.get('timestamp', 'Unknown')
                status = log.get('status', 'unknown')
                url = log.get('url', 'No URL')
                success = log.get('success', False)
                
                # Check if this is our test URL
                is_our_test = TEST_URL in url
                marker = "👈 OUR TEST" if is_our_test else ""
                
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {timestamp[-8:]} - {status} - {url[:40]}... {marker}")
                
                if not success and 'error' in log:
                    print(f"      Error: {log['error']}")
        else:
            print(f"   ❌ Could not fetch logs: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Log check error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Quick test completed!")
    print("💡 Edit TEST_URL in this script to test different URLs")

if __name__ == "__main__":
    quick_test()