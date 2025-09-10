# setup_enhanced_system.py
"""
Enhanced setup script for the template extraction and monetization system
Uses existing Django apps structure
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def setup_enhanced_system():
    """Set up the enhanced chat system with existing Django apps"""
    
    print("🚀 Setting up Enhanced Chat System with Template Extraction & Monetization")
    print("=" * 80)
    
    # 1. Database setup
    print("\n📊 Setting up database...")
    try:
        # Generate migrations for all apps
        call_command('makemigrations', verbosity=1)
        
        # Apply migrations
        call_command('migrate', verbosity=1)
        print("✅ Database setup completed")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    # 2. Create subscription plans
    print("\n💰 Setting up subscription plans...")
    try:
        setup_subscription_plans()
        print("✅ Subscription plans created")
    except Exception as e:
        print(f"❌ Subscription plans setup failed: {e}")
    
    # 3. Create template extraction rules
    print("\n🔍 Setting up template extraction rules...")
    try:
        setup_extraction_rules()
        print("✅ Template extraction rules created")
    except Exception as e:
        print(f"❌ Template extraction rules setup failed: {e}")
    
    # 4. Create admin user with proper subscription
    print("\n👤 Setting up admin user...")
    try:
        admin_user = setup_admin_user()
        print(f"✅ Admin user created: {admin_user.username}")
    except Exception as e:
        print(f"❌ Admin user setup failed: {e}")
    
    # 5. Test API configuration
    print("\n🔧 Testing API configuration...")
    try:
        test_api_configuration()
        print("✅ API configuration verified")
    except Exception as e:
        print(f"⚠️  API configuration warning: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 Enhanced System Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start Celery worker: celery -A celery_config worker --loglevel=info")
    print("2. Start Celery beat: celery -A celery_config beat --loglevel=info")
    print("3. Start Django server: python manage.py runserver")
    print("4. Test the enhanced chat endpoint: /api/v2/chat/completions/")
    print("\nTemplate extraction will happen automatically for new chat messages!")
    return True


def setup_subscription_plans():
    """Create default subscription plans using billing app"""
    from apps.billing.models import SubscriptionPlan
    
    plans = [
        {
            'name': 'Free Plan',
            'plan_type': 'free',
            'billing_interval': 'monthly',
            'price': Decimal('0.00'),
            'description': 'Get started with basic template access',
            'daily_template_limit': 5,
            'daily_copy_limit': 3,
            'premium_templates_access': False,
            'ads_free': False,
            'priority_support': False,
            'analytics_access': False,
            'api_access': False,
            'collaboration_features': False,
            'is_active': True,
        },
        {
            'name': 'Pro Plan',
            'plan_type': 'premium',
            'billing_interval': 'monthly',
            'price': Decimal('29.99'),
            'description': 'Professional template library with premium features',
            'daily_template_limit': 50,
            'daily_copy_limit': 30,
            'premium_templates_access': True,
            'ads_free': True,
            'priority_support': True,
            'analytics_access': True,
            'api_access': True,
            'collaboration_features': False,
            'is_active': True,
            'is_popular': True,
        },
        {
            'name': 'Enterprise Plan',
            'plan_type': 'enterprise',
            'billing_interval': 'monthly',
            'price': Decimal('99.99'),
            'description': 'Advanced features for teams and businesses',
            'daily_template_limit': 200,
            'daily_copy_limit': 100,
            'premium_templates_access': True,
            'ads_free': True,
            'priority_support': True,
            'analytics_access': True,
            'api_access': True,
            'collaboration_features': True,
            'is_active': True,
        }
    ]
    
    for plan_data in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            plan_type=plan_data['plan_type'],
            defaults=plan_data
        )
        if created:
            print(f"  ✓ Created plan: {plan.name}")


def setup_extraction_rules():
    """Create template extraction rules using chat app"""
    from apps.chat.models import TemplateExtractionRule
    
    rules = [
        {
            'name': 'High-Value Business Templates',
            'description': 'Extract templates containing business and monetization keywords',
            'rule_type': 'keyword',
            'rule_config': {
                'keywords': ['business', 'monetization', 'revenue', 'profit', 'sales', 'marketing'],
                'minimum_keywords': 2,
                'boost_score': 0.2
            },
            'minimum_confidence': 0.6,
            'auto_approve_threshold': 0.8,
            'priority': 1
        },
        {
            'name': 'Numbered Prompt Collections',
            'description': 'Extract numbered prompt lists and collections',
            'rule_type': 'pattern',
            'rule_config': {
                'patterns': [r'\d+\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)'],
                'minimum_matches': 5
            },
            'minimum_confidence': 0.8,
            'auto_approve_threshold': 0.9,
            'priority': 2
        },
        {
            'name': 'Act As Templates',
            'description': 'Extract "Act as" and role-based prompt templates',
            'rule_type': 'pattern',
            'rule_config': {
                'patterns': [r'(Act as|You are|As a)\s*(.+?)(?=\n\n|\Z)'],
                'minimum_length': 50
            },
            'minimum_confidence': 0.7,
            'auto_approve_threshold': 0.85,
            'priority': 3
        },
        {
            'name': 'LangChain Analysis',
            'description': 'Use LangChain for semantic template analysis',
            'rule_type': 'langchain',
            'rule_config': {
                'use_embeddings': True,
                'similarity_threshold': 0.75,
                'quality_factors': ['clarity', 'usefulness', 'specificity']
            },
            'minimum_confidence': 0.65,
            'auto_approve_threshold': 0.85,
            'priority': 4
        }
    ]
    
    for rule_data in rules:
        rule, created = TemplateExtractionRule.objects.get_or_create(
            name=rule_data['name'],
            defaults=rule_data
        )
        if created:
            print(f"  ✓ Created extraction rule: {rule.name}")


def setup_admin_user():
    """Create admin user for template moderation"""
    from apps.billing.models import SubscriptionPlan, UserSubscription
    
    admin_user, created = User.objects.get_or_create(
        username='template_admin',
        defaults={
            'email': 'admin@promptcraft.local',
            'first_name': 'Template',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        admin_user.set_password('admin123')  # Change this in production!
        admin_user.save()
        
        # Create free subscription for admin
        try:
            free_plan = SubscriptionPlan.objects.filter(plan_type='free').first()
            if free_plan:
                subscription, sub_created = UserSubscription.objects.get_or_create(
                    user=admin_user,
                    defaults={
                        'plan': free_plan,
                        'status': 'active',
                        'started_at': timezone.now(),
                    }
                )
                if sub_created:
                    print(f"  ✓ Created subscription for admin user")
        except Exception as e:
            print(f"  ⚠️  Could not create subscription for admin: {e}")
    
    return admin_user


def test_api_configuration():
    """Test API configuration"""
    from django.conf import settings
    
    # Check DeepSeek configuration
    deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
    if not deepseek_config.get('API_KEY'):
        raise Exception("DeepSeek API key not configured")
    
    if not deepseek_config.get('BASE_URL'):
        raise Exception("DeepSeek base URL not configured")
    
    print(f"  ✓ DeepSeek API configured: {deepseek_config.get('BASE_URL')}")
    
    # Check Celery configuration
    celery_broker = getattr(settings, 'CELERY_BROKER_URL', None)
    if celery_broker:
        print(f"  ✓ Celery broker configured: {celery_broker}")
    else:
        print("  ⚠️  Celery broker not configured - background tasks won't work")


def create_template_preferences_for_existing_users():
    """Create template preferences for existing users"""
    from apps.chat.models import UserTemplatePreference
    
    users_without_preferences = User.objects.filter(template_preferences__isnull=True)
    count = 0
    
    for user in users_without_preferences:
        UserTemplatePreference.objects.create(
            user=user,
            auto_extract_enabled=True,
            auto_approve_high_confidence=False,
            notification_on_extraction=True,
            contribute_to_public_library=True,
            allow_template_sharing=True,
            minimum_quality_threshold='medium'
        )
        count += 1
    
    if count > 0:
        print(f"  ✓ Created template preferences for {count} existing users")


if __name__ == '__main__':
    setup_enhanced_system()