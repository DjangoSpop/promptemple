# Heroku Deployment Script for PromptCraft Backend
# Run this script to deploy to Heroku with all necessary configurations

Write-Host "🚀 PromptCraft Backend - Heroku Deployment Script" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Heroku CLI is installed
try {
    heroku --version | Out-Null
    Write-Host "✅ Heroku CLI installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Heroku CLI not found. Please install from: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Red
    exit 1
}

# Check if logged in to Heroku
try {
    $herokuAuth = heroku auth:whoami 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Logged in to Heroku as: $herokuAuth" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Not logged in to Heroku. Please login:" -ForegroundColor Yellow
        heroku login
    }
} catch {
    Write-Host "⚠️  Not logged in to Heroku. Please login:" -ForegroundColor Yellow
    heroku login
}

Write-Host ""
Write-Host "📋 Deployment Options:" -ForegroundColor Yellow
Write-Host "1. Create new Heroku app"
Write-Host "2. Use existing Heroku app"
Write-Host "3. Configure environment variables only"
Write-Host "4. Deploy code only"
Write-Host "5. Full deployment (recommended)"
Write-Host ""

$choice = Read-Host "Select option (1-5)"

$appName = ""

switch ($choice) {
    "1" {
        Write-Host ""
        $appName = Read-Host "Enter app name (e.g., prompt-temple-backend)"
        Write-Host "Creating Heroku app: $appName" -ForegroundColor Cyan
        heroku create $appName
        
        Write-Host ""
        Write-Host "Adding PostgreSQL..." -ForegroundColor Cyan
        heroku addons:create heroku-postgresql:essential-0 -a $appName
        
        Write-Host ""
        $addRedis = Read-Host "Add Redis? (y/n)"
        if ($addRedis -eq "y") {
            Write-Host "Adding Redis..." -ForegroundColor Cyan
            heroku addons:create heroku-redis:mini -a $appName
        }
    }
    "2" {
        Write-Host ""
        $appName = Read-Host "Enter existing app name"
        Write-Host "Connecting to Heroku app: $appName" -ForegroundColor Cyan
        heroku git:remote -a $appName
    }
    "3" {
        Write-Host ""
        $appName = Read-Host "Enter app name"
        Write-Host "Configuring environment variables only..." -ForegroundColor Cyan
    }
    "4" {
        Write-Host ""
        $appName = Read-Host "Enter app name"
        Write-Host "Deploying code only..." -ForegroundColor Cyan
    }
    "5" {
        Write-Host ""
        $appName = Read-Host "Enter app name (existing or new)"
        Write-Host "Starting full deployment..." -ForegroundColor Cyan
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Configure environment variables
if ($choice -in @("1", "3", "5")) {
    Write-Host ""
    Write-Host "⚙️  Configuring Environment Variables" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    
    # Django Configuration
    Write-Host ""
    Write-Host "Django Configuration:" -ForegroundColor Yellow
    $secretKey = Read-Host "Enter SECRET_KEY (press Enter to generate random)"
    if ([string]::IsNullOrWhiteSpace($secretKey)) {
        $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})
        Write-Host "Generated SECRET_KEY: $secretKey" -ForegroundColor Green
    }
    
    heroku config:set DJANGO_ENVIRONMENT=heroku -a $appName
    heroku config:set SECRET_KEY="$secretKey" -a $appName
    heroku config:set DEBUG=False -a $appName
    heroku config:set ALLOWED_HOSTS=".herokuapp.com,www.prompt-temple.com,prompt-temple.com" -a $appName
    
    # Frontend URL
    Write-Host ""
    $frontendUrl = Read-Host "Enter FRONTEND_URL (default: https://www.prompt-temple.com)"
    if ([string]::IsNullOrWhiteSpace($frontendUrl)) {
        $frontendUrl = "https://www.prompt-temple.com"
    }
    heroku config:set FRONTEND_URL="$frontendUrl" -a $appName
    
    # Google OAuth
    Write-Host ""
    Write-Host "Google OAuth Configuration:" -ForegroundColor Yellow
    Write-Host "⚠️  IMPORTANT: Make sure to add redirect URI to Google Console!" -ForegroundColor Red
    Write-Host "   https://www.prompt-temple.com/auth/callback/google" -ForegroundColor Yellow
    
    $googleClientId = Read-Host "Enter GOOGLE_OAUTH2_CLIENT_ID (press Enter for existing)"
    if (![string]::IsNullOrWhiteSpace($googleClientId)) {
        heroku config:set GOOGLE_OAUTH2_CLIENT_ID="$googleClientId" -a $appName
    }
    
    $googleSecret = Read-Host "Enter GOOGLE_OAUTH2_CLIENT_SECRET (press Enter to skip)"
    if (![string]::IsNullOrWhiteSpace($googleSecret)) {
        heroku config:set GOOGLE_OAUTH2_CLIENT_SECRET="$googleSecret" -a $appName
    }
    
    $googleRedirectUri = Read-Host "Enter SOCIAL_AUTH_GOOGLE_REDIRECT_URI (default: https://www.prompt-temple.com/auth/callback/google)"
    if ([string]::IsNullOrWhiteSpace($googleRedirectUri)) {
        $googleRedirectUri = "https://www.prompt-temple.com/auth/callback/google"
    }
    heroku config:set SOCIAL_AUTH_GOOGLE_REDIRECT_URI="$googleRedirectUri" -a $appName
    
    # GitHub OAuth
    Write-Host ""
    Write-Host "GitHub OAuth Configuration:" -ForegroundColor Yellow
    $githubClientId = Read-Host "Enter GITHUB_CLIENT_ID (press Enter to skip)"
    if (![string]::IsNullOrWhiteSpace($githubClientId)) {
        heroku config:set GITHUB_CLIENT_ID="$githubClientId" -a $appName
        
        $githubSecret = Read-Host "Enter GITHUB_CLIENT_SECRET"
        heroku config:set GITHUB_CLIENT_SECRET="$githubSecret" -a $appName
        
        $githubRedirectUri = Read-Host "Enter SOCIAL_AUTH_GITHUB_REDIRECT_URI (default: https://www.prompt-temple.com/auth/callback/github)"
        if ([string]::IsNullOrWhiteSpace($githubRedirectUri)) {
            $githubRedirectUri = "https://www.prompt-temple.com/auth/callback/github"
        }
        heroku config:set SOCIAL_AUTH_GITHUB_REDIRECT_URI="$githubRedirectUri" -a $appName
    }
    
    # AI API Keys
    Write-Host ""
    Write-Host "AI API Configuration:" -ForegroundColor Yellow
    $deepseekKey = Read-Host "Enter DEEPSEEK_API_KEY (press Enter to skip)"
    if (![string]::IsNullOrWhiteSpace($deepseekKey)) {
        heroku config:set DEEPSEEK_API_KEY="$deepseekKey" -a $appName
        heroku config:set DEEPSEEK_BASE_URL="https://api.deepseek.com/v1" -a $appName
    }
    
    $tavilyKey = Read-Host "Enter TAVILY_API_KEY (press Enter to skip)"
    if (![string]::IsNullOrWhiteSpace($tavilyKey)) {
        heroku config:set TAVILY_API_KEY="$tavilyKey" -a $appName
    }
    
    $zaiToken = Read-Host "Enter ZAI_API_TOKEN (press Enter to skip)"
    if (![string]::IsNullOrWhiteSpace($zaiToken)) {
        heroku config:set ZAI_API_TOKEN="$zaiToken" -a $appName
        heroku config:set ZAI_API_BASE="https://api.z.ai/api/paas/v4" -a $appName
        heroku config:set ZAI_DEFAULT_MODEL="glm-4-32b-0414-128k" -a $appName
    }
    
    Write-Host ""
    Write-Host "✅ Environment variables configured" -ForegroundColor Green
}

# Deploy code
if ($choice -in @("1", "4", "5")) {
    Write-Host ""
    Write-Host "📦 Preparing Code for Deployment" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    
    # Check git status
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host ""
        Write-Host "⚠️  Uncommitted changes detected:" -ForegroundColor Yellow
        git status --short
        
        Write-Host ""
        $commitChanges = Read-Host "Commit changes before deploy? (y/n)"
        if ($commitChanges -eq "y") {
            $commitMsg = Read-Host "Enter commit message"
            git add .
            git commit -m "$commitMsg"
            Write-Host "✅ Changes committed" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "Pushing to Heroku..." -ForegroundColor Cyan
    
    # Try main branch first, then master
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "Current branch: $currentBranch" -ForegroundColor Yellow
    
    if ($currentBranch -eq "main") {
        git push heroku main
    } elseif ($currentBranch -eq "master") {
        git push heroku master
    } else {
        Write-Host "⚠️  Current branch is '$currentBranch'" -ForegroundColor Yellow
        $pushBranch = Read-Host "Push $currentBranch to heroku main? (y/n)"
        if ($pushBranch -eq "y") {
            git push heroku "${currentBranch}:main"
        } else {
            Write-Host "❌ Deployment cancelled" -ForegroundColor Red
            exit 1
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Code deployed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Deployment failed. Check logs above." -ForegroundColor Red
        exit 1
    }
}

# Run migrations
if ($choice -in @("1", "5")) {
    Write-Host ""
    Write-Host "🗄️  Running Database Migrations" -ForegroundColor Cyan
    Write-Host "===============================" -ForegroundColor Cyan
    
    heroku run python manage.py migrate -a $appName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migrations completed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Migrations failed. Check errors above." -ForegroundColor Yellow
    }
    
    Write-Host ""
    $createSuperuser = Read-Host "Create superuser? (y/n)"
    if ($createSuperuser -eq "y") {
        heroku run python manage.py createsuperuser -a $appName
    }
}

# Final checks
Write-Host ""
Write-Host "🔍 Final Checks" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

Write-Host ""
Write-Host "App Status:" -ForegroundColor Yellow
heroku ps -a $appName

Write-Host ""
Write-Host "Recent Logs:" -ForegroundColor Yellow
heroku logs --tail -n 50 -a $appName

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app is available at:" -ForegroundColor Cyan
heroku domains -a $appName

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify health check: https://$appName.herokuapp.com/health/"
Write-Host "2. Test API endpoints: https://$appName.herokuapp.com/api/"
Write-Host "3. Test OAuth flow from frontend"
Write-Host "4. Monitor logs: heroku logs --tail -a $appName"
Write-Host "5. Set up custom domain (optional)"
Write-Host ""
Write-Host "⚠️  IMPORTANT: Update Google OAuth Console with production redirect URI!" -ForegroundColor Red
Write-Host "   https://console.cloud.google.com/apis/credentials" -ForegroundColor Yellow
Write-Host "   Add: https://www.prompt-temple.com/auth/callback/google" -ForegroundColor Yellow
Write-Host ""

$openApp = Read-Host "Open app in browser? (y/n)"
if ($openApp -eq "y") {
    heroku open -a $appName
}

Write-Host ""
Write-Host "🎉 Deployment script completed!" -ForegroundColor Green
