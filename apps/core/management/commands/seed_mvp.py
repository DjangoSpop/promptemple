"""
MVP Database Seeding Command

Seeds the database with professional sample data for MVP demo:
- Admin user  
- Sample users with realistic profiles
- Template categories
- High-quality prompt templates
- Proper relationships and data integrity
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with MVP sample data for professional demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--users-count',
            type=int,
            default=10,
            help='Number of sample users to create (default: 10)',
        )
        parser.add_argument(
            '--templates-count',
            type=int,
            default=50,
            help='Number of sample templates to create (default: 50)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(self.style.SUCCESS('🚀 Starting MVP database seeding...'))
        
        if options['reset']:
            self.clear_data()
        
        with transaction.atomic():
            # Create admin user
            admin_user = self.create_admin_user()
            
            # Create categories
            categories = self.create_categories()
            
            # Create sample users
            users = self.create_sample_users(options['users_count'])
            
            # Create sample templates
            self.create_sample_templates(
                users + [admin_user], 
                categories, 
                options['templates_count']
            )
        
        self.stdout.write(self.style.SUCCESS('✅ MVP database seeding completed successfully!'))
        self.print_summary(options['users_count'], options['templates_count'])

    def clear_data(self):
        """Clear existing sample data"""
        self.stdout.write('🧹 Clearing existing data...')
        
        # Don't delete superusers or staff users
        Template.objects.filter(is_active=True).delete()
        TemplateCategory.objects.all().delete()
        User.objects.filter(is_superuser=False, is_staff=False).delete()
        
        self.stdout.write(self.style.WARNING('⚠️  Sample data cleared'))

    def create_admin_user(self):
        """Create admin user if not exists"""
        admin_email = 'admin@promptcraft.com'
        admin_username = 'admin'
        
        user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'bio': 'PromptCraft Administrator',
                'credits': 1000,
                'level': 50,
                'experience_points': 5000,
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'👑 Admin user created: {admin_username}')
        else:
            self.stdout.write(f'👑 Admin user exists: {admin_username}')
        
        return user

    def create_categories(self):
        """Create template categories"""
        categories_data = [
            {
                'name': 'Business & Marketing',
                'slug': 'business-marketing', 
                'description': 'Templates for business communications, marketing copy, and professional content',
                'icon': '💼',
                'color': '#3B82F6',
                'order': 1
            },
            {
                'name': 'Content Creation',
                'slug': 'content-creation',
                'description': 'Blog posts, articles, social media content, and creative writing',
                'icon': '✍️',
                'color': '#10B981',
                'order': 2
            },
            {
                'name': 'Code & Development',
                'slug': 'code-development',
                'description': 'Programming prompts, code generation, debugging, and technical documentation',
                'icon': '💻',
                'color': '#8B5CF6',
                'order': 3
            },
            {
                'name': 'Education & Learning',
                'slug': 'education-learning',
                'description': 'Teaching materials, study guides, explanations, and educational content',
                'icon': '🎓',
                'color': '#F59E0B',
                'order': 4
            },
            {
                'name': 'Analysis & Research',
                'slug': 'analysis-research',
                'description': 'Data analysis, research summaries, and analytical frameworks',
                'icon': '📊',
                'color': '#EF4444',
                'order': 5
            },
            {
                'name': 'Personal & Lifestyle',
                'slug': 'personal-lifestyle',
                'description': 'Personal development, health, travel, and lifestyle content',
                'icon': '🌟',
                'color': '#EC4899',
                'order': 6
            }
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = TemplateCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories.append(category)
            
            if created:
                self.stdout.write(f'📂 Category created: {category.name}')
        
        return categories

    def create_sample_users(self, count):
        """Create sample users with realistic data"""
        self.stdout.write(f'👥 Creating {count} sample users...')
        
        sample_users_data = [
            ('sarah_johnson', 'Sarah', 'Johnson', 'Content strategist and marketing professional'),
            ('mike_developer', 'Mike', 'Chen', 'Full-stack developer and AI enthusiast'),
            ('emma_writer', 'Emma', 'Williams', 'Freelance writer specializing in tech content'),
            ('alex_designer', 'Alex', 'Rodriguez', 'UX designer and prompt engineering hobbyist'),
            ('lisa_educator', 'Lisa', 'Davis', 'Online educator and course creator'),
            ('david_analyst', 'David', 'Wilson', 'Business analyst and data scientist'),
            ('nina_consultant', 'Nina', 'Taylor', 'Management consultant and strategy advisor'),
            ('carlos_entrepreneur', 'Carlos', 'Garcia', 'Startup founder and innovation coach'),
            ('rachel_marketer', 'Rachel', 'Brown', 'Digital marketing specialist'),
            ('jason_researcher', 'Jason', 'Lee', 'Academic researcher and AI researcher'),
        ]
        
        users = []
        for i in range(min(count, len(sample_users_data))):
            username, first_name, last_name, bio = sample_users_data[i]
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'bio': bio,
                    'credits': random.randint(50, 500),
                    'level': random.randint(1, 25),
                    'experience_points': random.randint(0, 2500),
                    'daily_streak': random.randint(0, 30),
                    'templates_created': random.randint(0, 20),
                    'templates_completed': random.randint(0, 50),
                    'total_prompts_generated': random.randint(10, 500),
                }
            )
            
            if created:
                user.set_password('demo123')
                user.save()
            
            users.append(user)
        
        self.stdout.write(f'✅ Created {len(users)} users')
        return users

    def create_sample_templates(self, users, categories, count):
        """Create high-quality sample templates"""
        self.stdout.write(f'📝 Creating {count} sample templates...')
        
        sample_templates = [
            # Business & Marketing
            {
                'title': 'Professional Email Generator',
                'description': 'Create professional business emails for any situation with proper tone and structure.',
                'category_slug': 'business-marketing',
                'content': 'Write a professional email about {{topic}} to {{recipient}}. The tone should be {{tone}} and include {{key_points}}. The purpose is to {{purpose}}.',
                'tags': 'email, business, professional, communication',
                'is_featured': True,
                'fields': [
                    {'label': 'Topic', 'field_type': 'text', 'placeholder': 'Meeting request', 'is_required': True},
                    {'label': 'Recipient', 'field_type': 'text', 'placeholder': 'Client, colleague, manager', 'is_required': True},
                    {'label': 'Tone', 'field_type': 'dropdown', 'options': ['Formal', 'Friendly', 'Urgent', 'Casual'], 'is_required': True},
                    {'label': 'Key Points', 'field_type': 'textarea', 'placeholder': 'Main points to cover', 'is_required': True},
                    {'label': 'Purpose', 'field_type': 'text', 'placeholder': 'Request a meeting', 'is_required': True}
                ]
            },
            {
                'title': 'Social Media Post Creator',
                'description': 'Generate engaging social media posts for different platforms with hashtags and call-to-actions.',
                'category_slug': 'business-marketing',
                'content': 'Create a {{platform}} post about {{topic}}. Include relevant hashtags and a clear call-to-action. Style: {{style}}. Target audience: {{audience}}.',
                'tags': 'social media, marketing, content, engagement',
                'is_featured': True,
                'fields': [
                    {'label': 'Platform', 'field_type': 'dropdown', 'options': ['LinkedIn', 'Twitter', 'Instagram', 'Facebook'], 'is_required': True},
                    {'label': 'Topic', 'field_type': 'text', 'placeholder': 'Product launch', 'is_required': True},
                    {'label': 'Style', 'field_type': 'dropdown', 'options': ['Professional', 'Casual', 'Inspirational', 'Educational'], 'is_required': True},
                    {'label': 'Target Audience', 'field_type': 'text', 'placeholder': 'Small business owners', 'is_required': True}
                ]
            },
            
            # Content Creation
            {
                'title': 'Blog Post Outline Generator',
                'description': 'Create comprehensive blog post outlines with SEO-optimized structure and engaging content ideas.',
                'category_slug': 'content-creation',
                'content': 'Create a detailed blog post outline for "{{title}}" targeting {{audience}}. Include {{sections}} main sections, SEO keywords: {{keywords}}, and estimated word count: {{word_count}}.',
                'tags': 'blog, content, SEO, writing, outline',
                'is_featured': True,
                'fields': [
                    {'label': 'Blog Title', 'field_type': 'text', 'placeholder': 'How to Start a Successful Blog', 'is_required': True},
                    {'label': 'Target Audience', 'field_type': 'text', 'placeholder': 'Beginner bloggers', 'is_required': True},
                    {'label': 'Number of Sections', 'field_type': 'number', 'default_value': '5', 'is_required': True},
                    {'label': 'SEO Keywords', 'field_type': 'text', 'placeholder': 'blogging, content marketing', 'is_required': True},
                    {'label': 'Word Count', 'field_type': 'dropdown', 'options': ['500-800', '800-1200', '1200-2000', '2000+'], 'is_required': True}
                ]
            },
            
            # Code & Development
            {
                'title': 'Code Documentation Generator',
                'description': 'Generate comprehensive documentation for code functions and classes with examples.',
                'category_slug': 'code-development',
                'content': 'Write detailed documentation for this {{language}} {{code_type}}: {{code}}. Include purpose, parameters, return values, examples, and best practices.',
                'tags': 'documentation, code, programming, development',
                'is_featured': False,
                'fields': [
                    {'label': 'Programming Language', 'field_type': 'dropdown', 'options': ['Python', 'JavaScript', 'Java', 'C++', 'Other'], 'is_required': True},
                    {'label': 'Code Type', 'field_type': 'dropdown', 'options': ['Function', 'Class', 'Module', 'API'], 'is_required': True},
                    {'label': 'Code', 'field_type': 'textarea', 'placeholder': 'Paste your code here', 'is_required': True}
                ]
            },
            
            # Education & Learning
            {
                'title': 'Study Guide Creator',
                'description': 'Create comprehensive study guides with key concepts, practice questions, and memory aids.',
                'category_slug': 'education-learning',
                'content': 'Create a study guide for {{subject}} covering {{topics}}. Include key concepts, definitions, practice questions, and memory techniques for {{level}} students.',
                'tags': 'education, study, learning, guide',
                'is_featured': False,
                'fields': [
                    {'label': 'Subject', 'field_type': 'text', 'placeholder': 'Biology', 'is_required': True},
                    {'label': 'Topics', 'field_type': 'textarea', 'placeholder': 'Cell structure, photosynthesis', 'is_required': True},
                    {'label': 'Education Level', 'field_type': 'dropdown', 'options': ['High School', 'Undergraduate', 'Graduate', 'Professional'], 'is_required': True}
                ]
            },
            
            # Analysis & Research
            {
                'title': 'Market Research Analysis',
                'description': 'Analyze market research data and generate insights with actionable recommendations.',
                'category_slug': 'analysis-research',
                'content': 'Analyze this market research data for {{industry}}: {{data}}. Provide key insights, trends, opportunities, and actionable recommendations for {{business_type}}.',
                'tags': 'market research, analysis, business, insights',
                'is_featured': False,
                'fields': [
                    {'label': 'Industry', 'field_type': 'text', 'placeholder': 'E-commerce', 'is_required': True},
                    {'label': 'Research Data', 'field_type': 'textarea', 'placeholder': 'Survey results, statistics, etc.', 'is_required': True},
                    {'label': 'Business Type', 'field_type': 'text', 'placeholder': 'Startup, enterprise, SMB', 'is_required': True}
                ]
            },
        ]
        
        # Extend with more templates to reach target count
        extended_templates = []
        while len(extended_templates) < count:
            for template in sample_templates:
                if len(extended_templates) >= count:
                    break
                extended_templates.append(template.copy())
        
        created_count = 0
        for i, template_data in enumerate(extended_templates[:count]):
            try:
                # Find category
                category = next(cat for cat in categories if cat.slug == template_data['category_slug'])
                author = random.choice(users)
                
                # Create template
                template = Template.objects.create(
                    title=template_data['title'],
                    description=template_data['description'],
                    template_content=template_data['content'],  # Correct field name
                    category=category,
                    author=author,
                    tags=template_data['tags'].split(', '),  # Convert string to list
                    is_public=True,
                    is_featured=template_data.get('is_featured', False),
                    usage_count=random.randint(0, 100),
                    average_rating=round(random.uniform(3.5, 5.0), 1),
                    popularity_score=random.randint(0, 1000),
                )
                
                # Add fields
                for order, field_data in enumerate(template_data.get('fields', [])):
                    # Create the PromptField first
                    field = PromptField.objects.create(
                        order=order,
                        **field_data
                    )
                    # Link it to the template through TemplateField
                    TemplateField.objects.create(
                        template=template,
                        field=field,
                        order=order
                    )
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(f'❌ Error creating template {i}: {e}')
        
        self.stdout.write(f'✅ Created {created_count} templates')

    def print_summary(self, users_count, templates_count):
        """Print seeding summary"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 MVP DATABASE SEEDING SUMMARY'))
        self.stdout.write('='*50)
        
        # Count actual created data
        total_users = User.objects.count()
        total_categories = TemplateCategory.objects.count()
        total_templates = Template.objects.filter(is_active=True).count()
        
        self.stdout.write(f'👥 Users: {total_users} (including admin)')
        self.stdout.write(f'📂 Categories: {total_categories}')
        self.stdout.write(f'📝 Templates: {total_templates}')
        
        self.stdout.write('\n🔗 Access Information:')
        self.stdout.write('Admin Login: admin / admin123')
        self.stdout.write('Sample User: sarah_johnson / demo123')
        self.stdout.write('MVP API: /api/mvp/')
        self.stdout.write('API Docs: /api/schema/swagger-ui/')
        
        self.stdout.write('\n✨ Ready for professional MVP demonstration!')