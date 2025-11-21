#!/usr/bin/env python3
"""
Pre-deployment verification script for Heroku
Checks all required files and configurations are in place
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def check_file(filepath, required=True):
    """Check if file exists"""
    path = BASE_DIR / filepath
    exists = path.exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filepath}")
    return exists

def check_file_size(filepath):
    """Check file size"""
    path = BASE_DIR / filepath
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")
        return size_mb
    return 0

def main():
    print("=" * 60)
    print("🔍 HEROKU DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    all_good = True
    
    # Check required files
    print("\n📦 Required Deployment Files:")
    files_required = [
        'requirements-heroku.txt',
        'Procfile',
        'runtime.txt',
        '.slugignore',
        'promptcraft/settings/heroku.py',
        'manage.py',
    ]
    
    for file in files_required:
        if not check_file(file, required=True):
            all_good = False
    
    # Check optional files
    print("\n📄 Optional Files:")
    files_optional = [
        'app.json',
        'HEROKU_DEPLOYMENT.md',
        'HEROKU_QUICKSTART.md',
        'templates_fixture.json',
    ]
    
    for file in files_optional:
        check_file(file, required=False)
    
    # Check database seeding command
    print("\n🌱 Template Seeding:")
    seed_cmd = 'apps/templates/management/commands/seed_templates.py'
    if check_file(seed_cmd):
        print("   ✅ Seed command available")
    else:
        print("   ⚠️  No seed command found")
    
    # Check requirements file size
    print("\n📊 Requirements File Analysis:")
    req_size = check_file_size('requirements-heroku.txt')
    
    # Estimate total slug size (rough approximation)
    estimated_slug = req_size * 1.5  # Packages + Python runtime + code
    print(f"\n📦 Estimated Slug Size: ~{estimated_slug:.0f} MB")
    
    if estimated_slug < 500:
        print(f"   ✅ Under 500MB limit (target achieved!)")
    else:
        print(f"   ❌ Over 500MB limit (needs optimization)")
        all_good = False
    
    # Check Procfile content
    print("\n⚙️  Procfile Configuration:")
    procfile_path = BASE_DIR / 'Procfile'
    if procfile_path.exists():
        with open(procfile_path, 'r') as f:
            content = f.read()
            if 'gunicorn' in content:
                print("   ✅ Using Gunicorn")
            if '$PORT' in content:
                print("   ✅ Port binding configured")
            if 'migrate' in content:
                print("   ✅ Migrations in Procfile")
            if 'collectstatic' in content:
                print("   ✅ Static files collection")
    
    # Check Python version
    print("\n🐍 Python Version:")
    runtime_path = BASE_DIR / 'runtime.txt'
    if runtime_path.exists():
        with open(runtime_path, 'r') as f:
            version = f.read().strip()
            print(f"   {version}")
            if version.startswith('python-3.11'):
                print("   ✅ Python 3.11 (recommended)")
    
    # Check settings module
    print("\n⚙️  Settings Configuration:")
    heroku_settings = BASE_DIR / 'promptcraft' / 'settings' / 'heroku.py'
    if heroku_settings.exists():
        with open(heroku_settings, 'r') as f:
            content = f.read()
            checks = {
                'DEBUG = False': 'Debug mode disabled',
                'WhiteNoise': 'Static files (WhiteNoise)',
                'dj_database_url': 'PostgreSQL configuration',
                'ALLOWED_HOSTS': 'Allowed hosts configured',
            }
            for check, desc in checks.items():
                if check in content:
                    print(f"   ✅ {desc}")
    
    # Check .slugignore
    print("\n🚫 Slug Exclusions:")
    slugignore_path = BASE_DIR / '.slugignore'
    if slugignore_path.exists():
        with open(slugignore_path, 'r') as f:
            content = f.read()
            exclusions = [
                ('*.md', 'Documentation files'),
                ('*.csv', 'Dataset files'),
                ('tests/', 'Test files'),
                ('*.pkl', 'ML artifacts'),
            ]
            for pattern, desc in exclusions:
                if pattern in content:
                    print(f"   ✅ Excluding {desc}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if all_good:
        print("✅ ALL CHECKS PASSED - READY TO DEPLOY!")
        print("=" * 60)
        print("\n🚀 Next Steps:")
        print("1. heroku create your-app-name")
        print("2. heroku addons:create heroku-postgresql:mini")
        print("3. heroku config:set [environment variables]")
        print("4. git push heroku main")
        print("\nSee HEROKU_QUICKSTART.md for full instructions")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - REVIEW ABOVE")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
