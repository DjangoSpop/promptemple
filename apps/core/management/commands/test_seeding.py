"""
Simple MVP seeding test to isolate the issue
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.templates.models import TemplateCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Test seeding with minimal data to isolate issues'

    def handle(self, *args, **options):
        """Test basic creation"""
        self.stdout.write('🧪 Testing basic model creation...')
        
        try:
            # Test user creation
            user, created = User.objects.get_or_create(
                username='test_user',
                defaults={'email': 'test@example.com'}
            )
            self.stdout.write(f'✅ User creation: {user.username}')
            
            # Test category creation
            category, created = TemplateCategory.objects.get_or_create(
                slug='test-category',
                defaults={
                    'name': 'Test Category',
                    'description': 'Test category description'
                }
            )
            self.stdout.write(f'✅ Category creation: {category.name}')
            
            # Test simple template creation (without fields first)
            from apps.templates.models import Template
            
            template_data = {
                'title': 'Simple Test Template',
                'description': 'A simple test template',
                'template_content': 'Hello {{name}}!',
                'category': category,
                'author': user,
                'tags': ['test'],
                'is_public': True
            }
            
            template = Template.objects.create(**template_data)
            self.stdout.write(f'✅ Template creation: {template.title}')
            
            self.stdout.write('✅ All basic tests passed!')
            
        except Exception as e:
            self.stdout.write(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()