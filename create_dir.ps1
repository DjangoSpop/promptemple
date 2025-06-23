# PowerShell script to create directories
param (
    [string]$Path = "."
)

# Function to create a directory if it doesn't exist
function New-DirectoryIfNotExists {
    param (
        [string]$Path
    )
    
    if (-not (Test-Path -Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
        Write-Host "Created directory: $Path" -ForegroundColor Green
    } else {
        Write-Host "Directory already exists: $Path" -ForegroundColor Yellow
    }
}

# Create Django app structure directories for a new app
function New-DjangoAppStructure {
    param (
        [string]$AppName
    )
    
    $basePath = Join-Path -Path $Path -ChildPath "apps\$AppName"
    
    # Create main app directory
    New-DirectoryIfNotExists -Path $basePath
    
    # Create standard Django app directories
    $directories = @(
        "",
        "migrations",
        "management",
        "management\commands",
        "templates",
        "templates\$AppName",
        "static",
        "static\$AppName",
        "static\$AppName\css",
        "static\$AppName\js",
        "templatetags",
        "tests",
        "fixtures"
    )
    
    foreach ($dir in $directories) {
        $dirPath = if ($dir -eq "") { $basePath } else { Join-Path -Path $basePath -ChildPath $dir }
        New-DirectoryIfNotExists -Path $dirPath
    }
    
    # Create standard Django app files
    $files = @{
        "__init__.py" = "# $AppName app initialization";
        "admin.py" = "from django.contrib import admin`n`n# Register your models here`n";
        "apps.py" = "from django.apps import AppConfig`n`n`nclass $(($AppName.Substring(0,1).ToUpper() + $AppName.Substring(1)))Config(AppConfig):`n    default_auto_field = 'django.db.models.BigAutoField'`n    name = 'apps.$AppName'`n    verbose_name = '$(($AppName.Substring(0,1).ToUpper() + $AppName.Substring(1)))'`n";
        "models.py" = "from django.db import models`n`n# Create your models here`n";
        "views.py" = "from django.shortcuts import render`n`n# Create your views here`n";
        "urls.py" = "from django.urls import path`nfrom . import views`n`nurlpatterns = [`n    # Add URL patterns here`n]`n";
        "serializers.py" = "from rest_framework import serializers`n`n# Create your serializers here`n";
        "services.py" = "# Service layer for $AppName app`n`n# Create your services here`n";
        "management\__init__.py" = "# Management commands initialization";
        "management\commands\__init__.py" = "# Commands initialization";
        "migrations\__init__.py" = "# Migrations initialization";
        "templatetags\__init__.py" = "# Template tags initialization";
        "tests\__init__.py" = "# Tests initialization";
        "tests\test_models.py" = "from django.test import TestCase`n`n# Create your model tests here`n";
        "tests\test_views.py" = "from django.test import TestCase`n`n# Create your view tests here`n";
    }
    
    foreach ($file in $files.Keys) {
        $filePath = Join-Path -Path $basePath -ChildPath $file
        if (-not (Test-Path -Path $filePath)) {
            $content = $files[$file]
            Set-Content -Path $filePath -Value $content
            Write-Host "Created file: $filePath" -ForegroundColor Green
        } else {
            Write-Host "File already exists: $filePath" -ForegroundColor Yellow
        }
    }
    
    Write-Host "Django app structure for '$AppName' created successfully" -ForegroundColor Cyan
}

# Check if an app name was provided via command line argument
$appNames = $args
if ($appNames.Count -gt 0) {
    foreach ($appName in $appNames) {
        New-DjangoAppStructure -AppName $appName
    }
} else {
    Write-Host "Usage: .\create_dir.ps1 [app_name1] [app_name2] ..." -ForegroundColor Yellow
    Write-Host "Example: .\create_dir.ps1 users templates" -ForegroundColor Yellow
}
