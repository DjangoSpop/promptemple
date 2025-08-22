#!/usr/bin/env python
"""
Template Database Population and Testing Tool

This script offers a comprehensive solution to:
1. Populate the database with professional templates from JSON files
2. Test template-related API endpoints
3. Verify template data is correctly stored and accessible

Usage:
    python template_db_tool.py [action]
    
    Actions:
    - populate: Populate templates from JSON files
    - verify: Verify templates in database
    - test_api: Test template API endpoints
    - all: Run all actions (default)

Author: GitHub Copilot
Date: July 2, 2025
"""

import os
import sys
import json
import uuid
import django
import requests
from urllib.parse import urljoin
import argparse
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.templates.models import (
    Template, TemplateCategory, PromptField, TemplateField, FieldType
)

# Global constants
JSON_FILES = [
    'creative_templates.json',
    'software_templates.json',
    'advanced_storytelling_templates.json',
    'star_interview.json'
]

API_BASE_URL = "http://localhost:8000/api/"

User = get_user_model()

# Utility functions
def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️ {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️ {message}")

# Database population functions
def create_or_get_admin_user():
    """Create or get admin user for template creation"""
    try:
        admin_user = User.objects.get(username='admin')
        print_success(f"Using existing admin user: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@promptcraft.com',
            password='adminpassword123'
        )
        print_success(f"Created new admin user: {admin_user.username}")
    
    return admin_user

def create_template_categories():
    """Create template categories if they don't exist"""
    categories = {
        'Creative Writing': {
            'slug': 'creative-writing',
            'description': 'Templates for creative and narrative writing projects',
            'icon': 'pencil-alt',
            'color': '#6366F1'
        },
        'Software Development': {
            'slug': 'software-development',
            'description': 'Templates for coding, development and technical documentation',
            'icon': 'code',
            'color': '#2563EB'
        },
        'Career': {
            'slug': 'career',
            'description': 'Templates for job applications, interviews, and career growth',
            'icon': 'briefcase',
            'color': '#059669'
        },
        'Marketing': {
            'slug': 'marketing',
            'description': 'Templates for marketing content and campaigns',
            'icon': 'chart-pie',
            'color': '#DC2626'
        },
        'Academic': {
            'slug': 'academic',
            'description': 'Templates for essays, research papers, and academic writing',
            'icon': 'book-open',
            'color': '#7C3AED'
        }
    }
    
    created_categories = {}
    for name, details in categories.items():
        category, created = TemplateCategory.objects.update_or_create(
            name=name,
            defaults={
                'slug': details['slug'],
                'description': details['description'],
                'icon': details['icon'],
                'color': details['color']
            }
        )
        created_categories[name] = category
        if created:
            print_success(f"Created category: {name}")
        else:
            print_info(f"Updated existing category: {name}")
    
    return created_categories

def field_type_to_model_choice(field_type_str):
    """Convert field type string to model choice"""
    type_mapping = {
        'text': FieldType.TEXT,
        'textarea': FieldType.TEXTAREA,
        'dropdown': FieldType.DROPDOWN,
        'checkbox': FieldType.CHECKBOX,
        'radio': FieldType.RADIO,
        'number': FieldType.NUMBER
    }
    return type_mapping.get(field_type_str.lower(), FieldType.TEXT)

@transaction.atomic
def process_template(template_data, categories, admin_user):
    """Process a single template from JSON data"""
    try:
        # Get or determine the category
        category_name = template_data.get('category')
        category = categories.get(category_name)
        
        # If category doesn't exist, use the first available one
        if category is None:
            category = list(categories.values())[0]
            print_warning(f"Category '{category_name}' not found. Using '{category.name}' instead.")
        
        # Check if template already exists by title to avoid duplicates
        title = template_data.get('title')
        existing_template = Template.objects.filter(title=title).first()
        
        if existing_template:
            print_info(f"Template '{title}' already exists, skipping.")
            return
            
        # Create the template
        template = Template(
            id=uuid.uuid4(),  # Generate new UUID
            title=template_data.get('title', 'Untitled Template'),
            description=template_data.get('description', ''),
            category=category,
            template_content=template_data.get('templateContent', ''),
            author=admin_user,
            version=template_data.get('version', '1.0.0'),
            tags=template_data.get('tags', []),
            is_public=True,
            is_active=True,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        template.save()
        print_success(f"Created template: {template.title}")
        
        # Process fields
        fields_data = template_data.get('fields', [])
        for order, field_data in enumerate(fields_data):
            field = PromptField(
                id=uuid.uuid4(),  # Generate new UUID
                label=field_data.get('label', f'Field {order+1}'),
                placeholder=field_data.get('placeholder', ''),
                field_type=field_type_to_model_choice(field_data.get('type', 'text')),
                is_required=field_data.get('isRequired', False),
                default_value=field_data.get('defaultValue', ''),
                help_text=field_data.get('helpText', ''),
                options=field_data.get('options', []),
                order=order
            )
            field.save()
            
            # Create the association through the template_field model
            template_field = TemplateField(
                template=template,
                field=field,
                order=order
            )
            template_field.save()
            
            print_info(f"  Added field: {field.label} ({field.field_type})")
        
        return True
    
    except Exception as e:
        print_error(f"Error processing template '{template_data.get('title', 'Unknown')}': {e}")
        return False

def process_template_json(file_path, categories, admin_user):
    """Process a JSON file containing template data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_path.endswith('star_interview.json'):
                # Single template case
                data = json.load(file)
                templates_data = [data]
            else:
                # List of templates case
                templates_data = json.load(file)
        
        print_info(f"Processing {len(templates_data)} templates from {file_path}")
        
        success_count = 0
        for template_data in templates_data:
            # Handle the template
            if process_template(template_data, categories, admin_user):
                success_count += 1
            
        print_success(f"Successfully processed {success_count} out of {len(templates_data)} templates from {file_path}")
        
    except Exception as e:
        print_error(f"Error processing {file_path}: {e}")

def populate_templates():
    """Populate the database with templates from JSON files"""
    print_header("Populating Templates Database")
    
    # Create admin user
    admin_user = create_or_get_admin_user()
    
    # Create categories
    categories = create_template_categories()
    
    # Process each JSON file
    for json_file in JSON_FILES:
        print(f"\nProcessing {json_file}...")
        process_template_json(json_file, categories, admin_user)
    
    # Print summary
    template_count = Template.objects.count()
    field_count = PromptField.objects.count()
    category_count = TemplateCategory.objects.count()
    
    print("\nTemplate Population Complete!")
    print(f"Created/Updated:")
    print(f"- {category_count} Categories")
    print(f"- {template_count} Templates")
    print(f"- {field_count} Fields")

# Database verification functions
def verify_templates():
    """Verify templates in the database"""
    print_header("Database Verification")
    
    # Check categories
    categories = TemplateCategory.objects.all()
    print(f"Found {categories.count()} template categories:")
    
    for cat in categories:
        template_count = Template.objects.filter(category=cat).count()
        print(f"- {cat.name}: {template_count} templates")
    
    # Check templates
    templates = Template.objects.all().prefetch_related('fields')
    print(f"\nFound {templates.count()} templates:")
    
    for i, template in enumerate(templates[:10]):  # Show first 10
        field_count = template.fields.count()
        print(f"{i+1}. {template.title} ({template.category.name}) - {field_count} fields")
    
    if templates.count() > 10:
        print(f"... and {templates.count() - 10} more")
    
    # Check fields
    fields = PromptField.objects.all()
    print(f"\nFound {fields.count()} template fields")
    
    field_type_counts = {}
    for field in fields:
        field_type = field.get_field_type_display()
        field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1
    
    for field_type, count in field_type_counts.items():
        print(f"- {field_type}: {count}")
    
    # Sample a random template with fields
    if templates.exists():
        print("\nSample Template with Fields:")
        sample = templates.order_by('?').first()
        print(f"Title: {sample.title}")
        print(f"Description: {sample.description}")
        print(f"Category: {sample.category.name}")
        print(f"Author: {sample.author.username}")
        print("\nFields:")
        
        for i, field in enumerate(sample.fields.all().order_by('templatefield__order')):
            required = "Required" if field.is_required else "Optional"
            print(f"{i+1}. {field.label} ({field.get_field_type_display()}) - {required}")
            if field.placeholder:
                print(f"   Placeholder: {field.placeholder[:50]}...")
            if field.help_text:
                print(f"   Help: {field.help_text[:50]}...")
    
    return templates.count() > 0

# API testing functions
def test_api_endpoints(base_url=API_BASE_URL):
    """Test template API endpoints"""
    print_header("API Endpoint Testing")
    
    endpoints = [
        {"url": "templates/", "name": "Template List"},
        {"url": "template-categories/", "name": "Template Categories"},
        {"url": "templates/trending/", "name": "Trending Templates"},
        {"url": "templates/featured/", "name": "Featured Templates"}
    ]
    
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint["url"])
        print(f"\nTesting {endpoint['name']}...")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url)
            
            status_code = response.status_code
            if 200 <= status_code < 300:
                print_success(f"Status Code: {status_code}")
                
                data = response.json()
                if isinstance(data, list):
                    print_info(f"Returned {len(data)} items")
                    if data:
                        print(f"Sample: {json.dumps(data[0], indent=2)[:200]}...")
                elif isinstance(data, dict) and 'results' in data:
                    print_info(f"Returned {len(data.get('results', []))} items (of {data.get('count', 'unknown')} total)")
                    if data['results']:
                        print(f"Sample: {json.dumps(data['results'][0], indent=2)[:200]}...")
            else:
                print_error(f"Status Code: {status_code}")
                print(f"Response: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print_error("Connection Error. Is the server running?")
        except Exception as e:
            print_error(f"Error: {e}")
    
    # Try to get a specific template if available
    try:
        templates_response = requests.get(urljoin(base_url, "templates/"))
        if templates_response.status_code == 200:
            templates_data = templates_response.json()
            templates = templates_data.get('results', []) if isinstance(templates_data, dict) else templates_data
            
            if isinstance(templates, list) and len(templates) > 0:
                template_id = templates[0].get('id')
                if template_id:
                    print(f"\nTesting template detail...")
                    template_url = urljoin(base_url, f"templates/{template_id}/")
                    print(f"URL: {template_url}")
                    
                    detail_response = requests.get(template_url)
                    if detail_response.status_code == 200:
                        print_success(f"Status Code: {detail_response.status_code}")
                        detail_data = detail_response.json()
                        print_info(f"Title: {detail_data.get('title')}")
                        print_info(f"Fields: {len(detail_data.get('fields', []))}")
                    else:
                        print_error(f"Status Code: {detail_response.status_code}")
    except Exception as e:
        print_error(f"Error testing template detail: {e}")

def export_template_sample():
    """Export a sample template to JSON for verification"""
    print_header("Template Export Sample")
    
    try:
        # Get a random template
        template = Template.objects.order_by('?').first()
        
        if not template:
            print_warning("No templates found in database.")
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
        
        # Save to file
        filename = f"template_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(template_dict, f, indent=2)
        
        print_success(f"Sample template exported to {filename}")
    
    except Exception as e:
        print_error(f"Error exporting template: {e}")

def run_all_actions():
    """Run all actions in sequence"""
    populate_templates()
    verify_templates()
    test_api_endpoints()
    export_template_sample()

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Template Database Population and Testing Tool")
    parser.add_argument(
        'action', 
        nargs='?', 
        default='all', 
        choices=['populate', 'verify', 'test_api', 'all'],
        help='Action to perform (default: all)'
    )
    args = parser.parse_args()
    
    # Execute requested action
    if args.action == 'populate':
        populate_templates()
    elif args.action == 'verify':
        verify_templates()
    elif args.action == 'test_api':
        test_api_endpoints()
    else:  # all
        run_all_actions()
    
    print("\nOperation completed successfully!")

if __name__ == "__main__":
    main()
