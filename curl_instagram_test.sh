#!/bin/bash
"""
Instagram Downloader cURL Test Script
Quick test using curl commands
"""

BASE_URL="https://raspberrypi.tail83ea3e.ts.net/download"
TEST_URL="https://www.instagram.com/p/DOCCkdVj0Iy/"

echo "🧪 Instagram Downloader cURL Test"
echo "=================================="
echo "🕐 Time: $(date)"
echo "🌐 Endpoint: $BASE_URL"
echo "🔗 Test URL: $TEST_URL"
echo "=================================="

echo
echo "🔍 1. Testing health endpoint..."
curl -s "$BASE_URL/health" | jq '.' 2>/dev/null || curl -s "$BASE_URL/health"

echo
echo "🍪 2. Testing cookie status..."
curl -s "$BASE_URL/cookies/status" | jq '.' 2>/dev/null || curl -s "$BASE_URL/cookies/status"

echo
echo "📋 3. Checking recent logs..."
curl -s "$BASE_URL/logs" | jq '.logs[-3:] | .[] | {timestamp, status, url, success}' 2>/dev/null || curl -s "$BASE_URL/logs"

echo
echo "📥 4. Testing download (this may take a while)..."
echo "   Sending POST request..."

# Create JSON payload
JSON_PAYLOAD="{\"url\":\"$TEST_URL\"}"

# Send the download request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" \
  "$BASE_URL/" 2>/dev/null)

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Download successful!"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "400" ]; then
    echo "   ❌ Bad request (invalid URL format)"
    echo "$BODY" | jq '.error' 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "   ❌ Post not found or private"
    echo "$BODY" | jq '.error' 2>/dev/null || echo "$BODY"
else
    echo "   ❌ Unexpected response: $HTTP_CODE"
    echo "$BODY"
fi

echo
echo "📋 5. Checking logs after test..."
curl -s "$BASE_URL/logs" | jq '.logs[-2:] | .[] | {timestamp: .timestamp[-8:], status, url, success}' 2>/dev/null || curl -s "$BASE_URL/logs"

echo
echo "=================================="
echo "🏁 cURL test completed!"
echo "💡 To test different URLs, edit TEST_URL in this script"