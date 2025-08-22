#!/usr/bin/env python
"""
Template Verification Script

This script verifies that templates have been properly populated in the database
and tests the API endpoints to ensure they're working correctly.

Usage:
    python verify_templates.py

Author: GitHub Copilot
Date: July 2, 2025
"""

import os
import django
import json
import requests
from tabulate import tabulate
from django.core.serializers import serialize
from django.db.models import Count

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.templates.models import (
    Template, TemplateCategory, PromptField, TemplateField
)

def print_section_header(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def check_database():
    """Check the database for populated templates"""
    print_section_header("Database Verification")
    
    # Check categories
    categories = TemplateCategory.objects.all()
    print(f"Found {categories.count()} template categories:")
    
    category_data = []
    for cat in categories:
        template_count = Template.objects.filter(category=cat).count()
        category_data.append([cat.id, cat.name, cat.slug, template_count])
    
    print(tabulate(
        category_data, 
        headers=["ID", "Name", "Slug", "Template Count"],
        tablefmt="pretty"
    ))
    
    # Check templates
    templates = Template.objects.all().prefetch_related('fields')
    print(f"\nFound {templates.count()} templates:")
    
    template_data = []
    for template in templates:
        field_count = template.fields.count()
        template_data.append([
            str(template.id)[:8] + "...", 
            template.title[:30] + ("..." if len(template.title) > 30 else ""),
            template.category.name,
            field_count,
            "Yes" if template.is_public else "No",
            template.created_at.strftime("%Y-%m-%d")
        ])
    
    print(tabulate(
        template_data,
        headers=["ID", "Title", "Category", "Fields", "Public", "Created"],
        tablefmt="pretty"
    ))
    
    # Check fields
    fields = PromptField.objects.all()
    print(f"\nFound {fields.count()} template fields")
    
    field_type_counts = {}
    for field in fields:
        field_type = field.get_field_type_display()
        field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1
    
    field_type_data = [[field_type, count] for field_type, count in field_type_counts.items()]
    print(tabulate(
        field_type_data,
        headers=["Field Type", "Count"],
        tablefmt="pretty"
    ))
    
    # Sample a random template with fields
    if templates.exists():
        print("\nSample Template with Fields:")
        sample = templates.order_by('?').first()
        print(f"Title: {sample.title}")
        print(f"Description: {sample.description}")
        print(f"Category: {sample.category.name}")
        print(f"Author: {sample.author.username}")
        print("\nFields:")
        
        field_data = []
        for i, field in enumerate(sample.fields.all().order_by('templatefield__order')):
            field_data.append([
                i+1, 
                field.label, 
                field.get_field_type_display(),
                "Required" if field.is_required else "Optional",
                field.placeholder[:30] + ("..." if len(field.placeholder) > 30 else "") if field.placeholder else ""
            ])
        
        print(tabulate(
            field_data,
            headers=["#", "Label", "Type", "Required", "Placeholder"],
            tablefmt="pretty"
        ))
    
    return templates.count() > 0

def test_api_endpoints(base_url="http://localhost:8000/api/"):
    """Test API endpoints to ensure they're working correctly"""
    print_section_header("API Endpoint Testing")
    
    endpoints = [
        {"url": "templates/", "name": "Template List"},
        {"url": "template-categories/", "name": "Template Categories"},
        {"url": "templates/trending/", "name": "Trending Templates"},
        {"url": "templates/featured/", "name": "Featured Templates"}
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint['url']}"
        try:
            response = requests.get(url)
            
            status_code = response.status_code
            success = 200 <= status_code < 300
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    item_count = len(data)
                elif isinstance(data, dict) and 'results' in data:
                    item_count = len(data.get('results', []))
                else:
                    item_count = "N/A"
            else:
                item_count = "Error"
            
            results.append([
                endpoint["name"],
                url,
                status_code,
                "✓" if success else "✗",
                item_count
            ])
        except Exception as e:
            results.append([
                endpoint["name"],
                url,
                "Error",
                "✗",
                str(e)
            ])
    
    print(tabulate(
        results,
        headers=["Endpoint", "URL", "Status", "Success", "Items"],
        tablefmt="pretty"
    ))

def export_template_sample():
    """Export a sample template to JSON for verification"""
    print_section_header("Template Export Sample")
    
    try:
        # Get a random template
        template = Template.objects.order_by('?').first()
        
        if not template:
            print("No templates found in database.")
            return
        
        # Create a simplified dictionary representation
        template_dict = {
            "id": str(template.id),
            "title": template.title,
            "description": template.description,
            "category": template.category.name,
            "author": template.author.username,
            "version": template.version,
            "tags": template.tags,
            "created_at": template.created_at.isoformat(),
            "template_content": template.template_content,
            "fields": []
        }
        
        # Add fields
        for tf in TemplateField.objects.filter(template=template).order_by('order'):
            field = tf.field
            template_dict["fields"].append({
                "id": str(field.id),
                "label": field.label,
                "placeholder": field.placeholder,
                "field_type": field.field_type,
                "is_required": field.is_required,
                "default_value": field.default_value,
                "help_text": field.help_text,
                "options": field.options
            })
        
        # Print as formatted JSON
        print(json.dumps(template_dict, indent=2))
        
        # Save to file
        with open('template_sample.json', 'w') as f:
            json.dump(template_dict, f, indent=2)
        
        print("\nSample template exported to template_sample.json")
    
    except Exception as e:
        print(f"Error exporting template: {e}")

def main():
    """Main function to verify templates"""
    print("Template Verification Tool")
    print("=========================\n")
    
    # Check database
    database_ok = check_database()
    
    if not database_ok:
        print("\nWarning: No templates found in database!")
        print("Please run populate_templates.py first.")
        return
    
    # Try to test API endpoints
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"\nCould not test API endpoints: {e}")
        print("Make sure the development server is running with 'python manage.py runserver'")
    
    # Export a sample template
    export_template_sample()
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()
