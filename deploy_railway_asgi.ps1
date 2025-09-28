# Railway ASGI Deployment Script for PowerShell
# This script helps deploy your Django app with Daphne to Railway

Write-Host "🚀 Railway ASGI Deployment Script" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Check if railway CLI is installed
try {
    $railwayVersion = & railway --version 2>$null
    Write-Host "✅ Railway CLI found: $railwayVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Red
    Write-Host "Please install Railway CLI from: https://docs.railway.app/guides/cli" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "railway.toml")) {
    Write-Host "❌ railway.toml not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from your project root directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ railway.toml found" -ForegroundColor Green

# Login to Railway (if not already logged in)
Write-Host "🔐 Checking Railway login status..." -ForegroundColor Yellow
try {
    $whoami = & railway whoami 2>$null
    Write-Host "✅ Railway login successful: $whoami" -ForegroundColor Green
} catch {
    Write-Host "Please login to Railway:" -ForegroundColor Yellow
    & railway login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Railway login failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Initialize Railway project (if not already initialized)
if (-not (Test-Path ".railway")) {
    Write-Host "🏗️  Initializing Railway project..." -ForegroundColor Yellow
    & railway init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Railway initialization failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "✅ Railway project initialized" -ForegroundColor Green

# Deploy to Railway
Write-Host "📦 Deploying to Railway with ASGI/Daphne..." -ForegroundColor Yellow
& railway up

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host "🌐 Your app should be available at the Railway URL shown above" -ForegroundColor Cyan
    Write-Host "🔧 Don't forget to set your environment variables in Railway dashboard" -ForegroundColor Yellow
    Write-Host "📋 Check RAILWAY_ASGI_DEPLOYMENT.md for detailed configuration" -ForegroundColor Yellow
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host "📋 Check the error messages above and try again" -ForegroundColor Yellow
    Write-Host "📖 Refer to RAILWAY_ASGI_DEPLOYMENT.md for troubleshooting" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Set environment variables in Railway dashboard" -ForegroundColor White
Write-Host "2. Test your HTTP endpoints" -ForegroundColor White
Write-Host "3. Test your WebSocket connections" -ForegroundColor White
Write-Host "4. Monitor logs with 'railway logs'" -ForegroundColor White

Read-Host "Press Enter to exit"