# management/commands/setup_template_extraction.py
"""
Django management command to set up template extraction system
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up template extraction system with initial data and configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-models',
            action='store_true',
            help='Create database tables for chat and template extraction models',
        )
        parser.add_argument(
            '--setup-rules',
            action='store_true',
            help='Create initial template extraction rules',
        )
        parser.add_argument(
            '--setup-categories',
            action='store_true',
            help='Create initial template categories',
        )
        parser.add_argument(
            '--create-admin-user',
            action='store_true',
            help='Create admin user for template moderation',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all setup tasks',
        )
    
    def handle(self, *args, **options):
        if options['all']:
            options['create_models'] = True
            options['setup_rules'] = True
            options['setup_categories'] = True
        
        if options['create_models']:
            self.create_models()
        
        if options['setup_rules']:
            self.setup_extraction_rules()
        
        if options['setup_categories']:
            self.setup_template_categories()
        
        if options['create_admin_user']:
            self.create_admin_user()
        
        self.stdout.write(
            self.style.SUCCESS('Template extraction system setup completed successfully!')
        )
    
    def create_models(self):
        """Create database tables for chat and template extraction"""
        self.stdout.write('Creating database tables...')
        
        try:
            from django.core.management import call_command
            
            # Generate migrations
            call_command('makemigrations', 'chat', verbosity=1)
            
            # Apply migrations
            call_command('migrate', verbosity=1)
            
            self.stdout.write(self.style.SUCCESS('✓ Database tables created successfully'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating database tables: {e}')
            )
    
    def setup_extraction_rules(self):
        """Create initial template extraction rules"""
        self.stdout.write('Setting up template extraction rules...')
        
        try:
            from apps.chat.models import TemplateExtractionRule
            
            rules = [
                {
                    'name': 'High-Value Business Templates',
                    'description': 'Extract templates containing business and monetization keywords',
                    'rule_type': 'keyword',
                    'rule_config': {
                        'keywords': [
                            'business', 'monetization', 'revenue', 'profit', 'sales',
                            'marketing', 'strategy', 'planning', 'optimization'
                        ],
                        'minimum_keywords': 2,
                        'boost_score': 0.2
                    },
                    'minimum_confidence': 0.6,
                    'auto_approve_threshold': 0.8,
                    'priority': 1
                },
                {
                    'name': 'Numbered Prompt Lists',
                    'description': 'Extract numbered prompt lists and collections',
                    'rule_type': 'pattern',
                    'rule_config': {
                        'patterns': [
                            r'\d+\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)',
                            r'\*\s*\*\d+\*\*\s*(.+?)(?=\n\*|\Z)'
                        ],
                        'minimum_matches': 3
                    },
                    'minimum_confidence': 0.8,
                    'auto_approve_threshold': 0.9,
                    'priority': 2
                },
                {
                    'name': 'Role-Based Templates',
                    'description': 'Extract "Act as" and role-based prompt templates',
                    'rule_type': 'pattern',
                    'rule_config': {
                        'patterns': [
                            r'(Act as|You are|As a|Role:|Persona:)\s*(.+?)(?=\n\n|\Z)',
                            r'(I want you to act as|Please act as)\s*(.+?)(?=\n\n|\Z)'
                        ],
                        'minimum_length': 50
                    },
                    'minimum_confidence': 0.7,
                    'auto_approve_threshold': 0.85,
                    'priority': 3
                },
                {
                    'name': 'Template Collections',
                    'description': 'Extract large collections of templates (100+ templates)',
                    'rule_type': 'langchain',
                    'rule_config': {
                        'analysis_type': 'collection_detection',
                        'minimum_templates': 10,
                        'quality_threshold': 0.6
                    },
                    'minimum_confidence': 0.9,
                    'auto_approve_threshold': 0.95,
                    'priority': 4
                },
                {
                    'name': 'Professional Templates',
                    'description': 'Extract professional and industry-specific templates',
                    'rule_type': 'keyword',
                    'rule_config': {
                        'keywords': [
                            'professional', 'industry', 'corporate', 'enterprise',
                            'consulting', 'analysis', 'report', 'proposal'
                        ],
                        'minimum_keywords': 1,
                        'context_boost': True
                    },
                    'minimum_confidence': 0.5,
                    'auto_approve_threshold': 0.8,
                    'priority': 5
                }
            ]
            
            created_count = 0
            for rule_data in rules:
                rule, created = TemplateExtractionRule.objects.get_or_create(
                    name=rule_data['name'],
                    defaults=rule_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created rule: {rule.name}')
                else:
                    self.stdout.write(f'  - Rule already exists: {rule.name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created {created_count} new extraction rules')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error setting up extraction rules: {e}')
            )
    
    def setup_template_categories(self):
        """Create initial template categories for extracted templates"""
        self.stdout.write('Setting up template categories...')
        
        try:
            from django_models import TemplateCategory
            
            categories = [
                {
                    'name': 'Business Strategy',
                    'slug': 'business-strategy',
                    'description': 'Templates for business planning, strategy, and monetization',
                    'icon': 'business',
                    'color': '#2563EB',
                    'order': 1
                },
                {
                    'name': 'Marketing & Sales',
                    'slug': 'marketing-sales',
                    'description': 'Templates for marketing campaigns, sales funnels, and customer acquisition',
                    'icon': 'campaign',
                    'color': '#DC2626',
                    'order': 2
                },
                {
                    'name': 'Content Creation',
                    'slug': 'content-creation',
                    'description': 'Templates for writing, copywriting, and content development',
                    'icon': 'edit',
                    'color': '#7C3AED',
                    'order': 3
                },
                {
                    'name': 'Analysis & Research',
                    'slug': 'analysis-research',
                    'description': 'Templates for data analysis, market research, and insights',
                    'icon': 'analytics',
                    'color': '#059669',
                    'order': 4
                },
                {
                    'name': 'Planning & Organization',
                    'slug': 'planning-organization',
                    'description': 'Templates for project planning, goal setting, and organization',
                    'icon': 'planning',
                    'color': '#D97706',
                    'order': 5
                },
                {
                    'name': 'Creative & Innovation',
                    'slug': 'creative-innovation',
                    'description': 'Templates for brainstorming, ideation, and creative problem solving',
                    'icon': 'lightbulb',
                    'color': '#EC4899',
                    'order': 6
                },
                {
                    'name': 'Technical & Development',
                    'slug': 'technical-development',
                    'description': 'Templates for software development, technical writing, and IT tasks',
                    'icon': 'code',
                    'color': '#6B7280',
                    'order': 7
                },
                {
                    'name': 'Personal Productivity',
                    'slug': 'personal-productivity',
                    'description': 'Templates for personal development, productivity, and self-improvement',
                    'icon': 'person',
                    'color': '#10B981',
                    'order': 8
                },
                {
                    'name': 'Role Playing',
                    'slug': 'role-playing',
                    'description': 'Act as and persona-based prompt templates',
                    'icon': 'theater_comedy',
                    'color': '#8B5CF6',
                    'order': 9
                },
                {
                    'name': 'Template Collections',
                    'slug': 'template-collections',
                    'description': 'Large collections and lists of prompt templates',
                    'icon': 'collections',
                    'color': '#F59E0B',
                    'order': 10
                }
            ]
            
            created_count = 0
            for category_data in categories:
                category, created = TemplateCategory.objects.get_or_create(
                    slug=category_data['slug'],
                    defaults=category_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created category: {category.name}')
                else:
                    self.stdout.write(f'  - Category already exists: {category.name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created {created_count} new template categories')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error setting up template categories: {e}')
            )
    
    def create_admin_user(self):
        """Create admin user for template moderation"""
        self.stdout.write('Creating admin user for template moderation...')
        
        try:
            admin_user, created = User.objects.get_or_create(
                username='template_admin',
                defaults={
                    'email': 'admin@promptcraft.local',
                    'first_name': 'Template',
                    'last_name': 'Administrator',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_premium': True
                }
            )
            
            if created:
                admin_user.set_password('admin123')  # Change this in production
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS('✓ Created admin user: template_admin (password: admin123)')
                )
            else:
                self.stdout.write('  - Admin user already exists')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating admin user: {e}')
            )