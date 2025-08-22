#!/usr/bin/env python
"""
Template Population Script

This script populates the database with template data from JSON files.
It creates template categories and detailed templates with fields.

Usage:
    python populate_templates.py

Author: GitHub Copilot
Date: July 2, 2025
"""

import os
import json
import django
import uuid
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.templates.models import (
    Template, TemplateCategory, PromptField, TemplateField, FieldType
)

User = get_user_model()

# JSON template files to process
JSON_FILES = [
    'creative_templates.json',
    'software_templates.json',
    'advanced_storytelling_templates.json',
    'star_interview.json'
]

def create_or_get_admin_user():
    """Create or get admin user for template creation"""
    try:
        admin_user = User.objects.get(username='admin')
        print(f"Using existing admin user: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@promptcraft.com',
            password='adminpassword123'
        )
        print(f"Created new admin user: {admin_user.username}")
    
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
            print(f"Created category: {name}")
        else:
            print(f"Updated existing category: {name}")
    
    return created_categories

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
        
        print(f"Processing {len(templates_data)} templates from {file_path}")
        
        for template_data in templates_data:
            # Handle the template
            process_template(template_data, categories, admin_user)
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
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
            print(f"Warning: Category '{category_name}' not found. Using '{category.name}' instead.")
        
        # Check if template already exists by title to avoid duplicates
        title = template_data.get('title')
        existing_template = Template.objects.filter(title=title).first()
        
        if existing_template:
            print(f"Template '{title}' already exists, skipping.")
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
        print(f"Created template: {template.title}")
        
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
            
            print(f"  Added field: {field.label} ({field.field_type})")
    
    except Exception as e:
        print(f"Error processing template '{template_data.get('title', 'Unknown')}': {e}")
        raise e

def main():
    """Main function to run the template population process"""
    print("Starting template population...")
    
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

if __name__ == "__main__":
    main()
