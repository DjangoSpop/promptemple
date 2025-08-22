"""
Django Management Command: Seed Prompt Library

This command processes the top-1000-prompts-library.json file and populates
the database with comprehensive prompt data including categories, templates,
and performance metrics.

Usage:
    python manage.py seed_prompt_library --json-file path/to/top-1000-prompts-library.json
    python manage.py seed_prompt_library --clear-existing  # Clears existing data first
    python manage.py seed_prompt_library --update-only     # Only updates existing prompts
"""

import json
import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import models
from apps.templates.models import (
    Template, 
    TemplateCategory, 
    PromptField, 
    TemplateField, 
    FieldType
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with comprehensive prompt library data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default='top-1000-prompts-library.json',
            help='Path to the JSON file containing prompt library data'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing templates before seeding'
        )
        parser.add_argument(
            '--update-only',
            action='store_true',
            help='Only update existing templates, do not create new ones'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually saving data'
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']
        json_file = options['json_file']
        
        # Find the JSON file
        if not os.path.isabs(json_file):
            # Try multiple possible locations
            possible_paths = [
                json_file,
                os.path.join(os.getcwd(), json_file),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), json_file),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), json_file)
            ]
            
            json_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    json_file = path
                    break
            
            if not json_file:
                raise CommandError(f"Could not find JSON file. Tried: {possible_paths}")

        self.stdout.write(f"📂 Loading prompt library from: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"JSON file not found: {json_file}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")

        # Validate JSON structure
        if not self._validate_json_structure(data):
            raise CommandError("Invalid JSON structure")

        # Get or create admin user for templates
        admin_user = self._get_or_create_admin_user()

        # Clear existing data if requested
        if options['clear_existing']:
            self._clear_existing_data()

        # Process the data
        stats = {
            'categories_created': 0,
            'categories_updated': 0,
            'templates_created': 0,
            'templates_updated': 0,
            'errors': []
        }

        try:
            # Process categories and templates
            if self.dry_run:
                # For dry run, use a savepoint to rollback changes
                with transaction.atomic():
                    sid = transaction.savepoint()
                    self._process_categories(data, admin_user, stats, options)
                    transaction.savepoint_rollback(sid)
                    self.stdout.write(self.style.WARNING("🔄 DRY RUN - No data was actually saved"))
            else:
                # For real run, process without transaction wrapping to handle individual errors
                self._process_categories(data, admin_user, stats, options)
                
        except Exception as e:
            raise CommandError(f"Error during seeding: {str(e)}")

        # Display results
        self._display_results(stats)

    def _validate_json_structure(self, data):
        """Validate that the JSON has the expected structure"""
        required_keys = ['prompt_library_metadata', 'categories']
        
        for key in required_keys:
            if key not in data:
                self.stdout.write(
                    self.style.ERROR(f"❌ Missing required key: {key}")
                )
                return False
        
        if not isinstance(data['categories'], dict):
            self.stdout.write(
                self.style.ERROR("❌ 'categories' should be a dictionary")
            )
            return False
            
        self.stdout.write(self.style.SUCCESS("✅ JSON structure is valid"))
        return True

    def _get_or_create_admin_user(self):
        """Get or create admin user for template creation"""
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@promptcraft.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created admin user: {admin_user.username}")
                )
            return admin_user
        except Exception as e:
            raise CommandError(f"Failed to create admin user: {e}")

    def _clear_existing_data(self):
        """Clear existing template data"""
        if not self.dry_run:
            deleted_templates = Template.objects.count()
            deleted_categories = TemplateCategory.objects.count()
            
            Template.objects.all().delete()
            TemplateCategory.objects.all().delete()
            
            self.stdout.write(
                self.style.WARNING(
                    f"🗑️  Cleared {deleted_templates} templates and {deleted_categories} categories"
                )
            )

    def _process_categories(self, data, admin_user, stats, options):
        """Process categories and their templates"""
        categories_data = data['categories']
        metadata = data.get('prompt_library_metadata', {})
        
        for category_key, category_info in categories_data.items():
            try:
                # Create/update category
                category = self._create_or_update_category(
                    category_key, 
                    category_info, 
                    stats
                )
                
                if category:
                    # Process subcategories and prompts
                    subcategories = category_info.get('subcategories', {})
                    for subcat_key, subcat_info in subcategories.items():
                        self._process_subcategory_prompts(
                            category, 
                            subcat_key, 
                            subcat_info, 
                            admin_user, 
                            stats, 
                            options
                        )
                        
            except Exception as e:
                error_msg = f"Error processing category {category_key}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))

    def _create_or_update_category(self, category_key, category_info, stats):
        """Create or update a template category"""
        category_name = self._format_category_name(category_key)
        category_slug = slugify(category_key)
        
        # Define category colors and icons
        category_styles = {
            'business_strategy': {'color': '#1E40AF', 'icon': 'chart-line'},
            'marketing_sales': {'color': '#DC2626', 'icon': 'megaphone'},
            'project_management': {'color': '#059669', 'icon': 'clipboard-list'},
            'operations_management': {'color': '#7C2D12', 'icon': 'cogs'},
            'data_analysis': {'color': '#6366F1', 'icon': 'chart-bar'},
            'technical_development': {'color': '#1F2937', 'icon': 'code'},
            'creative_content': {'color': '#EC4899', 'icon': 'palette'},
            'education_training': {'color': '#059669', 'icon': 'academic-cap'},
            'legal_compliance': {'color': '#374151', 'icon': 'scale'},
            'healthcare_medical': {'color': '#EF4444', 'icon': 'heart'},
            'finance_investment': {'color': '#10B981', 'icon': 'dollar-sign'},
            'human_resources': {'color': '#F59E0B', 'icon': 'users'},
            'customer_service': {'color': '#8B5CF6', 'icon': 'support'},
            'product_development': {'color': '#06B6D4', 'icon': 'lightbulb'},
        }
        
        defaults = {
            'name': category_name,
            'description': category_info.get('description', ''),
            'color': category_styles.get(category_key, {}).get('color', '#6366F1'),
            'icon': category_styles.get(category_key, {}).get('icon', 'folder'),
            'is_active': True,
            'order': len(category_styles)
        }
        
        if not self.dry_run:
            category, created = TemplateCategory.objects.get_or_create(
                slug=category_slug,
                defaults=defaults
            )
            
            if created:
                stats['categories_created'] += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created category: {category_name}")
                )
            else:
                # Update existing category
                for key, value in defaults.items():
                    setattr(category, key, value)
                category.save()
                stats['categories_updated'] += 1
                self.stdout.write(
                    self.style.WARNING(f"🔄 Updated category: {category_name}")
                )
        else:
            # Dry run - just create a mock category
            category = TemplateCategory(slug=category_slug, **defaults)
            stats['categories_created'] += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ [DRY RUN] Would create category: {category_name}")
            )
            
        return category

    def _process_subcategory_prompts(self, category, subcat_key, subcat_info, admin_user, stats, options):
        """Process prompts within a subcategory"""
        prompts = subcat_info.get('prompts', [])
        
        for prompt_data in prompts:
            try:
                self._create_or_update_template(
                    category, 
                    subcat_key, 
                    prompt_data, 
                    admin_user, 
                    stats, 
                    options
                )
            except Exception as e:
                error_msg = f"Error processing prompt {prompt_data.get('id', 'unknown')}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))

    def _create_or_update_template(self, category, subcategory, prompt_data, admin_user, stats, options):
        """Create or update a template from prompt data"""
        external_id = prompt_data.get('id', '')
        title = prompt_data.get('title', '')
        framework = prompt_data.get('framework', '')
        prompt_content = prompt_data.get('prompt', '')
        use_cases = prompt_data.get('use_cases', [])
        performance_metrics = prompt_data.get('performance_metrics', {})
        
        if not title or not prompt_content:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Skipping prompt {external_id}: Missing title or content")
            )
            return

        # Extract placeholder fields from prompt content
        placeholder_fields = self._extract_placeholder_fields(prompt_content)
        
        # Create comprehensive description with framework and metrics info
        description = self._generate_description(prompt_data, subcategory)
        if framework:
            description += f" Uses {framework} framework."
        if performance_metrics:
            metrics_text = ", ".join([f"{k}: {v}" for k, v in performance_metrics.items()])
            description += f" Performance: {metrics_text}."
        
        # Store additional data in tags and smart_suggestions
        enhanced_tags = self._generate_tags(prompt_data, subcategory, framework)
        if external_id:
            enhanced_tags.append(f"source-id-{external_id}")
        
        # Store framework and metrics in smart_suggestions for later retrieval
        smart_suggestions = {
            'framework': framework,
            'subcategory': self._format_subcategory_name(subcategory),
            'use_cases': use_cases,
            'performance_metrics': performance_metrics,
            'source_id': external_id
        }
        
        # Prepare template data using existing model fields
        template_data = {
            'title': title[:200],  # Ensure it fits in the field
            'description': description,
            'category': category,
            'template_content': prompt_content,
            'author': admin_user,
            'tags': enhanced_tags,
            'smart_suggestions': smart_suggestions,
            'is_public': True,
            'is_active': True,
            'is_featured': self._should_be_featured(performance_metrics),
            'is_ai_generated': True,  # Mark as AI-generated professional prompts
            'ai_confidence': 0.95,   # High confidence for professionally curated prompts
            'version': '1.0.0'
        }

        if not self.dry_run:
            # Check if template exists by title (since we don't have external_id field)
            template = None
            if title:
                template = Template.objects.filter(title=title, category=category).first()
            
            if template and not options['update_only']:
                # Update existing template
                for key, value in template_data.items():
                    setattr(template, key, value)
                template.save()
                stats['templates_updated'] += 1
                self.stdout.write(
                    self.style.WARNING(f"🔄 Updated template: {title}")
                )
            elif not template and not options['update_only']:
                # Create new template
                template = Template.objects.create(**template_data)
                stats['templates_created'] += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created template: {title}")
                )
                
                # Create fields for this template
                self._create_template_fields(template, placeholder_fields)
            
        else:
            # Dry run
            stats['templates_created'] += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ [DRY RUN] Would create template: {title}")
            )

    def _extract_placeholder_fields(self, prompt_content):
        """Extract placeholder fields from prompt content"""
        # Pattern to match [PLACEHOLDER_NAME] or {{placeholder_name}} or {placeholder_name}
        patterns = [
            r'\[([A-Z_][A-Z0-9_]*)\]',  # [PLACEHOLDER_NAME]
            r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}',  # {{placeholder_name}}
            r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',  # {placeholder_name}
        ]
        
        placeholders = set()
        for pattern in patterns:
            matches = re.findall(pattern, prompt_content)
            placeholders.update(matches)
        
        return list(placeholders)

    def _create_template_fields(self, template, placeholder_fields):
        """Create PromptField instances for template placeholders"""
        for i, placeholder in enumerate(placeholder_fields):
            # Convert placeholder to human-readable label
            label = self._format_field_label(placeholder)
            
            # Determine field type based on placeholder name
            field_type = self._determine_field_type(placeholder)
            
            # Create the PromptField
            prompt_field = PromptField.objects.create(
                label=label,
                placeholder=f"Enter {label.lower()}",
                field_type=field_type,
                is_required=True,
                order=i,
                help_text=f"Please provide {label.lower()} for the prompt"
            )
            
            # Link to template through TemplateField
            TemplateField.objects.create(
                template=template,
                field=prompt_field,
                order=i
            )

    def _format_field_label(self, placeholder):
        """Convert placeholder name to human-readable label"""
        # Convert PLACEHOLDER_NAME to Placeholder Name
        return placeholder.replace('_', ' ').title()

    def _determine_field_type(self, placeholder):
        """Determine appropriate field type based on placeholder name"""
        placeholder_lower = placeholder.lower()
        
        # Text areas for longer content
        if any(keyword in placeholder_lower for keyword in [
            'description', 'content', 'message', 'details', 'explanation',
            'background', 'context', 'story', 'objective', 'response'
        ]):
            return FieldType.TEXTAREA
        
        # Numbers
        if any(keyword in placeholder_lower for keyword in [
            'count', 'number', 'amount', 'budget', 'age', 'year', 'rate'
        ]):
            return FieldType.NUMBER
        
        # Default to text
        return FieldType.TEXT

    def _generate_description(self, prompt_data, subcategory):
        """Generate a comprehensive description for the template"""
        base_desc = f"Professional {self._format_subcategory_name(subcategory)} prompt template"
        
        if 'framework' in prompt_data and prompt_data['framework']:
            base_desc += f" using the {prompt_data['framework']} framework"
        
        if 'use_cases' in prompt_data and prompt_data['use_cases']:
            use_cases_str = ', '.join(prompt_data['use_cases'][:3])
            base_desc += f". Ideal for {use_cases_str}"
        
        # Add performance highlights if available
        if 'performance_metrics' in prompt_data and prompt_data['performance_metrics']:
            metrics = prompt_data['performance_metrics']
            if metrics:
                key_metric = list(metrics.keys())[0]  # Get first metric
                metric_value = metrics[key_metric]
                base_desc += f". Proven performance: {key_metric} {metric_value}"
        
        base_desc += ". This enterprise-grade prompt has been professionally curated and tested for optimal results."
        
        return base_desc

    def _generate_tags(self, prompt_data, subcategory, framework):
        """Generate tags for the template"""
        tags = []
        
        # Add framework as tag
        if framework:
            tags.append(framework.lower())
        
        # Add subcategory
        tags.append(subcategory.replace('_', ' '))
        
        # Add use cases as tags
        if 'use_cases' in prompt_data:
            tags.extend([case.lower() for case in prompt_data['use_cases']])
        
        # Add performance-related tags
        if 'performance_metrics' in prompt_data:
            metrics = prompt_data['performance_metrics']
            if any(key in metrics for key in ['accuracy', 'success_rate']):
                tags.append('high-performance')
            if any(key in metrics for key in ['time_savings', 'efficiency']):
                tags.append('time-saving')
        
        return list(set(tags))  # Remove duplicates

    def _should_be_featured(self, performance_metrics):
        """Determine if a template should be featured based on performance metrics"""
        if not performance_metrics:
            return False
        
        # Look for high-performance indicators
        for key, value in performance_metrics.items():
            if isinstance(value, str):
                # Look for percentage improvements
                if '%' in value and any(char.isdigit() for char in value):
                    try:
                        # Extract number from strings like "+89%", "67%", etc.
                        num_str = ''.join(c for c in value if c.isdigit() or c == '.')
                        if num_str and float(num_str) >= 80:  # High performance threshold
                            return True
                    except:
                        pass
                # Look for high ratings
                if '4.' in value or '5.' in value or value in ['4.8/5', '4.9/5']:
                    return True
        
        return False

    def _format_category_name(self, category_key):
        """Convert category_key to human-readable name"""
        return category_key.replace('_', ' ').title()

    def _format_subcategory_name(self, subcategory_key):
        """Convert subcategory_key to human-readable name"""
        return subcategory_key.replace('_', ' ').title()

    def _display_results(self, stats):
        """Display seeding results"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📊 SEEDING RESULTS"))
        self.stdout.write("="*50)
        
        self.stdout.write(f"Categories created: {stats['categories_created']}")
        self.stdout.write(f"Categories updated: {stats['categories_updated']}")
        self.stdout.write(f"Templates created: {stats['templates_created']}")
        self.stdout.write(f"Templates updated: {stats['templates_updated']}")
        
        if stats['errors']:
            self.stdout.write(f"\n❌ Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                self.stdout.write(f"  - {error}")
            if len(stats['errors']) > 5:
                self.stdout.write(f"  ... and {len(stats['errors']) - 5} more errors")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ No errors encountered!"))
        
        self.stdout.write("\n" + "="*50)