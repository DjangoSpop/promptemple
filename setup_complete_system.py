# setup_complete_system.py
"""
Complete setup script for the enhanced chat system with template extraction and monetization
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def setup_complete_system():
    """Set up the complete enhanced chat system"""
    
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
    
    # 3. Create template categories
    print("\n📁 Setting up template categories...")
    try:
        setup_template_categories()
        print("✅ Template categories created")
    except Exception as e:
        print(f"❌ Template categories setup failed: {e}")
    
    # 4. Create template access tiers
    print("\n🎯 Setting up template access tiers...")
    try:
        setup_template_access_tiers()
        print("✅ Template access tiers created")
    except Exception as e:
        print(f"❌ Template access tiers setup failed: {e}")
    
    # 5. Create extraction rules
    print("\n🔍 Setting up template extraction rules...")
    try:
        setup_extraction_rules()
        print("✅ Template extraction rules created")
    except Exception as e:
        print(f"❌ Template extraction rules setup failed: {e}")
    
    # 6. Create admin user
    print("\n👤 Setting up admin user...")
    try:
        admin_user = setup_admin_user()
        print(f"✅ Admin user created: {admin_user.username}")
    except Exception as e:
        print(f"❌ Admin user setup failed: {e}")
    
    # 7. Test API configuration
    print("\n🔧 Testing API configuration...")
    try:
        test_api_configuration()
        print("✅ API configuration verified")
    except Exception as e:
        print(f"⚠️  API configuration warning: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start Celery worker: celery -A celery_config worker --loglevel=info")
    print("2. Start Celery beat: celery -A celery_config beat --loglevel=info")
    print("3. Start Django server: python manage.py runserver")
    print("4. Test the enhanced chat endpoint: /api/v2/chat/completions/")
    print("\nTemplate extraction will happen automatically for new chat messages!")


def setup_subscription_plans():
    """Create default subscription plans"""
    from monetization_models import SubscriptionPlan
    
    plans = [
        {
            'name': 'Free',
            'slug': 'free',
            'plan_type': 'free',
            'billing_cycle': 'monthly',
            'price': Decimal('0.00'),
            'description': 'Get started with basic template access',
            'monthly_template_generations': 50,
            'monthly_ai_requests': 20,
            'max_saved_templates': 10,
            'max_custom_categories': 1,
            'access_premium_templates': False,
            'template_export_enabled': False,
            'api_access_enabled': False,
            'priority_support': False,
            'custom_branding': False,
            'is_active': True,
            'highlight_color': '#6B7280',
            'order': 1
        },
        {
            'name': 'Pro',
            'slug': 'pro',
            'plan_type': 'pro',
            'billing_cycle': 'monthly',
            'price': Decimal('29.99'),
            'description': 'Professional template library with premium features',
            'monthly_template_generations': 500,
            'monthly_ai_requests': 200,
            'max_saved_templates': 100,
            'max_custom_categories': 10,
            'access_premium_templates': True,
            'template_export_enabled': True,
            'api_access_enabled': True,
            'priority_support': True,
            'custom_branding': False,
            'is_active': True,
            'is_featured': True,
            'highlight_color': '#7C3AED',
            'order': 2
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'plan_type': 'enterprise',
            'billing_cycle': 'monthly',
            'price': Decimal('99.99'),
            'description': 'Advanced features for teams and businesses',
            'monthly_template_generations': 2000,
            'monthly_ai_requests': 1000,
            'max_saved_templates': 500,
            'max_custom_categories': 50,
            'access_premium_templates': True,
            'template_export_enabled': True,
            'api_access_enabled': True,
            'priority_support': True,
            'custom_branding': True,
            'is_active': True,
            'highlight_color': '#DC2626',
            'order': 3
        }
    ]
    
    for plan_data in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults=plan_data
        )
        if created:
            print(f"  ✓ Created plan: {plan.name}")


def setup_template_categories():
    """Create template categories"""
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
            'name': 'AI Extracted',
            'slug': 'ai-extracted',
            'description': 'High-quality templates extracted from AI conversations',
            'icon': 'auto_awesome',
            'color': '#F59E0B',
            'order': 5
        }
    ]
    
    for category_data in categories:
        category, created = TemplateCategory.objects.get_or_create(
            slug=category_data['slug'],
            defaults=category_data
        )
        if created:
            print(f"  ✓ Created category: {category.name}")


def setup_template_access_tiers():
    """Create template access tiers"""
    from monetization_models import TemplateAccessTier, SubscriptionPlan
    
    try:
        pro_plan = SubscriptionPlan.objects.get(slug='pro')
        enterprise_plan = SubscriptionPlan.objects.get(slug='enterprise')
    except SubscriptionPlan.DoesNotExist:
        print("  ⚠️  Subscription plans not found, creating basic tiers")
        pro_plan = None
        enterprise_plan = None
    
    tiers = [
        {
            'name': 'Free',
            'tier_type': 'free',
            'price_per_template': Decimal('0.00'),
            'credits_required': 0,
            'min_subscription_plan': None,
            'description': 'Basic templates available to all users',
            'features': ['Basic templates', 'Community support'],
            'color': '#6B7280',
            'icon': 'public',
            'order': 1
        },
        {
            'name': 'Premium',
            'tier_type': 'premium',
            'price_per_template': Decimal('2.99'),
            'credits_required': 50,
            'min_subscription_plan': pro_plan,
            'description': 'High-quality curated templates',
            'features': ['Curated templates', 'Advanced features', 'Priority support'],
            'color': '#7C3AED',
            'icon': 'star',
            'order': 2
        },
        {
            'name': 'Enterprise',
            'tier_type': 'enterprise',
            'price_per_template': Decimal('9.99'),
            'credits_required': 150,
            'min_subscription_plan': enterprise_plan,
            'description': 'Enterprise-grade templates with advanced features',
            'features': ['Enterprise templates', 'Custom branding', 'API access', 'Dedicated support'],
            'color': '#DC2626',
            'icon': 'business_center',
            'order': 3
        }
    ]
    
    for tier_data in tiers:
        tier, created = TemplateAccessTier.objects.get_or_create(
            tier_type=tier_data['tier_type'],
            defaults=tier_data
        )
        if created:
            print(f"  ✓ Created access tier: {tier.name}")


def setup_extraction_rules():
    """Create template extraction rules"""
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
    admin_user, created = User.objects.get_or_create(
        username='template_admin',
        defaults={
            'email': 'admin@promptcraft.local',
            'first_name': 'Template',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
            'is_premium': True,
            'credits': 1000
        }
    )
    
    if created:
        admin_user.set_password('admin123')  # Change this in production!
        admin_user.save()
        
        # Create free subscription for admin
        try:
            from monetization_models import SubscriptionPlan
            from monetization_services import subscription_service
            
            free_plan = SubscriptionPlan.objects.get(slug='free')
            subscription_service.create_subscription(admin_user, free_plan)
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


if __name__ == '__main__':
    setup_complete_system()