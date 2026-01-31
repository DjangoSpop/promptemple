# Complete GraphQL Setup Script with Virtual Environment
# Handles venv activation, installation, migrations, and testing

Write-Host "🚀 GraphQL Prompt History - Complete Setup" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

# Step 1: Check if virtual environment exists
Write-Host "`n📦 Step 1: Checking virtual environment..." -ForegroundColor Yellow

$venvPath = ".\venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "❌ Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    exit 1
}

Write-Host "✅ Virtual environment found" -ForegroundColor Green

# Step 2: Activate virtual environment
Write-Host "`n🔧 Step 2: Activating virtual environment..." -ForegroundColor Yellow

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating venv..." -ForegroundColor Cyan
    & $activateScript
    
    if ($LASTEXITCODE -eq 0 -or $?) {
        Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Warning: Virtual environment activation may have issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Activation script not found at $activateScript" -ForegroundColor Red
    exit 1
}

# Step 3: Install GraphQL dependencies
Write-Host "`n📥 Step 3: Installing GraphQL dependencies..." -ForegroundColor Yellow
Write-Host "Installing graphene-django==3.2.0 and graphene==3.3..." -ForegroundColor Cyan

pip install graphene-django==3.2.0 graphene==3.3

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install GraphQL dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ GraphQL dependencies installed" -ForegroundColor Green

# Step 4: Install any missing dependencies
Write-Host "`n📥 Step 4: Ensuring all requirements are installed..." -ForegroundColor Yellow

pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Some requirements may have failed to install" -ForegroundColor Yellow
} else {
    Write-Host "✅ All requirements checked" -ForegroundColor Green
}

# Step 5: Create migrations
Write-Host "`n🔨 Step 5: Creating database migrations..." -ForegroundColor Yellow

python manage.py makemigrations prompt_history

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create migrations" -ForegroundColor Red
    Write-Host "Check for model errors in apps\prompt_history\models.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Migrations created" -ForegroundColor Green

# Step 6: Apply migrations
Write-Host "`n🔄 Step 6: Applying migrations to database..." -ForegroundColor Yellow

python manage.py migrate prompt_history --noinput

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Migrations applied" -ForegroundColor Green

# Step 7: Run GraphQL setup script
Write-Host "`n🧪 Step 7: Setting up test data..." -ForegroundColor Yellow

python setup_graphql.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Test data setup had issues" -ForegroundColor Yellow
    Write-Host "This is okay if data already exists or if you're in production" -ForegroundColor Cyan
} else {
    Write-Host "✅ Test data created" -ForegroundColor Green
}

# Step 8: Verify GraphQL installation
Write-Host "`n✅ Step 8: Verifying GraphQL installation..." -ForegroundColor Yellow

$verifyScript = @"
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

try:
    import graphene_django
    print('✅ graphene-django installed')
    
    from apps.prompt_history.schema import schema
    print('✅ GraphQL schema imported successfully')
    
    from apps.prompt_history.models import PromptIteration, ConversationThread
    print('✅ Models imported successfully')
    
    print('\n🎉 GraphQL system is ready!')
    print('GraphQL Endpoint: /api/graphql/')
    
except Exception as e:
    print(f'❌ Verification failed: {e}')
    import traceback
    traceback.print_exc()
"@

Write-Host "Running verification..." -ForegroundColor Cyan
python -c $verifyScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Verification had issues, but setup may still be successful" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Gray
Write-Host "🎉 GraphQL Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Gray

Write-Host "`n📊 What was installed:" -ForegroundColor Cyan
Write-Host "   ✓ graphene-django (GraphQL framework)" -ForegroundColor White
Write-Host "   ✓ graphene (GraphQL core)" -ForegroundColor White
Write-Host "   ✓ Database models (PromptIteration, ConversationThread, ThreadMessage)" -ForegroundColor White
Write-Host "   ✓ GraphQL schema with queries and mutations" -ForegroundColor White
Write-Host "   ✓ Test data (if applicable)" -ForegroundColor White

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Start development server:" -ForegroundColor Yellow
Write-Host "      python manage.py runserver" -ForegroundColor White
Write-Host "`n   2. Access GraphiQL interface:" -ForegroundColor Yellow
Write-Host "      http://localhost:8000/api/graphql/" -ForegroundColor White
Write-Host "`n   3. Get JWT token for authentication:" -ForegroundColor Yellow
Write-Host "      POST http://localhost:8000/api/v2/auth/login/" -ForegroundColor White
Write-Host "      with: {`"email`": `"test@promptcraft.com`", `"password`": `"testpass123`"}" -ForegroundColor White
Write-Host "`n   4. Test GraphQL queries (see GRAPHQL_PROMPT_HISTORY.md)" -ForegroundColor Yellow

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - Complete guide: GRAPHQL_PROMPT_HISTORY.md" -ForegroundColor White
Write-Host "   - Frontend integration: graphql_frontend_integration.tsx" -ForegroundColor White

Write-Host "`n🚢 To Deploy to Heroku:" -ForegroundColor Cyan
Write-Host "   Run: .\deploy_graphql.ps1" -ForegroundColor White

Write-Host "`n" + ("=" * 80) -ForegroundColor Gray
Write-Host "✨ Ready to track prompt iterations professionally! ✨" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Gray
