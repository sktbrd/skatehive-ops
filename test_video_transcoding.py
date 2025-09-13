#!/usr/bin/env python3
"""
Test Video Transcoding with Error Tracking
Test real video transcoding and monitor for errors
"""

import requests
import json
import time
import os
from datetime import datetime

def test_video_transcoding():
    """Test video transcoding functionality with error monitoring"""
    base_url = "https://raspberrypi.tail83ea3e.ts.net"
    
    print("📹 Testing Video Transcoding Service")
    print("=" * 50)
    
    # Check if test video exists
    test_video_path = "/home/pi/skatehive-monorepo/skatehive-video-transcoder/test-video.mov"
    if not os.path.exists(test_video_path):
        print(f"❌ Test video not found at: {test_video_path}")
        print("   Creating a small test video...")
        # We'll skip creating a video for now and use a URL instead
    
    # Test URLs - mix of valid and potentially problematic ones
    test_videos = [
        {
            "url": "https://sample-videos.com/zip/10/mov/SampleVideo_1280x720_1mb.mov",
            "description": "Valid sample video (should work)"
        },
        {
            "url": "https://invalid-video-url-that-should-fail.com/video.mp4", 
            "description": "Invalid URL (should fail)"
        },
        {
            "url": "https://httpbin.org/status/404",
            "description": "404 URL (should fail with HTTP error)"
        }
    ]
    
    print(f"🔍 Testing {len(test_videos)} video URLs...")
    
    results = []
    
    for i, video_test in enumerate(test_videos, 1):
        url = video_test["url"]
        description = video_test["description"]
        
        print(f"\n{i}. Testing: {description}")
        print(f"   URL: {url}")
        
        try:
            # Send transcoding request
            data = {
                "url": url,
                "user": "test_error_monitoring",
                "hp": 100,  # Max HP for testing
                "device": "dashboard/test/error_monitoring"
            }
            
            print(f"   📤 Sending transcode request...")
            
            response = requests.post(f"{base_url}/transcode", 
                                   json=data, 
                                   timeout=120)  # Video transcoding can take time
            
            print(f"   📥 Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('message', 'Transcode completed')}")
                
                # Check if there's output info
                if 'outputUrl' in result:
                    print(f"   🎬 Output URL: {result['outputUrl']}")
                if 'processingTime' in result:
                    print(f"   ⏱️  Processing time: {result['processingTime']}s")
                if 'outputSize' in result:
                    print(f"   📊 Output size: {result['outputSize']}")
                    
                results.append({
                    'url': url,
                    'description': description,
                    'status': 'success',
                    'result': result
                })
            else:
                error_text = response.text
                print(f"   ❌ Failed: {error_text[:100]}...")
                results.append({
                    'url': url,
                    'description': description,
                    'status': 'failed',
                    'error': error_text,
                    'http_code': response.status_code
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout: Request took longer than 120 seconds")
            results.append({
                'url': url,
                'description': description,
                'status': 'timeout',
                'error': 'Request timeout'
            })
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
            results.append({
                'url': url,
                'description': description,
                'status': 'error',
                'error': str(e)
            })
        
        # Wait between requests to avoid overwhelming the service
        if i < len(test_videos):
            print("   ⏳ Waiting 10 seconds before next request...")
            time.sleep(10)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    success_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len([r for r in results if r['status'] == 'failed'])
    error_count = len([r for r in results if r['status'] == 'error'])
    timeout_count = len([r for r in results if r['status'] == 'timeout'])
    
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   💥 Errors: {error_count}")
    print(f"   ⏰ Timeouts: {timeout_count}")
    
    # Show detailed results
    for result in results:
        status_icon = {
            'success': '✅',
            'failed': '❌',
            'error': '💥',
            'timeout': '⏰'
        }.get(result['status'], '❓')
        
        print(f"   {status_icon} {result['description']}")
        if result['status'] != 'success' and 'error' in result:
            error_msg = result['error'][:60] + "..." if len(str(result['error'])) > 60 else result['error']
            print(f"      Error: {error_msg}")
    
    # Check logs after tests
    print("\n🔍 Checking recent transcode logs...")
    try:
        response = requests.get(f"{base_url}/transcode/logs", timeout=10)
        if response.status_code == 200:
            logs = response.json()
            
            # Show last 5 log entries
            recent_logs = logs[-5:] if logs else []
            print(f"   📝 Last {len(recent_logs)} log entries:")
            
            for log in recent_logs:
                timestamp = log.get('timestamp', 'Unknown')
                status = log.get('status', 'Unknown')
                user = log.get('user', 'Unknown')
                filename = log.get('filename', 'Unknown')
                
                if timestamp != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp[:8]
                else:
                    time_str = 'Unknown'
                
                status_icon = {
                    'completed': '✅',
                    'failed': '❌',
                    'error': '💥',
                    'started': '🔄'
                }.get(status, '❓')
                
                filename_short = filename[:25] + "..." if len(filename) > 25 else filename
                
                print(f"      {status_icon} {time_str} - {status} - {user} - {filename_short}")
                
                if status in ['failed', 'error'] and 'error' in log:
                    error_msg = log['error'][:50] + "..." if len(log['error']) > 50 else log['error']
                    print(f"         Error: {error_msg}")
        else:
            print(f"   ❌ Could not fetch logs: HTTP {response.status_code}")
    except Exception as e:
        print(f"   💥 Error fetching logs: {e}")
    
    # Test health endpoint
    print("\n🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/transcode/healthz", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health: {health}")
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   💥 Health check error: {e}")
    
    print("\n💡 Next steps:")
    print("   - Check the dashboard to see if errors are displayed")
    print("   - Monitor the video transcoder panel for recent activity")
    print("   - Check the error monitor panel for error tracking")
    
    return results

if __name__ == "__main__":
    test_video_transcoding()
