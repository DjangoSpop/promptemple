#!/usr/bin/env python
"""
Database Connection Check

This script verifies the database connection and checks for template models/tables.

Usage:
    python check_db.py

Author: GitHub Copilot
Date: July 2, 2025
"""

import os
import sys
import django
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
django.setup()

from django.db import connection
from django.db.utils import OperationalError

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def check_template_tables():
    """Check for template-related tables"""
    print_header("Template Tables")
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%template%'")
        template_tables = [row[0] for row in cursor.fetchall()]
        
        if template_tables:
            print(f"Found {len(template_tables)} template tables:")
            for table in template_tables:
                print(f"- {table}")
        else:
            print("No template tables found. Have migrations been applied?")
        
        return template_tables
    except Exception as e:
        print(f"Error checking template tables: {e}")
        return []

def check_templates_table(template_tables):
    """Check details of the templates table"""
    if 'templates' in template_tables:
        print_header("Templates Table Details")
        
        try:
            cursor = connection.cursor()
            
            # Check author column
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'templates' 
                AND column_name = 'author_id'
            """)
            author_col_info = cursor.fetchall()
            print("Author column info:")
            for col_info in author_col_info:
                print(f"- Name: {col_info[0]}")
                print(f"- Type: {col_info[1]}")
                print(f"- Nullable: {col_info[2]}")
            
            # Check all columns
            print("\nAll columns in templates table:")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'templates' 
                ORDER BY ordinal_position
            """)
            all_cols = cursor.fetchall()
            for col in all_cols:
                print(f"- {col[0]}: {col[1]}")
                
            # Count rows
            cursor.execute("SELECT COUNT(*) FROM templates")
            count = cursor.fetchone()[0]
            print(f"\nTotal templates in database: {count}")
            
        except Exception as e:
            print(f"Error checking templates table: {e}")
    else:
        print("\ntemplates table not found. Have migrations been applied?")

def check_template_model():
    """Check the Template model in Django"""
    print_header("Django Template Model")
    
    try:
        from apps.templates.models import Template
        
        # Count templates
        template_count = Template.objects.count()
        print(f"Template objects in database: {template_count}")
        
        if template_count > 0:
            # Sample template
            first_template = Template.objects.first()
            print("\nSample template:")
            print(f"- ID: {first_template.id}")
            print(f"- Title: {first_template.title}")
            print(f"- Category: {first_template.category.name}")
            print(f"- Fields: {first_template.fields.count()}")
    except ImportError:
        print("Could not import the Template model. Check your project structure.")
    except OperationalError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error checking template model: {e}")

def check_template_categories():
    """Check template categories"""
    print_header("Template Categories")
    
    try:
        from apps.templates.models import TemplateCategory
        
        categories = TemplateCategory.objects.all()
        print(f"Found {categories.count()} template categories:")
        
        for cat in categories:
            template_count = cat.templates.count()
            print(f"- {cat.name}: {template_count} templates")
            
    except ImportError:
        print("Could not import the TemplateCategory model.")
    except OperationalError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error checking categories: {e}")

def main():
    """Main function"""
    print("Database Check Tool")
    print("==================")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Django Version: {django.get_version()}")
    
    # Check template tables
    template_tables = check_template_tables()
    
    # Check templates table details
    check_templates_table(template_tables)
    
    # Check Django models
    check_template_model()
    check_template_categories()
    
    print("\nDatabase check completed!")
    
    # Suggest next steps
    print("\nNext Steps:")
    print("1. Run 'python template_db_tool.py populate' to populate templates")
    print("2. Run 'python manage.py runserver' to start the development server")
    print("3. Visit http://localhost:8000/api/templates/ to see the templates API")

if __name__ == "__main__":
    main()
