# Production Deployment Script
# Run this after adding credits to your DeepSeek account

Write-Host "🚀 PromptCraft Production Deployment" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# Check if credits are working
Write-Host "`n💳 Testing DeepSeek API with credits..." -ForegroundColor Cyan
$env:DEEPSEEK_API_KEY = "sk-e2b0d6d2de3a4850bfc21ebd4a671af8"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"

Write-Host "Running integration test..." -ForegroundColor Yellow
python test_deepseek_ai.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DeepSeek API test successful!" -ForegroundColor Green
    
    # Create .env for production
    Write-Host "`n📝 Creating production .env file..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env" -Force
    Write-Host "✅ Production .env created from template" -ForegroundColor Green
    
    # Start Redis if not running
    Write-Host "`n🔴 Checking Redis..." -ForegroundColor Cyan
    try {
        $redisCheck = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
        if ($redisCheck.TcpTestSucceeded) {
            Write-Host "✅ Redis is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis not running. Starting with Docker..." -ForegroundColor Yellow
            docker run -d -p 6379:6379 --name redis-promptcraft redis:alpine
            Start-Sleep 3
            Write-Host "✅ Redis started via Docker" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ Redis check failed. Please ensure Redis is running." -ForegroundColor Yellow
    }
    
    # Run migrations
    Write-Host "`n🗄️ Running database migrations..." -ForegroundColor Cyan
    python manage.py migrate
    
    # Collect static files
    Write-Host "`n📁 Collecting static files..." -ForegroundColor Cyan
    python manage.py collectstatic --noinput
    
    # Create superuser prompt
    Write-Host "`n👤 Create admin user? (Optional)" -ForegroundColor Cyan
    $createUser = Read-Host "Create superuser? (y/N)"
    if ($createUser -eq 'y' -or $createUser -eq 'Y') {
        python manage.py createsuperuser
    }
    
    # Start production server
    Write-Host "`n🚀 Starting Production Server..." -ForegroundColor Green
    Write-Host "===============================" -ForegroundColor Green
    
    Write-Host "`nProduction server starting with WebSocket support..." -ForegroundColor Yellow
    Write-Host "URL: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Admin: http://localhost:8000/admin" -ForegroundColor Cyan
    Write-Host "WebSocket: ws://localhost:8000/ws/" -ForegroundColor Cyan
    
    Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Gray
    
    # Start with Daphne for WebSocket support
    daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
    
} else {
    Write-Host "`n❌ DeepSeek API test failed!" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "1. Add credits to your DeepSeek account" -ForegroundColor Yellow
    Write-Host "2. Verify API key is correct" -ForegroundColor Yellow
    Write-Host "3. Check internet connectivity" -ForegroundColor Yellow
    Write-Host "`nVisit: https://platform.deepseek.com/billing" -ForegroundColor Cyan
}

Write-Host "`n📚 Useful Commands:" -ForegroundColor Cyan
Write-Host "   🧪 Test API: python test_deepseek_ai.py" -ForegroundColor Gray
Write-Host "   🖥️  Development: python manage.py runserver" -ForegroundColor Gray
Write-Host "   🌐 Production: daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application" -ForegroundColor Gray
Write-Host "   📊 Check status: python manage.py check" -ForegroundColor Gray