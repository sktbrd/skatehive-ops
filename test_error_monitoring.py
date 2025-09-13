#!/usr/bin/env python3
"""
Test Error Monitoring and Logging
Generate test errors to verify error tracking and display works correctly
"""

import requests
import json
import time
from datetime import datetime

def test_error_monitoring():
    """Test the error monitoring functionality"""
    base_url = "https://raspberrypi.tail83ea3e.ts.net"
    
    print("🧪 Testing Error Monitoring System")
    print("=" * 50)
    
    # Test 1: Check if services are responding
    print("\n1. 📊 Checking service endpoints...")
    
    # Video Transcoder
    try:
        response = requests.get(f"{base_url}/transcode/healthz", timeout=10)
        print(f"   📹 Video Transcoder: {response.status_code} - {response.json().get('ok', 'Unknown')}")
    except Exception as e:
        print(f"   📹 Video Transcoder: ERROR - {e}")
    
    # Instagram Downloader
    try:
        response = requests.get(f"{base_url}/download/health", timeout=10)
        data = response.json()
        print(f"   📱 Instagram Downloader: {response.status_code} - {data.get('status', 'Unknown')}")
    except Exception as e:
        print(f"   📱 Instagram Downloader: ERROR - {e}")
    
    # Test 2: Check logs endpoints for existing errors
    print("\n2. 🔍 Checking for existing errors in logs...")
    
    # Video Transcoder logs
    try:
        response = requests.get(f"{base_url}/transcode/logs", timeout=10)
        if response.status_code == 200:
            logs = response.json()
            failed_logs = [log for log in logs if log.get('status') in ['failed', 'error']]
            print(f"   📹 Video Transcoder: Found {len(failed_logs)} error logs")
            if failed_logs:
                latest = failed_logs[0]
                print(f"      Latest error: {latest.get('error', 'No error message')[:50]}...")
        else:
            print(f"   📹 Video Transcoder logs: HTTP {response.status_code}")
    except Exception as e:
        print(f"   📹 Video Transcoder logs: ERROR - {e}")
    
    # Instagram Downloader logs
    try:
        response = requests.get(f"{base_url}/download/logs", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            failed_logs = [log for log in logs if log.get('status') == 'failed' or not log.get('success', True)]
            print(f"   📱 Instagram Downloader: Found {len(failed_logs)} error logs")
            if failed_logs:
                latest = failed_logs[0]
                print(f"      Latest error: {latest.get('error', latest.get('message', 'No error message'))[:50]}...")
        else:
            print(f"   📱 Instagram Downloader logs: HTTP {response.status_code}")
    except Exception as e:
        print(f"   📱 Instagram Downloader logs: ERROR - {e}")
    
    # Test 3: Test error monitor panel locally
    print("\n3. 🎛️  Testing error monitor panel...")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from panels.error_monitor_panel import create_error_monitor_panel
        panel = create_error_monitor_panel()
        print("   ✅ Error monitor panel created successfully")
        
        # Test the error tracker directly
        from panels.error_monitor_panel import error_tracker
        summary = error_tracker.get_error_summary()
        
        video_errors = summary['video_transcoder']['recent_errors']
        instagram_errors = summary['instagram_downloader']['recent_errors']
        
        print(f"   📊 Error Summary (last 24h):")
        print(f"      📹 Video Transcoder: {video_errors} errors")
        print(f"      📱 Instagram Downloader: {instagram_errors} errors")
        
    except Exception as e:
        print(f"   ❌ Error testing panel: {e}")
    
    # Test 4: Try to trigger an error (safely)
    print("\n4. 🚨 Testing error generation...")
    
    # Try invalid video transcode request
    try:
        invalid_data = {
            "url": "https://invalid-url-that-should-fail.com/video.mp4",
            "user": "test_user",
            "hp": 100
        }
        
        print("   📹 Sending invalid video transcode request...")
        response = requests.post(f"{base_url}/transcode", 
                               json=invalid_data, 
                               timeout=30)
        print(f"      Response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"      Result: {result}")
    except Exception as e:
        print(f"   📹 Video transcode test error: {e}")
    
    # Try invalid Instagram download
    try:
        invalid_instagram_data = {
            "url": "https://instagram.com/p/invalid_post_id_12345/"
        }
        
        print("   📱 Sending invalid Instagram download request...")
        response = requests.post(f"{base_url}/download", 
                               json=invalid_instagram_data, 
                               timeout=30)
        print(f"      Response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"      Result: {result}")
    except Exception as e:
        print(f"   📱 Instagram download test error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Error monitoring test complete!")
    print("\n💡 Tips:")
    print("   - Check the dashboard to see if errors are displayed correctly")
    print("   - Monitor the error panel for real-time error tracking")
    print("   - Errors should show detailed messages and timestamps")

if __name__ == "__main__":
    test_error_monitoring()
