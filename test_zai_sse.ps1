# Z.AI SSE Chat Completions Test Script (PowerShell)
# Make sure to replace YOUR_JWT_TOKEN with a real JWT token

Write-Host "🧪 Testing Z.AI SSE Chat Completions Endpoint" -ForegroundColor Cyan
Write-Host "=============================================="

# Configuration
$BASE_URL = "http://localhost:8000"
$JWT_TOKEN = "YOUR_JWT_TOKEN"  # Replace with actual JWT

Write-Host "📍 Base URL: $BASE_URL"
Write-Host "🔐 JWT Token: $($JWT_TOKEN.Substring(0, [Math]::Min(20, $JWT_TOKEN.Length)))..." # Show only first 20 chars

Write-Host ""
Write-Host "1️⃣ Testing Health Check..." -ForegroundColor Yellow
Write-Host "-------------------------"

try {
    $headers = @{
        "Authorization" = "Bearer $JWT_TOKEN"
        "Content-Type" = "application/json"
    }
    
    $healthResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v2/chat/health/" -Method GET -Headers $headers
    Write-Host "✅ Health Check Success:" -ForegroundColor Green
    $healthResponse | ConvertTo-Json -Depth 3 | Write-Host
}
catch {
    Write-Host "❌ Health Check Failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "2️⃣ Testing SSE Chat Completions..." -ForegroundColor Yellow
Write-Host "--------------------------------"

# Test payload
$payload = @{
    model = "glm-4-32b-0414-128k"
    messages = @(
        @{
            role = "user"
            content = "As a marketing expert, please create an attractive slogan for my product: AI-powered chat platform."
        }
    )
    stream = $true
    temperature = 0.7
    max_tokens = 500
} | ConvertTo-Json -Depth 3

try {
    $headers = @{
        "Authorization" = "Bearer $JWT_TOKEN"
        "Content-Type" = "application/json"
        "Accept" = "text/event-stream"
    }
    
    Write-Host "📤 Sending SSE request..."
    Write-Host "📋 Payload:" 
    Write-Host $payload
    
    # Note: PowerShell's Invoke-RestMethod doesn't handle SSE well
    # For full SSE testing, use the Python script or curl
    Write-Host "⚠️  PowerShell doesn't handle SSE streaming well."
    Write-Host "   Use the Python script (test_zai_sse.py) for full SSE testing."
    Write-Host "   Or use curl with the bash script (test_zai_curl.sh)."
    
    # Test basic connectivity
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/v2/chat/completions/" -Method POST -Body $payload -Headers $headers -TimeoutSec 10
    Write-Host "✅ Connection successful. Status: $($response.StatusCode)"
    Write-Host "📡 Response headers:"
    $response.Headers | Format-Table
    
}
catch {
    Write-Host "❌ SSE Test Failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "✅ Test completed!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 For full SSE streaming tests, run:" -ForegroundColor Cyan
Write-Host "   python test_zai_sse.py"