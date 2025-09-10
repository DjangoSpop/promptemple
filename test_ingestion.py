"""
Test script to verify the MD ingestion system
Run this to test if the ingestion works correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.templates.services.md_ingestion_service import MarkdownIngestionManager

def test_ingestion():
    """Test the markdown ingestion system"""
    
    # Sample markdown content for testing
    test_markdown = """
# Business Plan Generator
**Category**: Business Development
**Target Audience**: Entrepreneurs, Startups
**Revenue Potential**: $10K-50K MRR

```
Create a comprehensive business plan for {{business_name}}, a {{business_type}} company targeting {{target_market}}.

**Executive Summary:**
{{business_name}} is a {{business_type}} that {{value_proposition}}. Our target market consists of {{target_market}} who need {{main_solution}}.

**Market Analysis:**
- Market Size: {{market_size}}
- Target Demographics: {{demographics}}
- Competition Analysis: {{competition_overview}}

**Revenue Model:**
- Primary Revenue Stream: {{revenue_stream}}
- Pricing Strategy: {{pricing_strategy}}
- Projected Monthly Revenue: ${{projected_revenue}}

**Marketing Strategy:**
- Digital Marketing: {{digital_strategy}}
- Content Marketing: {{content_strategy}}
- Partnership Strategy: {{partnership_strategy}}

**Financial Projections:**
- Year 1 Revenue: ${{year_1_revenue}}
- Year 2 Revenue: ${{year_2_revenue}}
- Break-even Point: {{breakeven_timeframe}}
```

## Social Media Campaign Creator
**Category**: Marketing
**Target Audience**: Marketers, Agencies

Create a {{campaign_duration}} social media campaign for {{brand_name}} targeting {{target_audience}}.

**Campaign Objectives:**
- Primary Goal: {{primary_goal}}
- Secondary Goal: {{secondary_goal}}
- Success Metrics: {{success_metrics}}

**Content Strategy:**
- Platform Focus: {{platforms}}
- Content Types: {{content_types}}
- Posting Frequency: {{posting_frequency}}

**Budget Allocation:**
- Total Budget: ${{total_budget}}
- Paid Ads: {{paid_percentage}}%
- Content Creation: {{content_percentage}}%
- Tools & Software: {{tools_percentage}}%
"""

    print("🚀 Testing Markdown Ingestion System")
    print("=" * 50)
    
    # Initialize the ingestion manager
    manager = MarkdownIngestionManager()
    
    # Test extraction
    print("📝 Testing prompt extraction...")
    prompts = manager.extractor._parse_markdown_content(test_markdown, 'test_source')
    
    print(f"✅ Extracted {len(prompts)} prompts")
    
    # Display extracted prompts
    for i, prompt in enumerate(prompts, 1):
        print(f"\n📋 Prompt {i}:")
        print(f"   Title: {prompt['title']}")
        print(f"   Category: {prompt['category']}")
        print(f"   Variables: {len(prompt['variables'])}")
        print(f"   Tags: {', '.join(prompt['tags'])}")
        
        # Show variables
        if prompt['variables']:
            print("   Variables:")
            for var in prompt['variables'][:3]:  # Show first 3
                print(f"     - {var['name']} ({var['type']})")
    
    print(f"\n🔄 Testing database ingestion...")
    
    # Test database ingestion (dry run concept)
    try:
        # Get stats before
        from apps.templates.models import Template, TemplateCategory
        templates_before = Template.objects.count()
        categories_before = TemplateCategory.objects.count()
        
        print(f"   Templates before: {templates_before}")
        print(f"   Categories before: {categories_before}")
        
        # Perform ingestion
        result = manager.ingestion_service.bulk_ingest_prompts(prompts)
        
        # Get stats after
        templates_after = Template.objects.count()
        categories_after = TemplateCategory.objects.count()
        
        print(f"   Templates after: {templates_after}")
        print(f"   Categories after: {categories_after}")
        
        print(f"\n📊 Ingestion Results:")
        print(f"   Successfully created: {result['successfully_created']}")
        print(f"   Skipped duplicates: {result['skipped_duplicates']}")
        print(f"   Errors: {result['errors']}")
        print(f"   Categories created: {result['categories_created']}")
        print(f"   Fields created: {result['fields_created']}")
        
        if result['successfully_created'] > 0:
            print("\n✅ Ingestion system working correctly!")
        else:
            print("\n⚠️  No templates were created. Check for duplicates or errors.")
            
    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ingestion()