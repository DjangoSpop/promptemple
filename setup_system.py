#!/usr/bin/env python3
"""
Quick Setup Script for PromptCraft Template System
This script sets up the complete template management system.
"""

import os
import sys
import subprocess
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

def run_command(command, description):
    """Run a command and print the result."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False
    return True

def create_sample_data():
    """Create sample data for testing."""
    print("🔄 Creating sample data...")
    
    try:
        from apps.templates.models import TemplateCategory, Template
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create categories
        categories = [
            ('Business', 'business', 'Business templates for entrepreneurs'),
            ('Marketing', 'marketing', 'Marketing and advertising templates'),
            ('Technology', 'technology', 'Technical and software templates'),
            ('Content', 'content', 'Content creation templates'),
            ('Sales', 'sales', 'Sales and conversion templates'),
        ]
        
        for name, slug, desc in categories:
            category, created = TemplateCategory.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc}
            )
            if created:
                print(f"   Created category: {name}")
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@promptcraft.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print("   Created admin user (username: admin, password: admin123)")
        
        print("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def check_system_status():
    """Check the status of the system."""
    print("\n📊 System Status Check:")
    
    try:
        from apps.templates.models import Template, TemplateCategory
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        print(f"   📁 Templates: {Template.objects.count()}")
        print(f"   📂 Categories: {TemplateCategory.objects.count()}")
        print(f"   👥 Users: {User.objects.count()}")
        print(f"   👑 Admin Users: {User.objects.filter(is_superuser=True).count()}")
        
        # Check if required files exist
        required_files = [
            'apps/templates/services/md_ingestion_service.py',
            'apps/templates/services/suggestion_service.py',
            'apps/templates/admin.py',
            'apps/templates/api_views.py',
        ]
        
        print("\n   📁 Required Files:")
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 PromptCraft Template System Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the Django project root.")
        return
    
    steps = [
        ("python manage.py makemigrations", "Creating database migrations"),
        ("python manage.py migrate", "Applying database migrations"),
    ]
    
    # Run setup steps
    for command, description in steps:
        if not run_command(command, description):
            print("❌ Setup failed. Please check the errors above.")
            return
    
    # Create sample data
    if not create_sample_data():
        print("❌ Failed to create sample data.")
        return
    
    # Check system status
    check_system_status()
    
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Access admin panel: http://localhost:8000/admin/")
    print("3. Test ingestion: python test_ingestion.py")
    print("4. Try API endpoints: http://localhost:8000/api/templates/")
    print("\nAdmin credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("\n📖 Full documentation: TEMPLATE_SYSTEM_DOCS.md")

if __name__ == "__main__":
    main()