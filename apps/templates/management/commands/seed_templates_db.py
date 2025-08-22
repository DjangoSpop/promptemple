from django.core.management.base import BaseCommand
from django.db import transaction
from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField
from django.contrib.auth import get_user_model
import json
import os
import uuid
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with template data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Specific JSON file to load (default: all files)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting template seeding process...')
        )

        if options['clear']:
            self.clear_existing_data()

        # Get the admin user or create one
        admin_user = self.get_or_create_admin()

        # Define JSON files to process
        json_files = self.get_json_files(options.get('file'))

        total_seeded = 0
        for json_file in json_files:
            seeded_count = self.process_json_file(json_file, admin_user)
            total_seeded += seeded_count

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully seeded {total_seeded} templates from {len(json_files)} files!'
            )
        )

    def clear_existing_data(self):
        """Clear existing template data"""
        self.stdout.write('🗑️ Clearing existing template data...')
        Template.objects.all().delete()
        TemplateCategory.objects.all().delete()
        PromptField.objects.all().delete()
        self.stdout.write(self.style.WARNING('Existing data cleared.'))

    def get_or_create_admin(self):
        """Get or create an admin user for authoring templates"""
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_user(
                    username='promptmaster',
                    email='admin@promptcraft.ai',
                    first_name='Prompt',
                    last_name='Master',
                    is_staff=True,
                    is_superuser=True,
                    credits=10000,
                    level=10,
                    user_rank='Prompt Overlord'
                )
                self.stdout.write(
                    self.style.SUCCESS('Created admin user: promptmaster')
                )
            return admin_user
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )
            raise

    def get_json_files(self, specific_file=None):
        """Get list of JSON files to process"""
        json_directory = settings.BASE_DIR
        
        if specific_file:
            return [os.path.join(json_directory, specific_file)]
        
        # Default JSON files to process
        default_files = [
            'advanced_storytelling_templates.json',
            'creative_templates.json',
            'software_templates.json',
            'star_interview.json',
        ]
        
        json_files = []
        for filename in default_files:
            filepath = os.path.join(json_directory, filename)
            if os.path.exists(filepath):
                json_files.append(filepath)
            else:
                self.stdout.write(
                    self.style.WARNING(f'File not found: {filename}')
                )
        
        return json_files

    @transaction.atomic
    def process_json_file(self, json_file, admin_user):
        """Process a single JSON file and create templates"""
        self.stdout.write(f'📁 Processing: {os.path.basename(json_file)}')
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single template and array of templates
            if isinstance(data, dict):
                templates_data = [data]
            else:
                templates_data = data
            
            seeded_count = 0
            for template_data in templates_data:
                if self.create_template(template_data, admin_user):
                    seeded_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Seeded {seeded_count} templates from {os.path.basename(json_file)}'
                )
            )
            return seeded_count
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing {json_file}: {e}')
            )
            return 0

    def create_template(self, template_data, admin_user):
        """Create a single template with its fields"""
        try:
            # Get or create category
            category_name = template_data.get('category', 'General')
            category, created = TemplateCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'slug': category_name.lower().replace(' ', '-'),
                    'description': f'Templates for {category_name}',
                    'color': self.get_category_color(category_name),
                    'icon': self.get_category_icon(category_name),
                }
            )
            
            if created:
                self.stdout.write(f'📂 Created category: {category_name}')
            
            # Check if template already exists by title and category
            if Template.objects.filter(
                title=template_data.get('title', 'Untitled Template'),
                category=category
            ).exists():
                self.stdout.write(
                    self.style.WARNING(f'Template "{template_data.get("title")}" already exists, skipping...')
                )
                return False

            # Create template with proper fields
            template = Template.objects.create(
                title=template_data.get('title', 'Untitled Template'),
                description=template_data.get('description', ''),
                category=category,
                template_content=template_data.get('templateContent', ''),
                author=admin_user,
                version=template_data.get('version', '1.0.0'),
                tags=template_data.get('tags', []),
                is_public=True,
                is_featured=self.is_featured_template(template_data)
            )

            # Create and associate fields
            fields_data = template_data.get('fields', [])
            for order, field_data in enumerate(fields_data):
                self.create_template_field(template, field_data, order)

            self.stdout.write(f'✨ Created template: {template.title}')
            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating template {template_data.get("title", "Unknown")}: {e}')
            )
            return False

    def create_template_field(self, template, field_data, order):
        """Create a prompt field and associate it with the template"""
        try:
            # Create the prompt field
            field = PromptField.objects.create(
                label=field_data.get('label', 'Unnamed Field'),
                placeholder=field_data.get('placeholder', ''),
                field_type=field_data.get('type', 'text'),
                is_required=field_data.get('isRequired', False),
                default_value=field_data.get('defaultValue', ''),
                help_text=field_data.get('helpText', ''),
                options=field_data.get('options', []),
                order=order
            )

            # Create the through model relationship
            TemplateField.objects.create(
                template=template,
                field=field,
                order=order
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating field {field_data.get("label", "Unknown")}: {e}')
            )

    def get_category_color(self, category_name):
        """Get color for category based on name"""
        color_map = {
            'Creative Writing': '#FF6B6B',
            'Software Development': '#4ECDC4',
            'Marketing': '#45B7D1',
            'Business': '#96CEB4',
            'Career': '#FECA57',
            'General': '#6C5CE7',
            'Productivity': '#A29BFE',
            'Education': '#FD79A8',
            'Health & Wellness': '#00B894',
            'Finance': '#FDCB6E',
        }
        return color_map.get(category_name, '#6366F1')

    def get_category_icon(self, category_name):
        """Get icon for category based on name"""
        icon_map = {
            'Creative Writing': '✍️',
            'Software Development': '💻',
            'Marketing': '📈',
            'Business': '💼',
            'Career': '🎯',
            'General': '⭐',
            'Productivity': '⚡',
            'Education': '🎓',
            'Health & Wellness': '🌿',
            'Finance': '💰',
        }
        return icon_map.get(category_name, '📄')

    def is_featured_template(self, template_data):
        """Determine if template should be featured"""
        # Feature templates that are marked as version 2.0+ or have specific tags
        version = template_data.get('version', '1.0.0')
        tags = template_data.get('tags', [])
        
        return (
            version.startswith('2.') or 
            'featured' in tags or 
            'premium' in tags or
            'monetization' in tags
        )