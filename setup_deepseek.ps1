# DeepSeek Quick Start Script
# Run this script to quickly set up your DeepSeek environment

Write-Host "🚀 DeepSeek AI Integration Quick Start" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    
    $envContent = @"
# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (for WebSocket channels)
REDIS_URL=redis://localhost:6379/0

# DeepSeek AI Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.7

# Optional: OpenAI Fallback
OPENAI_API_KEY=your_openai_key_here

# Sentry Configuration (optional)
SENTRY_DSN=your_sentry_dsn_here

# Channel Layers
CHANNEL_LAYERS_BACKEND=channels_redis.core.RedisChannelLayer
CHANNEL_LAYERS_HOST=127.0.0.1
CHANNEL_LAYERS_PORT=6379
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ .env file created with template values" -ForegroundColor Green
    Write-Host "⚠️  Remember to update your API keys!" -ForegroundColor Yellow
}

# Check Python virtual environment
Write-Host "`n🐍 Checking Python Environment..." -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
    
    # Activate virtual environment
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment created and activated" -ForegroundColor Green
}

# Install/upgrade dependencies
Write-Host "`n📦 Installing Dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

# Check if Redis is running
Write-Host "`n🔴 Checking Redis..." -ForegroundColor Cyan
try {
    $redisCheck = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisCheck.TcpTestSucceeded) {
        Write-Host "✅ Redis is running on localhost:6379" -ForegroundColor Green
    } else {
        throw "Redis not accessible"
    }
} catch {
    Write-Host "❌ Redis is not running" -ForegroundColor Red
    Write-Host "💡 Install Redis:" -ForegroundColor Yellow
    Write-Host "   - Windows: Download from https://redis.io/download" -ForegroundColor Yellow
    Write-Host "   - Or use Docker: docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Yellow
}

# Run database migrations
Write-Host "`n🗄️  Running Database Migrations..." -ForegroundColor Cyan
python manage.py makemigrations
python manage.py migrate

# Check DeepSeek API key
Write-Host "`n🔑 Checking API Configuration..." -ForegroundColor Cyan
$deepseekKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY")
if ($deepseekKey) {
    Write-Host "✅ DEEPSEEK_API_KEY environment variable is set" -ForegroundColor Green
} else {
    Write-Host "⚠️  DEEPSEEK_API_KEY not found in environment" -ForegroundColor Yellow
    Write-Host "💡 Set it with: `$env:DEEPSEEK_API_KEY='your-key-here'" -ForegroundColor Yellow
}

# Test the integration
Write-Host "`n🧪 Testing DeepSeek Integration..." -ForegroundColor Cyan
Write-Host "Running integration test..." -ForegroundColor Yellow

try {
    python test_deepseek_ai.py
    Write-Host "✅ Integration test completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Integration test encountered issues" -ForegroundColor Yellow
    Write-Host "Check the output above for details" -ForegroundColor Yellow
}

# Final instructions
Write-Host "`n🎉 Setup Complete!" -ForegroundColor Green
Write-Host "================" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. 🔑 Get your DeepSeek API key from: https://platform.deepseek.com/" -ForegroundColor White
Write-Host "2. 📝 Update your .env file with the actual API key" -ForegroundColor White
Write-Host "3. 🚀 Start the development server:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray

Write-Host "`nWebSocket Server (for production):" -ForegroundColor Cyan
Write-Host "   daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application" -ForegroundColor Gray

Write-Host "`nUseful Commands:" -ForegroundColor Cyan
Write-Host "   🧪 Test integration: python test_deepseek_ai.py" -ForegroundColor Gray
Write-Host "   📊 Check system: python manage.py check" -ForegroundColor Gray
Write-Host "   🗄️  Create superuser: python manage.py createsuperuser" -ForegroundColor Gray

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "   📖 DeepSeek Setup: .\DEEPSEEK_SETUP.md" -ForegroundColor Gray
Write-Host "   🌐 API Docs: https://platform.deepseek.com/docs" -ForegroundColor Gray

Write-Host "`n🎯 Your DeepSeek AI integration is ready!" -ForegroundColor Green