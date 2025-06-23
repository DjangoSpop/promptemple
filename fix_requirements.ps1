# PowerShell script to fix requirements naming issue

# Paths for the files
$CorrectFile = Join-Path -Path $PSScriptRoot -ChildPath "requirements.txt"
$MisspelledFile = Join-Path -Path $PSScriptRoot -ChildPath "requirments.txt"

# Check if the misspelled file exists and the correct file doesn't
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

Write-Host "Process completed" -ForegroundColor Green
