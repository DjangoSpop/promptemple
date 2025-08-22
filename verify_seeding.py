#!/usr/bin/env python
"""
Verification script for the template seeding process
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField
from django.contrib.auth import get_user_model

User = get_user_model()

def main():
    print("🎯 DATABASE SEEDING VERIFICATION")
    print("=" * 50)
    
    # Check counts
    template_count = Template.objects.count()
    category_count = TemplateCategory.objects.count()
    field_count = PromptField.objects.count()
    user_count = User.objects.count()
    
    print(f"📊 SUMMARY:")
    print(f"   🎨 Templates: {template_count}")
    print(f"   📂 Categories: {category_count}")
    print(f"   📝 Fields: {field_count}")
    print(f"   👥 Users: {user_count}")
    
    print(f"\n📋 CATEGORIES:")
    for category in TemplateCategory.objects.all().order_by('name'):
        template_count = category.templates.count()
        print(f"   {category.icon} {category.name}: {template_count} templates")
    
    print(f"\n🎨 TEMPLATES BY CATEGORY:")
    for category in TemplateCategory.objects.all().order_by('name'):
        print(f"\n📂 {category.name} ({category.templates.count()} templates):")
        for template in category.templates.all().order_by('title'):
            field_count = template.fields.count()
            print(f"   ✨ {template.title}")
            print(f"      Version: {template.version}")
            print(f"      Fields: {field_count}")
            print(f"      Tags: {', '.join(template.tags) if template.tags else 'None'}")
            print(f"      Public: {'Yes' if template.is_public else 'No'}")
            print(f"      Featured: {'Yes' if template.is_featured else 'No'}")
    
    print(f"\n👑 ADMIN USER:")
    admin = User.objects.filter(is_superuser=True).first()
    if admin:
        created_count = admin.created_templates.count()
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Created Templates: {created_count}")
        print(f"   Credits: {getattr(admin, 'credits', 'N/A')}")
        print(f"   Level: {getattr(admin, 'level', 'N/A')}")
        print(f"   Rank: {getattr(admin, 'user_rank', 'N/A')}")
    else:
        print("   No admin user found")
    
    print(f"\n📝 FIELD ANALYSIS:")
    field_types = PromptField.objects.values_list('field_type', flat=True)
    from collections import Counter
    type_counts = Counter(field_types)
    for field_type, count in type_counts.items():
        print(f"   {field_type}: {count} fields")
    
    print(f"\n🔗 TEMPLATE-FIELD RELATIONSHIPS:")
    template_fields = TemplateField.objects.count()
    print(f"   Total Template-Field associations: {template_fields}")
    
    # Check for templates with most fields
    print(f"\n🏆 TOP TEMPLATES BY FIELD COUNT:")
    for template in Template.objects.all():
        field_count = template.fields.count()
        print(f"   {template.title}: {field_count} fields")
    
    print(f"\n✅ VERIFICATION COMPLETE!")
    print("=" * 50)

if __name__ == "__main__":
    main()