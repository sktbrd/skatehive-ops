#!/bin/bash
# Quick Instagram Download Test with cURL
# Usage: ./quick_curl_test.sh [instagram_url]

BASE_URL="https://raspberrypi.tail83ea3e.ts.net/download"

# Use provided URL or default test URL
TEST_URL="${1:-https://www.instagram.com/p/DOCCkdVj0Iy/}"

echo "🧪 Quick Instagram cURL Test"
echo "URL: $TEST_URL"
echo "=========================="

# Health check
echo "🔍 Health check..."
curl -s "$BASE_URL/health" | jq -r '"Service: " + .status + " | Version: " + .version + " | Cookies: " + (.authentication.cookies_valid|tostring)'

echo

# Download test
echo "📥 Testing download..."
RESPONSE=$(curl -s -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"$TEST_URL\"}" \
  "$BASE_URL/")

HTTP_CODE="${RESPONSE: -3}"
BODY="${RESPONSE%???}"

case $HTTP_CODE in
  200)
    echo "✅ SUCCESS!"
    echo "$BODY" | jq -r '"Filename: " + .filename + " | IPFS: " + .ipfs_hash[:12] + "..."' 2>/dev/null || echo "$BODY"
    ;;
  400)
    echo "❌ BAD REQUEST"
    echo "$BODY" | jq -r '.error' 2>/dev/null || echo "$BODY"
    ;;
  404)
    echo "❌ NOT FOUND (Post may be private or deleted)"
    ;;
  *)
    echo "❌ ERROR: HTTP $HTTP_CODE"
    echo "$BODY"
    ;;
esac

echo
echo "📋 Recent activity:"
curl -s "$BASE_URL/logs" | jq -r '.logs[-3:] | .[] | .timestamp[-8:] + " | " + .status + " | " + (.success//false|tostring) + " | " + .url[0:50] + "..."' 2>/dev/null

echo
echo "💡 Usage: $0 [instagram_url]"