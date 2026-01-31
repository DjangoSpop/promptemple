# GraphQL Deployment Script for Heroku
# Deploy prompt iteration tracking system to production

Write-Host "🚀 Deploying GraphQL Prompt History System to Heroku" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

# Step 0: Activate virtual environment
Write-Host "`n🔧 Step 0: Activating virtual environment..." -ForegroundColor Yellow

$venvPath = ".\venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    Write-Host "Activating venv..." -ForegroundColor Cyan
    & $activateScript
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not found, continuing without activation..." -ForegroundColor Yellow
    Write-Host "   (This is okay if running in CI/CD or system Python)" -ForegroundColor Cyan
}

# Step 1: Create migrations
Write-Host "`n📦 Step 1: Creating database migrations..." -ForegroundColor Yellow
python manage.py makemigrations prompt_history

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create migrations" -ForegroundColor Red
    exit 1
}

# Step 2: Apply migrations locally (for testing)
Write-Host "`n🔧 Step 2: Testing migrations locally..." -ForegroundColor Yellow
python manage.py migrate prompt_history --noinput

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to apply migrations locally" -ForegroundColor Red
    exit 1
}

# Step 3: Run GraphQL setup script
Write-Host "`n🧪 Step 3: Setting up test data..." -ForegroundColor Yellow
python setup_graphql.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Test data setup had issues (this is okay if data already exists)" -ForegroundColor Yellow
}

# Step 4: Git commit
Write-Host "`n💾 Step 4: Committing changes..." -ForegroundColor Yellow
git add .
git status

$commitMessage = Read-Host "Enter commit message (or press Enter for default)"
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "feat: Add GraphQL prompt iteration tracking system"
}

git commit -m $commitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: No changes to commit or commit failed" -ForegroundColor Yellow
}

# Step 5: Push to Heroku
Write-Host "`n🚢 Step 5: Deploying to Heroku..." -ForegroundColor Yellow

$deployChoice = Read-Host "Deploy to Heroku? (y/n)"
if ($deployChoice -eq "y" -or $deployChoice -eq "Y") {
    Write-Host "Pushing to Heroku main branch..." -ForegroundColor Cyan
    git push heroku main
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push to Heroku" -ForegroundColor Red
        exit 1
    }
    
    # Step 6: Run migrations on Heroku
    Write-Host "`n🔄 Step 6: Running migrations on Heroku..." -ForegroundColor Yellow
    heroku run python manage.py migrate prompt_history
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to run migrations on Heroku" -ForegroundColor Red
        exit 1
    }
    
    # Step 7: Open the app
    Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
    Write-Host "`n📊 GraphQL Endpoints:" -ForegroundColor Cyan
    Write-Host "   GraphQL API: https://your-app.herokuapp.com/api/graphql/" -ForegroundColor White
    
    $openApp = Read-Host "`nOpen app in browser? (y/n)"
    if ($openApp -eq "y" -or $openApp -eq "Y") {
        heroku open
    }
    
    # Step 8: View logs
    $viewLogs = Read-Host "View deployment logs? (y/n)"
    if ($viewLogs -eq "y" -or $viewLogs -eq "Y") {
        heroku logs --tail
    }
    
} else {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    Write-Host "Changes committed locally. Run 'git push heroku main' when ready." -ForegroundColor Cyan
}

Write-Host "`n" + ("=" * 80) -ForegroundColor Gray
Write-Host "🎉 GraphQL System Ready!" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Test GraphQL endpoint at /api/graphql/" -ForegroundColor White
Write-Host "2. Review documentation in GRAPHQL_PROMPT_HISTORY.md" -ForegroundColor White
Write-Host "3. Integrate with frontend using Apollo Client" -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Gray
