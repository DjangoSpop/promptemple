# PowerShell script to fix requirements and ensure all needed packages are installed
Write-Host "PromptCraft Backend - Requirements Fix Tool" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Fix misspelled requirements file
Write-Host "`nStep 1: Fixing misspelled requirements file" -ForegroundColor Green
$CorrectFile = Join-Path -Path $PSScriptRoot -ChildPath "requirements.txt"
$MisspelledFile = Join-Path -Path $PSScriptRoot -ChildPath "requirments.txt"

if (Test-Path -Path $MisspelledFile) {
    Write-Host "Found misspelled requirements file" -ForegroundColor Yellow
    
    # If the correct file doesn't exist, rename the misspelled file
    if (-not (Test-Path -Path $CorrectFile)) {
        Copy-Item -Path $MisspelledFile -Destination $CorrectFile
        Write-Host "Created correctly spelled requirements.txt file" -ForegroundColor Green
    } else {
        # If both exist, check if they're different
        $misspelledContent = Get-Content -Path $MisspelledFile -Raw
        $correctContent = Get-Content -Path $CorrectFile -Raw
        
        if ($misspelledContent -ne $correctContent) {
            Write-Host "Both files exist and have different content" -ForegroundColor Yellow
            Write-Host "Please review both files manually to ensure no data is lost" -ForegroundColor Yellow
            Write-Host "requirments.txt (misspelled): $MisspelledFile" -ForegroundColor Cyan
            Write-Host "requirements.txt (correct): $CorrectFile" -ForegroundColor Cyan
        } else {
            Write-Host "Both files exist with identical content" -ForegroundColor Green
        }
    }
    
    # Update Dockerfile to use the correct filename
    $DockerfilePath = Join-Path -Path $PSScriptRoot -ChildPath "Dockerfile"
    if (Test-Path -Path $DockerfilePath) {
        $DockerfileContent = Get-Content -Path $DockerfilePath -Raw
        
        # Check if Dockerfile references the misspelled file
        if ($DockerfileContent -match "requirments\.txt") {
            $UpdatedContent = $DockerfileContent -replace "requirments\.txt", "requirements.txt"
            Set-Content -Path $DockerfilePath -Value $UpdatedContent
            Write-Host "Updated Dockerfile to use the correct requirements.txt filename" -ForegroundColor Green
        }
    }
} else {
    Write-Host "No misspelled requirements file found" -ForegroundColor Green
}

# 2. Check and add missing packages for template functionality
Write-Host "`nStep 2: Ensuring required packages are in requirements.txt" -ForegroundColor Green
$RequiredPackages = @(
    "requests>=2.31.0",
    "tabulate>=0.9.0",
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
    "python-dateutil>=2.8.2",
    "uuid>=1.30"
)

$CurrentRequirements = Get-Content -Path $CorrectFile

foreach ($package in $RequiredPackages) {
    $packageName = $package.Split(">=")[0].Trim()
    $packageFound = $false
    
    foreach ($line in $CurrentRequirements) {
        if ($line.StartsWith("$packageName==") -or $line.StartsWith("$packageName>=")) {
            $packageFound = $true
            break
        }
    }
    
    if (-not $packageFound) {
        Write-Host "Adding missing package: $package" -ForegroundColor Yellow
        Add-Content -Path $CorrectFile -Value $package
    } else {
        Write-Host "Package already exists: $packageName" -ForegroundColor Green
    }
}

# 3. Install all requirements
Write-Host "`nStep 3: Installing all requirements" -ForegroundColor Green
$InstallConfirmation = Read-Host "Would you like to install all requirements now? (y/n)"
if ($InstallConfirmation -eq "y") {
    Write-Host "Installing requirements..." -ForegroundColor Yellow
    try {
        & pip install -r $CorrectFile
        Write-Host "All requirements installed successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Error installing requirements: $_" -ForegroundColor Red
        Write-Host "Please try installing them manually with: pip install -r requirements.txt" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping installation. You can install requirements manually with:" -ForegroundColor Yellow
    Write-Host "pip install -r requirements.txt" -ForegroundColor Cyan
}

# 4. Next steps
Write-Host "`nNext Steps:" -ForegroundColor Green
Write-Host "1. Make sure your database is configured correctly" -ForegroundColor Cyan
Write-Host "2. Run migrations if needed: python manage.py migrate" -ForegroundColor Cyan
Write-Host "3. Run template population script: python template_db_tool.py populate" -ForegroundColor Cyan
Write-Host "4. Start development server: python manage.py runserver" -ForegroundColor Cyan

Write-Host "`nProcess completed!" -ForegroundColor Green
