#!/usr/bin/env python3
"""
Video Transcoder Test Script
Tests the video transcoding functionality via Tailscale Funnel
"""

import requests
import json
import time
import os
import base64
from datetime import datetime

BASE_URL = "https://raspberrypi.tail83ea3e.ts.net/video"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('ok')}")
            print(f"   Service: {data.get('service', 'video-transcoder')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_status_endpoint():
    """Test the status endpoint"""
    print("\n📊 Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status retrieved")
            print(f"   Queue size: {data.get('queue_size', 0)}")
            print(f"   Active jobs: {data.get('active_jobs', 0)}")
            print(f"   Total processed: {data.get('total_processed', 0)}")
            return True
        else:
            print(f"❌ Status failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status error: {e}")
        return False

def test_video_upload_and_transcode():
    """Test uploading and transcoding a small test video"""
    print("\n🎬 Testing video upload and transcoding...")
    
    # Check if test video exists
    test_video_path = "/home/pi/skatehive-monorepo/skatehive-video-transcoder/test-video.mov"
    if not os.path.exists(test_video_path):
        print(f"❌ Test video not found at {test_video_path}")
        return False
    
    try:
        # Read and encode the test video
        with open(test_video_path, 'rb') as f:
            video_data = f.read()
        
        file_size_mb = len(video_data) / (1024 * 1024)
        print(f"   Test video size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 50:  # Limit test to reasonable size
            print("   ⚠️  Test video is large, this may take a while...")
        
        # Prepare the upload
        files = {
            'video': ('test-video.mov', video_data, 'video/quicktime')
        }
        
        data = {
            'output_format': 'mp4',
            'quality': 'medium',
            'audio_codec': 'aac',
            'video_codec': 'libx264'
        }
        
        print("   Uploading video...")
        start_time = time.time()
        
        # Upload and transcode (this may take a while)
        response = requests.post(f"{BASE_URL}/transcode", files=files, data=data, timeout=300)
        
        upload_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transcoding successful! ({upload_time:.1f}s)")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Output file: {result.get('output_file', 'N/A')}")
            print(f"   IPFS hash: {result.get('ipfs_hash', 'N/A')}")
            
            # If we have a download URL, test it
            if 'download_url' in result:
                download_url = result['download_url']
                print(f"   Download URL: {download_url[:80]}...")
                
                # Test download
                dl_response = requests.head(download_url, timeout=10)
                if dl_response.status_code == 200:
                    content_length = dl_response.headers.get('content-length')
                    if content_length:
                        size_mb = int(content_length) / (1024 * 1024)
                        print(f"   ✅ Output file accessible ({size_mb:.2f} MB)")
                    else:
                        print(f"   ✅ Output file accessible")
                else:
                    print(f"   ⚠️  Output file not accessible: HTTP {dl_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Transcoding failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Transcoding timed out (>5min)")
        return False
    except FileNotFoundError:
        print(f"❌ Test video file not found: {test_video_path}")
        return False
    except Exception as e:
        print(f"❌ Transcoding error: {e}")
        return False

def test_job_status():
    """Test job status endpoint (if we have recent jobs)"""
    print("\n📋 Testing recent jobs...")
    try:
        response = requests.get(f"{BASE_URL}/jobs", timeout=10)
        if response.status_code == 200:
            jobs = response.json()
            recent_jobs = jobs.get('jobs', [])[:5]  # Get last 5 jobs
            print(f"✅ Jobs retrieved: {len(jobs.get('jobs', []))} total entries")
            
            if recent_jobs:
                print("   Recent jobs:")
                for job in recent_jobs:
                    job_id = job.get('id', 'Unknown')[:8]
                    status = job.get('status', 'Unknown')
                    created = job.get('created_at', 'Unknown')[:19]
                    input_file = job.get('input_file', 'Unknown')
                    print(f"     {created} | {job_id} | {status} | {input_file}")
            else:
                print("   No recent jobs found")
            return True
        else:
            print(f"❌ Jobs endpoint failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Jobs error: {e}")
        return False

def test_formats_endpoint():
    """Test supported formats endpoint"""
    print("\n🎛️  Testing supported formats...")
    try:
        response = requests.get(f"{BASE_URL}/formats", timeout=10)
        if response.status_code == 200:
            formats = response.json()
            print(f"✅ Formats retrieved")
            
            video_formats = formats.get('video_formats', [])
            audio_formats = formats.get('audio_formats', [])
            
            print(f"   Video formats: {', '.join(video_formats[:5])}{'...' if len(video_formats) > 5 else ''}")
            print(f"   Audio formats: {', '.join(audio_formats[:5])}{'...' if len(audio_formats) > 5 else ''}")
            return True
        else:
            print(f"❌ Formats endpoint failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Formats error: {e}")
        return False

def main():
    """Run all video transcoder tests"""
    print("🍓 Video Transcoder Test Suite")
    print("=" * 60)
    print(f"Testing endpoint: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test health first
    if test_health_endpoint():
        tests_passed += 1
    else:
        print("\n❌ Health check failed - some tests may not work")
    
    # Test other endpoints
    if test_status_endpoint():
        tests_passed += 1
    
    if test_formats_endpoint():
        tests_passed += 1
    
    if test_job_status():
        tests_passed += 1
    
    # Test video transcoding (the big one)
    print("\n" + "🎬" * 20)
    print("Starting video transcoding test...")
    print("This may take several minutes for larger videos!")
    print("🎬" * 20)
    
    if test_video_upload_and_transcode():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"Tests run: {total_tests}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {total_tests - tests_passed}")
    print(f"Success rate: {(tests_passed/total_tests*100):.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check logs above")

if __name__ == "__main__":
    main()
