#!/usr/bin/env python3
"""
Comprehensive Test Suite for all Skatehive Services
Tests NAS, Instagram Downloader, and Video Transcoder via Tailscale Funnel
"""

import subprocess
import sys
import time
from datetime import datetime

def run_test_script(script_name, description):
    """Run a test script and capture results"""
    print(f"\n{'='*80}")
    print(f"🧪 Running {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=600)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: {description}")
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {description} took too long (>10 minutes)")
        return False
    except Exception as e:
        print(f"❌ ERROR running {description}: {e}")
        return False

def test_basic_endpoints():
    """Test basic health endpoints for all services"""
    print("\n🔍 Basic Health Check Tests")
    print("-" * 50)
    
    import requests
    
    endpoints = [
        ("NAS", "https://raspberrypi.tail83ea3e.ts.net/"),
        ("Instagram Health", "https://raspberrypi.tail83ea3e.ts.net/download/health"),
        ("Video Transcoder Health", "https://raspberrypi.tail83ea3e.ts.net/transcode/healthz"),
    ]
    
    results = []
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK ({response.elapsed.total_seconds()*1000:.0f}ms)")
                results.append(True)
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run comprehensive test suite"""
    print("🍓 SKATEHIVE SERVICES COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing Tailscale Funnel endpoint: https://raspberrypi.tail83ea3e.ts.net")
    print("=" * 80)
    
    # Track results
    test_results = []
    
    # Basic health checks first
    basic_health_ok = test_basic_endpoints()
    test_results.append(("Basic Health Checks", basic_health_ok))
    
    if not basic_health_ok:
        print("\n⚠️  Basic health checks failed - continuing with detailed tests anyway...")
    
    # Run Instagram downloader tests
    instagram_ok = run_test_script("test_instagram_downloads.py", "Instagram Downloader Tests")
    test_results.append(("Instagram Downloader", instagram_ok))
    
    # Small delay between tests
    time.sleep(5)
    
    # Run video transcoder tests
    video_ok = run_test_script("test_video_transcoder.py", "Video Transcoder Tests")
    test_results.append(("Video Transcoder", video_ok))
    
    # Final summary
    print("\n" + "🎯" * 80)
    print("🎯 FINAL TEST SUMMARY")
    print("🎯" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("-" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your Skatehive services are working perfectly!")
    elif passed_tests > 0:
        print(f"\n⚠️  PARTIAL SUCCESS: {passed_tests}/{total_tests} test suites passed")
    else:
        print("\n❌ ALL TESTS FAILED: Check your service configurations")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
