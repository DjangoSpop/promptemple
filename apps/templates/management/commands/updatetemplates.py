"""
Update Templates Database

This script acts as a management command to update the template database.
It loads templates from JSON files into the database and ensures they're
available through the API.

Usage:
    python manage.py updatetemplates

Author: GitHub Copilot
Date: July 2, 2025
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
import os
import json
import uuid

from apps.templates.models import (
    Template, TemplateCategory, PromptField, TemplateField, FieldType
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Updates the template database from JSON files'

    # JSON template files to process
    JSON_FILES = [
        'creative_templates.json',
        'software_templates.json',
        'advanced_storytelling_templates.json',
        'star_interview.json'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Force update of existing templates',
        )

    def handle(self, *args, **options):
        self.force = options['force']
        self.verbosity = options['verbosity']
        self.style.SUCCESS('Starting template database update...')
        
        # Create admin user
        admin_user = self.create_or_get_admin_user()
        
        # Create categories
        categories = self.create_template_categories()
        
        # Process each JSON file
        templates_created = 0
        templates_updated = 0
        templates_skipped = 0
        
        for json_file in self.JSON_FILES:
            file_path = os.path.join(os.getcwd(), json_file)
            if os.path.exists(file_path):
                result = self.process_template_json(file_path, categories, admin_user)
                templates_created += result['created']
                templates_updated += result['updated']
                templates_skipped += result['skipped']
            else:
                self.stdout.write(self.style.WARNING(f'File not found: {json_file}'))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Templates created: {templates_created}'))
        self.stdout.write(self.style.SUCCESS(f'Templates updated: {templates_updated}'))
        self.stdout.write(self.style.SUCCESS(f'Templates skipped: {templates_skipped}'))
        
        template_count = Template.objects.count()
        field_count = PromptField.objects.count()
        category_count = TemplateCategory.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'Total in database: {template_count} templates, {field_count} fields, {category_count} categories'))
        
    def create_or_get_admin_user(self):
        """Create or get admin user for template creation"""
        try:
            admin_user = User.objects.get(username='admin')
            if self.verbosity >= 2:
                self.stdout.write(self.style.SUCCESS(f"Using existing admin user: {admin_user.username}"))
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@promptcraft.com',
                password='adminpassword123'
            )
            self.stdout.write(self.style.SUCCESS(f"Created new admin user: {admin_user.username}"))
        
        return admin_user

    def create_template_categories(self):
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
            if created and self.verbosity >= 2:
                self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))
        
        return created_categories

    def field_type_to_model_choice(self, field_type_str):
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

    def process_template_json(self, file_path, categories, admin_user):
        """Process a JSON file containing template data"""
        result = {'created': 0, 'updated': 0, 'skipped': 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_path.endswith('star_interview.json'):
                    # Single template case
                    data = json.load(file)
                    templates_data = [data]
                else:
                    # List of templates case
                    templates_data = json.load(file)
            
            if self.verbosity >= 1:
                self.stdout.write(f"Processing {len(templates_data)} templates from {os.path.basename(file_path)}")
            
            for template_data in templates_data:
                # Handle the template
                status = self.process_template(template_data, categories, admin_user)
                result[status] += 1
                
            return result
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {file_path}: {e}"))
            return result

    @transaction.atomic
    def process_template(self, template_data, categories, admin_user):
        """Process a single template from JSON data"""
        try:
            # Get or determine the category
            category_name = template_data.get('category')
            category = categories.get(category_name)
            
            # If category doesn't exist, use the first available one
            if category is None:
                category = list(categories.values())[0]
                if self.verbosity >= 2:
                    self.stdout.write(self.style.WARNING(f"Category '{category_name}' not found. Using '{category.name}' instead."))
            
            # Check if template already exists by title to avoid duplicates
            title = template_data.get('title')
            existing_template = Template.objects.filter(title=title).first()
            
            if existing_template and not self.force:
                if self.verbosity >= 2:
                    self.stdout.write(f"Template '{title}' already exists, skipping.")
                return 'skipped'
                
            # Create or update the template
            if existing_template and self.force:
                template = existing_template
                template.description = template_data.get('description', '')
                template.category = category
                template.template_content = template_data.get('templateContent', '')
                template.version = template_data.get('version', '1.0.0')
                template.tags = template_data.get('tags', [])
                template.updated_at = timezone.now()
                template.save()
                
                # Clear existing fields
                template.fields.clear()
                
                if self.verbosity >= 1:
                    self.stdout.write(self.style.SUCCESS(f"Updated template: {template.title}"))
                status = 'updated'
            else:
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
                if self.verbosity >= 1:
                    self.stdout.write(self.style.SUCCESS(f"Created template: {template.title}"))
                status = 'created'
            
            # Process fields
            fields_data = template_data.get('fields', [])
            for order, field_data in enumerate(fields_data):
                field = PromptField(
                    id=uuid.uuid4(),  # Generate new UUID
                    label=field_data.get('label', f'Field {order+1}'),
                    placeholder=field_data.get('placeholder', ''),
                    field_type=self.field_type_to_model_choice(field_data.get('type', 'text')),
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
                
                if self.verbosity >= 3:
                    self.stdout.write(f"  Added field: {field.label} ({field.field_type})")
            
            return status
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing template '{template_data.get('title', 'Unknown')}': {e}"))
            raise e
