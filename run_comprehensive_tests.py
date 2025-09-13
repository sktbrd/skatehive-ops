#!/usr/bin/env python3
"""
Comprehensive Service Test Suite
Runs tests for both Instagram downloader and video transcoder
"""

import subprocess
import sys
import time
from datetime import datetime

# Test URLs for easy maintenance
TEST_INSTAGRAM_URL = "https://www.instagram.com/p/DOCCkdVj0Iy/"  # Test link (easy to maintain)
INVALID_INSTAGRAM_URL = "https://www.instagram.com/p/INVALID_POST_ID/"

def run_test_script(script_name, description):
    """Run a test script and capture its output"""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd="/home/pi/skatehive-monorepo/skatehive-dashboard",
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_dashboard_status():
    """Check if the dashboard is currently running"""
    print("🔍 Checking dashboard status...")
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", "dashboard.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Dashboard is currently running")
            print("💡 You can monitor errors in real-time!")
            return True
        else:
            print("⚠️  Dashboard is not running")
            print("💡 Start it with: python3 dashboard.py")
            return False
            
    except Exception as e:
        print(f"❌ Error checking dashboard: {e}")
        return False

def test_endpoints_quickly():
    """Quick test of all service endpoints"""
    print("\n🚀 Quick endpoint connectivity test...")
    
    import requests
    
    endpoints = [
        ("NAS", "https://raspberrypi.tail83ea3e.ts.net/nas/"),
        ("Instagram Health", "https://raspberrypi.tail83ea3e.ts.net/instagram/health"),
        ("Video Transcoder Health", "https://raspberrypi.tail83ea3e.ts.net/video/healthz"),
        ("Instagram Logs", "https://raspberrypi.tail83ea3e.ts.net/instagram/logs"),
        ("Video Transcoder Logs", "https://raspberrypi.tail83ea3e.ts.net/video/logs")
    ]
    
    all_healthy = True
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK ({response.elapsed.total_seconds()*1000:.0f}ms)")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            all_healthy = False
    
    return all_healthy

def generate_test_errors():
    """Generate some test errors for the error monitoring system"""
    print("\n⚠️  Generating test errors for monitoring...")
    
    import requests
    
    # Test invalid Instagram URL
    try:
        response = requests.post(
            "https://raspberrypi.tail83ea3e.ts.net/download",
            json={"url": INVALID_INSTAGRAM_URL},
            timeout=10
        )
        print(f"📱 Instagram error test: HTTP {response.status_code}")
    except Exception as e:
        print(f"📱 Instagram error test: {e}")
    
    # Test valid Instagram URL (to show successful download in logs)
    try:
        response = requests.post(
            "https://raspberrypi.tail83ea3e.ts.net/download",
            json={"url": TEST_INSTAGRAM_URL},
            timeout=10
        )
        print(f"📱 Instagram valid test: HTTP {response.status_code}")
    except Exception as e:
        print(f"📱 Instagram valid test: {e}")
    
    # Test invalid video upload
    try:
        files = {'video': ('invalid.mp4', b'not a video', 'video/mp4')}
        data = {'creator': 'error-test', 'userHP': '50'}
        response = requests.post(
            "https://raspberrypi.tail83ea3e.ts.net/transcode/upload",
            files=files,
            data=data,
            timeout=10
        )
        print(f"📹 Video error test: HTTP {response.status_code}")
    except Exception as e:
        print(f"📹 Video error test: {e}")
    
    print("✅ Test errors generated (check error monitor panel)")

def main():
    print("🎯 Skatehive Services - Comprehensive Test Suite")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Check dashboard status
    dashboard_running = check_dashboard_status()
    
    # Quick connectivity test
    if not test_endpoints_quickly():
        print("\n❌ Some endpoints are not responding. Check service status.")
        return
    
    print("\n🎬 All endpoints responding. Starting comprehensive tests...")
    
    # Track test results
    test_results = {}
    
    # Run Instagram downloader tests
    test_results['instagram'] = run_test_script(
        "test_instagram_downloads.py",
        "Instagram Downloader Tests"
    )
    
    time.sleep(5)  # Brief pause between test suites
    
    # Run video transcoder tests
    test_results['video'] = run_test_script(
        "test_video_transcoding.py", 
        "Video Transcoder Tests"
    )
    
    time.sleep(2)
    
    # Generate test errors for monitoring
    generate_test_errors()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 70)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.capitalize()} Tests: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Services are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    if dashboard_running:
        print("\n💡 Check the dashboard error monitor panel for real-time error tracking!")
    else:
        print("\n💡 Start the dashboard to monitor errors: python3 dashboard.py")
    
    print(f"\n🏁 Test suite completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()