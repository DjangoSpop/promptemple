#!/bin/bash

# Z.AI SSE Chat Completions Test Script
# Make sure to replace YOUR_JWT_TOKEN with a real JWT token

echo "🧪 Testing Z.AI SSE Chat Completions Endpoint"
echo "=============================================="

# Configuration
BASE_URL="http://localhost:8000"
JWT_TOKEN="YOUR_JWT_TOKEN"  # Replace with actual JWT

echo "📍 Base URL: $BASE_URL"
echo "🔐 JWT Token: ${JWT_TOKEN:0:20}..." # Show only first 20 chars for security

echo ""
echo "1️⃣ Testing Health Check..."
echo "-------------------------"

curl -X GET "$BASE_URL/api/v2/chat/health/" \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -w "\n📊 HTTP Status: %{http_code}\n📏 Response Time: %{time_total}s\n\n"

echo "2️⃣ Testing SSE Chat Completions..."
echo "--------------------------------"

curl -X POST "$BASE_URL/api/v2/chat/completions/" \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
       "model": "glm-4-32b-0414-128k",
       "messages": [
         {
           "role": "user",
           "content": "As a marketing expert, please create an attractive slogan for my product: AI-powered chat platform."
         }
       ],
       "stream": true,
       "temperature": 0.7,
       "max_tokens": 500
     }' \
     --no-buffer \
     -w "\n\n📊 HTTP Status: %{http_code}\n📏 Response Time: %{time_total}s\n"

echo ""
echo "✅ Test completed!"