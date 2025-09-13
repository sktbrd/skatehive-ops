#!/usr/bin/env python3
"""
Instagram Downloader Test Script
Tests the Instagram download functionality via Tailscale Funnel
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "https://raspberrypi.tail83ea3e.ts.net/instagram"

# Test Instagram URLs (these should be public posts)
TEST_URLS = [
    "https://www.instagram.com/p/DOCCkdVj0Iy/",  # Test link (easy to maintain)
    "https://www.instagram.com/p/DABbmEBM8gU/",  # Example public post
    "https://www.instagram.com/reel/C_8gQZNtKhG/",  # Example reel
]

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Cookies valid: {data.get('authentication', {}).get('cookies_valid')}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_download(url):
    """Test downloading an Instagram post"""
    print(f"\n📥 Testing download: {url}")
    
    try:
        # Start download
        payload = {"url": url}
        response = requests.post(f"{BASE_URL}/", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Download successful!")
            print(f"   Filename: {result.get('filename', 'N/A')}")
            print(f"   IPFS Hash: {result.get('ipfs_hash', 'N/A')}")
            print(f"   Gateway URL: {result.get('gateway_url', 'N/A')[:100]}...")
            print(f"   File size: {result.get('file_size', 'N/A')}")
            return True
        else:
            print(f"❌ Download failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Download timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def test_logs_endpoint():
    """Test the logs endpoint"""
    print("\n📋 Testing logs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/logs", timeout=10)
        if response.status_code == 200:
            logs = response.json()
            recent_logs = logs.get('logs', [])[:5]  # Get last 5 logs
            print(f"✅ Logs retrieved: {len(logs.get('logs', []))} total entries")
            
            if recent_logs:
                print("   Recent entries:")
                for log in recent_logs:
                    timestamp = log.get('timestamp', 'Unknown')
                    status = log.get('status', 'Unknown')
                    url = log.get('url', 'Unknown')[:50] + "..."
                    print(f"     {timestamp[:19]} | {status} | {url}")
            else:
                print("   No recent log entries found")
            return True
        else:
            print(f"❌ Logs failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Logs error: {e}")
        return False

def test_cookies_status():
    """Test the cookies status endpoint"""
    print("\n🍪 Testing cookies status...")
    try:
        response = requests.get(f"{BASE_URL}/cookies/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cookies status retrieved")
            print(f"   Cookies exist: {data.get('cookies_exist')}")
            print(f"   Cookies valid: {data.get('cookies_valid')}")
            print(f"   Last validation: {data.get('last_validation', 'Never')}")
            return True
        else:
            print(f"❌ Cookies status failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cookies status error: {e}")
        return False

def main():
    """Run all Instagram downloader tests"""
    print("🍓 Instagram Downloader Test Suite")
    print("=" * 60)
    print(f"Testing endpoint: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test health first
    if not test_health_endpoint():
        print("\n❌ Health check failed - aborting other tests")
        return
    
    # Test other endpoints
    test_cookies_status()
    test_logs_endpoint()
    
    # Test downloads (only if health is good)
    print(f"\n🎬 Testing Downloads ({len(TEST_URLS)} URLs)")
    print("-" * 40)
    
    success_count = 0
    for i, url in enumerate(TEST_URLS, 1):
        print(f"\nTest {i}/{len(TEST_URLS)}:")
        if test_download(url):
            success_count += 1
        time.sleep(2)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"Downloads tested: {len(TEST_URLS)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(TEST_URLS) - success_count}")
    print(f"Success rate: {(success_count/len(TEST_URLS)*100):.1f}%")
    
    if success_count == len(TEST_URLS):
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check logs above")

if __name__ == "__main__":
    main()
