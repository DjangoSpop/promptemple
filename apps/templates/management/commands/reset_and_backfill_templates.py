"""
Management command to reset and backfill template data with clean data
This will clear all templates and reload from scratch
Usage: python manage.py reset_and_backfill_templates
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.templates.models import (
    Template, 
    TemplateCategory, 
    PromptField, 
    TemplateField,
    TemplateUsage,
    TemplateRating,
    TemplateBookmark
)
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset all template data and backfill with clean data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all existing template data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('⚠️  DATABASE RESET & BACKFILL'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        if not options['confirm']:
            self.stdout.write(self.style.ERROR('\n❌ This command will DELETE ALL template data!'))
            self.stdout.write(self.style.WARNING('\nThis includes:'))
            self.stdout.write('  - All templates')
            self.stdout.write('  - All categories')
            self.stdout.write('  - All prompt fields')
            self.stdout.write('  - All template usage records')
            self.stdout.write('  - All ratings and bookmarks')
            self.stdout.write(self.style.WARNING('\n⚠️  User data will NOT be affected'))
            self.stdout.write(self.style.ERROR('\nTo proceed, run with --confirm flag:'))
            self.stdout.write(self.style.SUCCESS('python manage.py reset_and_backfill_templates --confirm'))
            return

        self.stdout.write(self.style.WARNING('\n🗑️  Deleting existing template data...'))
        
        try:
            with transaction.atomic():
                # Delete in correct order (respecting foreign keys)
                deleted_counts = {}
                
                # Delete related data first (with error handling for missing tables)
                try:
                    deleted_counts['bookmarks'] = TemplateBookmark.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping bookmarks: {e}')
                    deleted_counts['bookmarks'] = 0
                
                try:
                    deleted_counts['ratings'] = TemplateRating.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping ratings: {e}')
                    deleted_counts['ratings'] = 0
                
                try:
                    deleted_counts['usage'] = TemplateUsage.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping usage: {e}')
                    deleted_counts['usage'] = 0
                
                try:
                    deleted_counts['template_fields'] = TemplateField.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping template_fields: {e}')
                    deleted_counts['template_fields'] = 0
                
                # Delete templates
                try:
                    deleted_counts['templates'] = Template.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping templates: {e}')
                    deleted_counts['templates'] = 0
                
                # Delete fields and categories
                try:
                    deleted_counts['fields'] = PromptField.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping fields: {e}')
                    deleted_counts['fields'] = 0
                
                try:
                    deleted_counts['categories'] = TemplateCategory.objects.all().delete()[0]
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Skipping categories: {e}')
                    deleted_counts['categories'] = 0
                
                self.stdout.write(self.style.SUCCESS('✅ Deleted existing data:'))
                for model, count in deleted_counts.items():
                    if count > 0:
                        self.stdout.write(f'   - {model}: {count}')
                
                # Now backfill with clean data
                self.stdout.write(self.style.WARNING('\n🌱 Backfilling with clean template data...'))
                self.backfill_templates()
                
                self.stdout.write(self.style.SUCCESS('\n✅ Reset and backfill completed successfully!'))
                self.stdout.write(self.style.WARNING('=' * 60))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during reset: {str(e)}'))
            raise

    def backfill_templates(self):
        """Backfill database with clean template data"""
        
        # Get or create admin user
        admin_user = self.get_or_create_admin_user()
        
        # Create categories
        categories = self.create_categories()
        
        # Create templates
        self.create_clean_templates(categories, admin_user)

    def get_or_create_admin_user(self):
        """Get or create admin user for templates"""
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                self.stdout.write(f'   Using existing admin user: {admin_user.username}')
                return admin_user
        except Exception:
            pass
        
        # Create default admin if none exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@prompt-temple.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('   Created admin user (username: admin, password: admin123)')
        return admin_user

    def create_categories(self):
        """Create clean template categories"""
        self.stdout.write('   📁 Creating categories...')
        
        categories_data = [
            {
                'name': 'Content Creation',
                'slug': 'content-creation',
                'description': 'Templates for blogs, articles, and social media content',
                'icon': 'edit',
                'color': '#3B82F6',
                'order': 1
            },
            {
                'name': 'Marketing',
                'slug': 'marketing',
                'description': 'Marketing campaigns, emails, and advertising templates',
                'icon': 'megaphone',
                'color': '#EF4444',
                'order': 2
            },
            {
                'name': 'Business',
                'slug': 'business',
                'description': 'Professional business documents and proposals',
                'icon': 'briefcase',
                'color': '#10B981',
                'order': 3
            },
            {
                'name': 'Education',
                'slug': 'education',
                'description': 'Educational content and lesson planning',
                'icon': 'academic-cap',
                'color': '#F59E0B',
                'order': 4
            },
            {
                'name': 'Creative Writing',
                'slug': 'creative-writing',
                'description': 'Creative writing and storytelling templates',
                'icon': 'pencil',
                'color': '#8B5CF6',
                'order': 5
            },
            {
                'name': 'Technical',
                'slug': 'technical',
                'description': 'Technical documentation and API guides',
                'icon': 'code',
                'color': '#6B7280',
                'order': 6
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = TemplateCategory.objects.create(**cat_data)
            categories[cat_data['slug']] = category
            self.stdout.write(f'      ✓ {category.name}')
        
        return categories

    def create_clean_templates(self, categories, admin_user):
        """Create clean templates without bad data"""
        self.stdout.write('   📝 Creating templates...')
        
        templates_data = [
            {
                'title': 'Blog Post Writer',
                'description': 'Create engaging blog posts with proper structure and SEO optimization',
                'category': 'content-creation',
                'content': '''Write a comprehensive blog post about {{topic}}.

Target Audience: {{audience}}
Tone: {{tone}}
Word Count: {{word_count}}

Include:
- Compelling introduction
- Well-structured main content
- Clear conclusion with call-to-action
- SEO-optimized headings''',
                'tags': ['blog', 'content', 'seo', 'writing'],
                'is_featured': True,
                'fields': [
                    {'label': 'Topic', 'type': 'text', 'placeholder': 'What is your blog post about?', 'required': True},
                    {'label': 'Target Audience', 'type': 'text', 'placeholder': 'Who are you writing for?', 'required': True},
                    {'label': 'Tone', 'type': 'dropdown', 'options': ['Professional', 'Casual', 'Informative', 'Conversational'], 'required': True},
                    {'label': 'Word Count', 'type': 'number', 'placeholder': '1000', 'required': False}
                ]
            },
            {
                'title': 'Social Media Post',
                'description': 'Generate engaging social media posts for various platforms',
                'category': 'content-creation',
                'content': '''Create a {{platform}} post about {{topic}}.

Message: {{message}}
Tone: {{tone}}
Include hashtags: {{include_hashtags}}
Call to action: {{cta}}''',
                'tags': ['social-media', 'engagement', 'marketing'],
                'is_featured': True,
                'fields': [
                    {'label': 'Platform', 'type': 'dropdown', 'options': ['Instagram', 'Twitter', 'LinkedIn', 'Facebook', 'TikTok'], 'required': True},
                    {'label': 'Topic', 'type': 'text', 'placeholder': 'What are you posting about?', 'required': True},
                    {'label': 'Message', 'type': 'textarea', 'placeholder': 'Your main message...', 'required': True},
                    {'label': 'Tone', 'type': 'dropdown', 'options': ['Professional', 'Casual', 'Funny', 'Inspirational'], 'required': False},
                    {'label': 'Include Hashtags', 'type': 'checkbox', 'options': ['Yes'], 'required': False},
                    {'label': 'Call to Action', 'type': 'text', 'placeholder': 'What should people do?', 'required': False}
                ]
            },
            {
                'title': 'Email Marketing Campaign',
                'description': 'Create compelling marketing emails that convert',
                'category': 'marketing',
                'content': '''Subject: {{subject}}

Hi {{recipient_name}},

{{opening}}

{{main_message}}

Key Benefits:
{{benefits}}

{{call_to_action}}

Best regards,
{{sender_name}}''',
                'tags': ['email', 'marketing', 'conversion'],
                'is_featured': False,
                'fields': [
                    {'label': 'Subject Line', 'type': 'text', 'placeholder': 'Compelling subject...', 'required': True},
                    {'label': 'Recipient Name', 'type': 'text', 'placeholder': 'First name or title', 'required': False},
                    {'label': 'Opening', 'type': 'textarea', 'placeholder': 'Personal greeting...', 'required': True},
                    {'label': 'Main Message', 'type': 'textarea', 'placeholder': 'What are you offering?', 'required': True},
                    {'label': 'Benefits', 'type': 'textarea', 'placeholder': 'List key benefits...', 'required': False},
                    {'label': 'Call to Action', 'type': 'text', 'placeholder': 'What should they do next?', 'required': True},
                    {'label': 'Sender Name', 'type': 'text', 'placeholder': 'Your name', 'required': True}
                ]
            },
            {
                'title': 'Product Description',
                'description': 'Write compelling product descriptions that sell',
                'category': 'marketing',
                'content': '''Product: {{product_name}}

{{description}}

Key Features:
{{features}}

Perfect for: {{target_customer}}
Price: {{price}}

{{unique_selling_point}}''',
                'tags': ['product', 'ecommerce', 'sales'],
                'is_featured': True,
                'fields': [
                    {'label': 'Product Name', 'type': 'text', 'placeholder': 'What is the product?', 'required': True},
                    {'label': 'Description', 'type': 'textarea', 'placeholder': 'Describe the product...', 'required': True},
                    {'label': 'Key Features', 'type': 'textarea', 'placeholder': 'List main features...', 'required': True},
                    {'label': 'Target Customer', 'type': 'text', 'placeholder': 'Who is this for?', 'required': False},
                    {'label': 'Price', 'type': 'text', 'placeholder': '$99', 'required': False},
                    {'label': 'Unique Selling Point', 'type': 'textarea', 'placeholder': 'What makes it special?', 'required': True}
                ]
            },
            {
                'title': 'Business Proposal',
                'description': 'Create professional business proposals',
                'category': 'business',
                'content': '''BUSINESS PROPOSAL

To: {{client_name}}
From: {{company_name}}
Date: {{date}}

Executive Summary:
{{executive_summary}}

Project Scope:
{{scope}}

Timeline: {{timeline}}
Budget: {{budget}}

Next Steps:
{{next_steps}}''',
                'tags': ['business', 'proposal', 'professional'],
                'is_featured': False,
                'fields': [
                    {'label': 'Client Name', 'type': 'text', 'placeholder': 'Client or company', 'required': True},
                    {'label': 'Your Company', 'type': 'text', 'placeholder': 'Your company name', 'required': True},
                    {'label': 'Executive Summary', 'type': 'textarea', 'placeholder': 'Brief overview...', 'required': True},
                    {'label': 'Project Scope', 'type': 'textarea', 'placeholder': 'What will you deliver?', 'required': True},
                    {'label': 'Timeline', 'type': 'text', 'placeholder': '4-6 weeks', 'required': False},
                    {'label': 'Budget', 'type': 'text', 'placeholder': '$10,000', 'required': False},
                    {'label': 'Next Steps', 'type': 'textarea', 'placeholder': 'What happens next?', 'required': True}
                ]
            },
            {
                'title': 'Meeting Agenda',
                'description': 'Structure productive meetings with clear agendas',
                'category': 'business',
                'content': '''MEETING AGENDA

Title: {{meeting_title}}
Date: {{date}}
Time: {{time}}
Location: {{location}}

Attendees: {{attendees}}

Agenda:
{{agenda_items}}

Action Items:
{{action_items}}''',
                'tags': ['meeting', 'productivity', 'business'],
                'is_featured': False,
                'fields': [
                    {'label': 'Meeting Title', 'type': 'text', 'placeholder': 'Purpose of meeting', 'required': True},
                    {'label': 'Date', 'type': 'text', 'placeholder': 'Meeting date', 'required': True},
                    {'label': 'Time', 'type': 'text', 'placeholder': '10:00 AM', 'required': False},
                    {'label': 'Location', 'type': 'text', 'placeholder': 'Conference room or Zoom', 'required': False},
                    {'label': 'Attendees', 'type': 'textarea', 'placeholder': 'Who will attend?', 'required': False},
                    {'label': 'Agenda Items', 'type': 'textarea', 'placeholder': 'List discussion topics...', 'required': True}
                ]
            },
            {
                'title': 'Lesson Plan',
                'description': 'Create comprehensive lesson plans for educators',
                'category': 'education',
                'content': '''LESSON PLAN

Subject: {{subject}}
Grade Level: {{grade}}
Duration: {{duration}}

Learning Objectives:
{{objectives}}

Materials Needed:
{{materials}}

Lesson Activities:
{{activities}}

Assessment:
{{assessment}}''',
                'tags': ['education', 'teaching', 'lesson'],
                'is_featured': False,
                'fields': [
                    {'label': 'Subject', 'type': 'text', 'placeholder': 'What subject?', 'required': True},
                    {'label': 'Grade Level', 'type': 'text', 'placeholder': '5th Grade', 'required': True},
                    {'label': 'Duration', 'type': 'text', 'placeholder': '45 minutes', 'required': False},
                    {'label': 'Learning Objectives', 'type': 'textarea', 'placeholder': 'What will students learn?', 'required': True},
                    {'label': 'Materials', 'type': 'textarea', 'placeholder': 'List materials needed...', 'required': False},
                    {'label': 'Activities', 'type': 'textarea', 'placeholder': 'Describe lesson activities...', 'required': True},
                    {'label': 'Assessment', 'type': 'textarea', 'placeholder': 'How will you assess learning?', 'required': False}
                ]
            },
            {
                'title': 'Story Outline',
                'description': 'Develop story outlines for creative writing',
                'category': 'creative-writing',
                'content': '''STORY OUTLINE

Title: {{title}}
Genre: {{genre}}

Main Character: {{protagonist}}
Setting: {{setting}}

Plot Summary:
{{plot}}

Key Scenes:
{{scenes}}

Conflict: {{conflict}}
Resolution: {{resolution}}''',
                'tags': ['story', 'writing', 'creative'],
                'is_featured': True,
                'fields': [
                    {'label': 'Story Title', 'type': 'text', 'placeholder': 'Working title', 'required': True},
                    {'label': 'Genre', 'type': 'dropdown', 'options': ['Fantasy', 'Sci-Fi', 'Mystery', 'Romance', 'Thriller', 'Drama'], 'required': True},
                    {'label': 'Main Character', 'type': 'text', 'placeholder': 'Protagonist name and description', 'required': True},
                    {'label': 'Setting', 'type': 'text', 'placeholder': 'Where does it take place?', 'required': True},
                    {'label': 'Plot Summary', 'type': 'textarea', 'placeholder': 'Brief plot overview...', 'required': True},
                    {'label': 'Key Scenes', 'type': 'textarea', 'placeholder': 'List major scenes...', 'required': False},
                    {'label': 'Conflict', 'type': 'textarea', 'placeholder': 'Main conflict...', 'required': True},
                    {'label': 'Resolution', 'type': 'textarea', 'placeholder': 'How does it end?', 'required': False}
                ]
            },
            {
                'title': 'API Documentation',
                'description': 'Document APIs with clear examples and specifications',
                'category': 'technical',
                'content': '''API DOCUMENTATION

Endpoint: {{endpoint}}
Method: {{method}}
Description: {{description}}

Parameters:
{{parameters}}

Request Example:
{{request_example}}

Response Example:
{{response_example}}

Error Codes:
{{error_codes}}''',
                'tags': ['api', 'documentation', 'technical'],
                'is_featured': False,
                'fields': [
                    {'label': 'Endpoint', 'type': 'text', 'placeholder': '/api/v1/resource', 'required': True},
                    {'label': 'HTTP Method', 'type': 'dropdown', 'options': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], 'required': True},
                    {'label': 'Description', 'type': 'textarea', 'placeholder': 'What does this endpoint do?', 'required': True},
                    {'label': 'Parameters', 'type': 'textarea', 'placeholder': 'List parameters...', 'required': False},
                    {'label': 'Request Example', 'type': 'textarea', 'placeholder': 'Show example request...', 'required': True},
                    {'label': 'Response Example', 'type': 'textarea', 'placeholder': 'Show example response...', 'required': True},
                    {'label': 'Error Codes', 'type': 'textarea', 'placeholder': 'List possible errors...', 'required': False}
                ]
            },
            {
                'title': 'Code Documentation',
                'description': 'Document code functions and classes clearly',
                'category': 'technical',
                'content': '''FUNCTION DOCUMENTATION

Function: {{function_name}}
Purpose: {{purpose}}

Parameters:
{{parameters}}

Returns: {{returns}}

Example Usage:
{{example}}

Notes:
{{notes}}''',
                'tags': ['code', 'documentation', 'programming'],
                'is_featured': False,
                'fields': [
                    {'label': 'Function Name', 'type': 'text', 'placeholder': 'function_name()', 'required': True},
                    {'label': 'Purpose', 'type': 'textarea', 'placeholder': 'What does it do?', 'required': True},
                    {'label': 'Parameters', 'type': 'textarea', 'placeholder': 'List parameters with types...', 'required': True},
                    {'label': 'Returns', 'type': 'text', 'placeholder': 'What does it return?', 'required': True},
                    {'label': 'Example Usage', 'type': 'textarea', 'placeholder': 'Show code example...', 'required': True},
                    {'label': 'Notes', 'type': 'textarea', 'placeholder': 'Additional notes...', 'required': False}
                ]
            }
        ]
        
        created_count = 0
        for template_data in templates_data:
            # Create template
            template = Template.objects.create(
                title=template_data['title'],
                description=template_data['description'],
                category=categories[template_data['category']],
                template_content=template_data['content'],
                author=admin_user,
                tags=template_data['tags'],
                is_featured=template_data['is_featured'],
                is_public=True,
                usage_count=0,
                average_rating=0.0,
                completion_rate=0.0
            )
            
            # Create fields
            for order, field_data in enumerate(template_data['fields']):
                field = PromptField.objects.create(
                    label=field_data['label'],
                    placeholder=field_data.get('placeholder', ''),
                    field_type=field_data.get('type', 'text'),
                    is_required=field_data.get('required', False),
                    options=field_data.get('options', []),
                    order=order
                )
                
                TemplateField.objects.create(
                    template=template,
                    field=field,
                    order=order
                )
            
            created_count += 1
            self.stdout.write(f'      ✓ {template.title}')
        
        self.stdout.write(self.style.SUCCESS(f'\n   Created {created_count} clean templates'))
        
        # Display final statistics
        self.show_statistics()

    def show_statistics(self):
        """Show database statistics after backfill"""
        self.stdout.write(self.style.SUCCESS('\n📊 Final Statistics:'))
        self.stdout.write(f'   Templates: {Template.objects.count()}')
        self.stdout.write(f'   Categories: {TemplateCategory.objects.count()}')
        self.stdout.write(f'   Prompt Fields: {PromptField.objects.count()}')
        self.stdout.write(f'   Featured Templates: {Template.objects.filter(is_featured=True).count()}')
