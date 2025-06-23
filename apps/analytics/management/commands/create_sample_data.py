from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.templates.models import Template, TemplateCategory, PromptField, FieldType
from apps.gamification.models import Achievement, DailyChallenge
from django.utils import timezone
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for development'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')        # Create sample user - use integer ID for compatibility with existing database
        try:
            user = User.objects.get(username='demo_user')
        except User.DoesNotExist:
            # Create user with only basic fields to avoid UUID conflicts
            user = User.objects.create_user(
                username='demo_user',
                email='demo@promptcraft.app',
                first_name='Demo',
                last_name='User'
            )
            # Add custom fields if they exist (for compatibility)
            if hasattr(user, 'credits'):
                user.credits = 500
            if hasattr(user, 'level'):
                user.level = 3
            if hasattr(user, 'experience_points'):
                user.experience_points = 250
            if hasattr(user, 'user_rank'):
                user.user_rank = 'Prompt Apprentice'
            user.save()
        
        # Create categories
        categories = [
            {'name': 'Business Strategy', 'slug': 'business', 'color': '#6366F1', 'icon': 'business'},
            {'name': 'Creative Content', 'slug': 'creative', 'color': '#EC4899', 'icon': 'palette'},
            {'name': 'Software Engineering', 'slug': 'engineering', 'color': '#10B981', 'icon': 'code'},
            {'name': 'Education', 'slug': 'education', 'color': '#F59E0B', 'icon': 'school'},
            {'name': 'Marketing', 'slug': 'marketing', 'color': '#EF4444', 'icon': 'campaign'},
        ]
        
        for cat_data in categories:
            TemplateCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
        
        # Create sample templates
        business_cat = TemplateCategory.objects.get(slug='business')
        
        template, created = Template.objects.get_or_create(
            title='Business Plan Generator',
            defaults={
                'description': 'Create a comprehensive business plan with AI assistance',
                'category': business_cat,
                'author': user,
                'template_content': '''Create a business plan for:

Company Name: {{company_name}}
Industry: {{industry}}
Target Market: {{target_market}}
Business Model: {{business_model}}

Executive Summary:
{{executive_summary}}

Market Analysis:
{{market_analysis}}

Financial Projections:
{{financial_projections}}

Please provide a detailed business plan based on this information.''',
                'is_public': True,
                'is_featured': True,
                'popularity_score': 85.5
            }
        )
        
        if created:
            # Create fields for the template
            fields_data = [
                {'label': 'Company Name', 'placeholder': 'Enter your company name', 'field_type': FieldType.TEXT, 'is_required': True, 'order': 0},
                {'label': 'Industry', 'placeholder': 'Select industry', 'field_type': FieldType.DROPDOWN, 'options': ['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing'], 'is_required': True, 'order': 1},
                {'label': 'Target Market', 'placeholder': 'Describe your target market', 'field_type': FieldType.TEXTAREA, 'is_required': True, 'order': 2},
                {'label': 'Business Model', 'placeholder': 'Describe your business model', 'field_type': FieldType.TEXTAREA, 'is_required': True, 'order': 3},
                {'label': 'Executive Summary', 'placeholder': 'Brief executive summary', 'field_type': FieldType.TEXTAREA, 'order': 4},
                {'label': 'Market Analysis', 'placeholder': 'Market analysis details', 'field_type': FieldType.TEXTAREA, 'order': 5},
                {'label': 'Financial Projections', 'placeholder': 'Financial projections', 'field_type': FieldType.TEXTAREA, 'order': 6},
            ]
            
            for field_data in fields_data:
                field = PromptField.objects.create(**field_data)
                template.fields.add(field)
        
        # Create achievements
        achievements = [
            {
                'name': 'First Steps',
                'description': 'Create your first template',
                'requirement_type': 'templates_created',
                'requirement_value': 1,
                'credits_reward': 50,
                'experience_reward': 25,
                'category': 'getting_started',
                'rarity': 'common'
            },
            {
                'name': 'Template Master',
                'description': 'Create 10 templates',
                'requirement_type': 'templates_created',
                'requirement_value': 10,
                'credits_reward': 200,
                'experience_reward': 100,
                'category': 'creation',
                'rarity': 'rare'
            },
            {
                'name': 'Streak Champion',
                'description': 'Maintain a 7-day login streak',
                'requirement_type': 'daily_streak',
                'requirement_value': 7,
                'credits_reward': 100,
                'experience_reward': 50,
                'category': 'engagement',
                'rarity': 'epic'
            }
        ]
        
        for ach_data in achievements:
            Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
        
        # Create daily challenge
        today = timezone.now().date()
        DailyChallenge.objects.get_or_create(
            date=today,
            challenge_type='complete_templates',
            defaults={
                'title': 'Complete 3 Templates',
                'description': 'Generate prompts using 3 different templates today',
                'target_value': 3,
                'credits_reward': 75,
                'experience_reward': 40,
                'is_active': True
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
