"""
Management command to seed the database with mock templates for development and testing
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with mock templates for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting template seeding...'))

        if options['clear']:
            self.stdout.write('Clearing existing templates...')
            Template.objects.all().delete()
            TemplateCategory.objects.all().delete()
            PromptField.objects.all().delete()

        with transaction.atomic():
            # Create categories
            categories = self.create_categories()
            
            # Get or create admin user
            admin_user = self.get_or_create_admin_user()
            
            # Create templates
            self.create_mock_templates(categories, admin_user)

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded templates!')
        )

    def create_categories(self):
        """Create template categories"""
        self.stdout.write('Creating categories...')
        
        categories_data = [
            {
                'name': 'Content Creation',
                'slug': 'content-creation',
                'description': 'Templates for creating engaging content across various platforms',
                'icon': 'edit',
                'color': '#3B82F6',
                'order': 1
            },
            {
                'name': 'Marketing',
                'slug': 'marketing',
                'description': 'Marketing and advertising templates for campaigns and strategies',
                'icon': 'megaphone',
                'color': '#EF4444',
                'order': 2
            },
            {
                'name': 'Business',
                'slug': 'business',
                'description': 'Professional business templates for presentations and documents',
                'icon': 'briefcase',
                'color': '#10B981',
                'order': 3
            },
            {
                'name': 'Education',
                'slug': 'education',
                'description': 'Educational templates for learning and teaching',
                'icon': 'academic-cap',
                'color': '#F59E0B',
                'order': 4
            },
            {
                'name': 'Creative Writing',
                'slug': 'creative-writing',
                'description': 'Templates for creative writing and storytelling',
                'icon': 'pencil',
                'color': '#8B5CF6',
                'order': 5
            },
            {
                'name': 'Technical',
                'slug': 'technical',
                'description': 'Technical documentation and code-related templates',
                'icon': 'code',
                'color': '#6B7280',
                'order': 6
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = TemplateCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'  Created category: {category.name}')
        
        return categories

    def get_or_create_admin_user(self):
        """Get or create admin user for templates"""
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@promptcraft.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')
        return admin_user

    def create_mock_templates(self, categories, admin_user):
        """Create mock templates with realistic data"""
        self.stdout.write('Creating templates...')
        
        templates_data = [
            # Content Creation Templates
            {
                'title': 'Blog Post Writer',
                'description': 'Create engaging blog posts with proper structure, SEO optimization, and compelling content that resonates with your target audience.',
                'category': 'content-creation',
                'template_content': '''# {{title}}

## Introduction
{{introduction}}

## Main Content
{{main_content}}

{{#sections}}
### {{section_title}}
{{section_content}}
{{/sections}}

## Conclusion
{{conclusion}}

**Tags:** {{tags}}
**Target Audience:** {{target_audience}}''',
                'tags': ['blog', 'content', 'seo', 'writing'],
                'is_featured': True,
                'fields': [
                    {'label': 'Blog Title', 'type': 'text', 'placeholder': 'Enter your blog post title...', 'required': True},
                    {'label': 'Introduction', 'type': 'textarea', 'placeholder': 'Write a compelling introduction...', 'required': True},
                    {'label': 'Main Content', 'type': 'textarea', 'placeholder': 'Write the main content of your blog post...', 'required': True},
                    {'label': 'Conclusion', 'type': 'textarea', 'placeholder': 'Summarize and conclude your post...', 'required': True},
                    {'label': 'Tags', 'type': 'text', 'placeholder': 'Enter relevant tags, separated by commas...'},
                    {'label': 'Target Audience', 'type': 'dropdown', 'options': ['General Public', 'Professionals', 'Students', 'Entrepreneurs', 'Tech Enthusiasts'], 'required': True}
                ]
            },
            {
                'title': 'Social Media Post Generator',
                'description': 'Generate engaging social media posts optimized for different platforms with hashtags and call-to-action elements.',
                'category': 'content-creation',
                'template_content': '''🚀 {{content}}

{{#include_hashtags}}
#{{hashtags}}
{{/include_hashtags}}

{{#include_cta}}
👉 {{call_to_action}}
{{/include_cta}}

Platform: {{platform}}
Tone: {{tone}}''',
                'tags': ['social-media', 'marketing', 'engagement'],
                'is_featured': True,
                'fields': [
                    {'label': 'Post Content', 'type': 'textarea', 'placeholder': 'What do you want to share?', 'required': True},
                    {'label': 'Platform', 'type': 'dropdown', 'options': ['Instagram', 'Twitter', 'LinkedIn', 'Facebook', 'TikTok'], 'required': True},
                    {'label': 'Tone', 'type': 'dropdown', 'options': ['Professional', 'Casual', 'Funny', 'Inspirational', 'Educational']},
                    {'label': 'Hashtags', 'type': 'text', 'placeholder': 'Enter hashtags without # symbol'},
                    {'label': 'Call to Action', 'type': 'text', 'placeholder': 'What action do you want users to take?'},
                    {'label': 'Include Hashtags', 'type': 'checkbox', 'options': ['Yes']},
                    {'label': 'Include CTA', 'type': 'checkbox', 'options': ['Yes']}
                ]
            },
            
            # Marketing Templates
            {
                'title': 'Email Marketing Campaign',
                'description': 'Create compelling email marketing campaigns with personalized subject lines, engaging content, and clear calls-to-action.',
                'category': 'marketing',
                'template_content': '''Subject: {{subject_line}}

Hi {{recipient_name}},

{{opening_message}}

{{main_message}}

{{#benefits}}
✅ {{benefit}}
{{/benefits}}

{{call_to_action}}

Best regards,
{{sender_name}}
{{company_name}}

{{#unsubscribe}}
Unsubscribe | Update Preferences
{{/unsubscribe}}''',
                'tags': ['email', 'marketing', 'campaign', 'conversion'],
                'fields': [
                    {'label': 'Subject Line', 'type': 'text', 'placeholder': 'Write a compelling subject line...', 'required': True},
                    {'label': 'Recipient Name', 'type': 'text', 'placeholder': 'How to address the recipient?'},
                    {'label': 'Opening Message', 'type': 'textarea', 'placeholder': 'Start with a personal greeting...', 'required': True},
                    {'label': 'Main Message', 'type': 'textarea', 'placeholder': 'What is your main message?', 'required': True},
                    {'label': 'Call to Action', 'type': 'text', 'placeholder': 'What action do you want them to take?', 'required': True},
                    {'label': 'Sender Name', 'type': 'text', 'placeholder': 'Your name', 'required': True},
                    {'label': 'Company Name', 'type': 'text', 'placeholder': 'Your company name'}
                ]
            },
            {
                'title': 'Product Launch Announcement',
                'description': 'Announce your new product launch with excitement, key features, and launch details that drive interest and sales.',
                'category': 'marketing',
                'template_content': '''🎉 Introducing {{product_name}}! 🎉

{{announcement_message}}

🌟 Key Features:
{{#features}}
• {{feature}}
{{/features}}

💡 Perfect for: {{target_audience}}

🚀 Launch Details:
📅 Launch Date: {{launch_date}}
💰 Price: {{price}}
🎁 Special Offer: {{special_offer}}

{{call_to_action}}

{{#social_proof}}
"{{testimonial}}" - {{customer_name}}
{{/social_proof}}''',
                'tags': ['product-launch', 'announcement', 'features'],
                'is_featured': True,
                'fields': [
                    {'label': 'Product Name', 'type': 'text', 'placeholder': 'What is your product called?', 'required': True},
                    {'label': 'Announcement Message', 'type': 'textarea', 'placeholder': 'Write an exciting announcement...', 'required': True},
                    {'label': 'Target Audience', 'type': 'text', 'placeholder': 'Who is this product for?'},
                    {'label': 'Launch Date', 'type': 'text', 'placeholder': 'When are you launching?'},
                    {'label': 'Price', 'type': 'text', 'placeholder': 'What is the price?'},
                    {'label': 'Special Offer', 'type': 'text', 'placeholder': 'Any launch special offers?'},
                    {'label': 'Call to Action', 'type': 'text', 'placeholder': 'What should people do next?', 'required': True}
                ]
            },
            
            # Business Templates
            {
                'title': 'Business Proposal Template',
                'description': 'Create professional business proposals with executive summary, project scope, timeline, and pricing details.',
                'category': 'business',
                'template_content': '''# Business Proposal

**To:** {{client_name}}
**From:** {{company_name}}
**Date:** {{proposal_date}}
**Project:** {{project_name}}

## Executive Summary
{{executive_summary}}

## Project Scope
{{project_scope}}

## Deliverables
{{#deliverables}}
• {{deliverable}}
{{/deliverables}}

## Timeline
{{timeline}}

## Investment
{{pricing_details}}

## Why Choose Us
{{why_choose_us}}

## Next Steps
{{next_steps}}

---
{{contact_information}}''',
                'tags': ['business', 'proposal', 'professional'],
                'fields': [
                    {'label': 'Client Name', 'type': 'text', 'placeholder': 'Client or company name', 'required': True},
                    {'label': 'Company Name', 'type': 'text', 'placeholder': 'Your company name', 'required': True},
                    {'label': 'Project Name', 'type': 'text', 'placeholder': 'Name of the project', 'required': True},
                    {'label': 'Executive Summary', 'type': 'textarea', 'placeholder': 'Brief overview of the proposal...', 'required': True},
                    {'label': 'Project Scope', 'type': 'textarea', 'placeholder': 'Detailed scope of work...', 'required': True},
                    {'label': 'Timeline', 'type': 'text', 'placeholder': 'Project timeline and milestones'},
                    {'label': 'Pricing Details', 'type': 'textarea', 'placeholder': 'Breakdown of costs...'},
                    {'label': 'Why Choose Us', 'type': 'textarea', 'placeholder': 'Your unique value proposition...'},
                    {'label': 'Next Steps', 'type': 'text', 'placeholder': 'What happens after approval?'},
                    {'label': 'Contact Information', 'type': 'textarea', 'placeholder': 'Your contact details...'}
                ]
            },
            {
                'title': 'Meeting Agenda Template',
                'description': 'Structure productive meetings with clear agendas, time allocations, and action items tracking.',
                'category': 'business',
                'template_content': '''# {{meeting_title}}

**Date:** {{meeting_date}}
**Time:** {{meeting_time}}
**Location:** {{location}}
**Attendees:** {{attendees}}

## Agenda Items

{{#agenda_items}}
### {{item_title}} ({{duration}} minutes)
**Presenter:** {{presenter}}
**Objective:** {{objective}}

{{/agenda_items}}

## Action Items
| Task | Assigned To | Due Date | Status |
|------|-------------|----------|--------|
{{#action_items}}
| {{task}} | {{assignee}} | {{due_date}} | {{status}} |
{{/action_items}}

## Notes
{{notes}}

## Next Meeting
**Date:** {{next_meeting_date}}
**Agenda Preview:** {{next_agenda}}''',
                'tags': ['meeting', 'agenda', 'productivity'],
                'fields': [
                    {'label': 'Meeting Title', 'type': 'text', 'placeholder': 'What is this meeting about?', 'required': True},
                    {'label': 'Meeting Date', 'type': 'text', 'placeholder': 'When is the meeting?', 'required': True},
                    {'label': 'Meeting Time', 'type': 'text', 'placeholder': 'What time does it start?'},
                    {'label': 'Location', 'type': 'text', 'placeholder': 'Where is the meeting?'},
                    {'label': 'Attendees', 'type': 'textarea', 'placeholder': 'Who will attend?'},
                    {'label': 'Notes', 'type': 'textarea', 'placeholder': 'Additional notes or preparation needed...'}
                ]
            },
            
            # Education Templates
            {
                'title': 'Lesson Plan Template',
                'description': 'Create comprehensive lesson plans with learning objectives, activities, and assessment methods.',
                'category': 'education',
                'template_content': '''# Lesson Plan: {{lesson_title}}

**Subject:** {{subject}}
**Grade Level:** {{grade_level}}
**Duration:** {{duration}}
**Date:** {{lesson_date}}

## Learning Objectives
By the end of this lesson, students will be able to:
{{#objectives}}
• {{objective}}
{{/objectives}}

## Materials Needed
{{materials}}

## Lesson Structure

### Introduction ({{intro_time}} minutes)
{{introduction_activity}}

### Main Activity ({{main_time}} minutes)
{{main_activity}}

### Conclusion ({{conclusion_time}} minutes)
{{conclusion_activity}}

## Assessment Methods
{{assessment_methods}}

## Homework/Extension Activities
{{homework}}

## Notes for Next Lesson
{{notes_next_lesson}}''',
                'tags': ['education', 'lesson-plan', 'teaching'],
                'fields': [
                    {'label': 'Lesson Title', 'type': 'text', 'placeholder': 'What is this lesson about?', 'required': True},
                    {'label': 'Subject', 'type': 'dropdown', 'options': ['Math', 'Science', 'English', 'History', 'Art', 'Music', 'PE', 'Other'], 'required': True},
                    {'label': 'Grade Level', 'type': 'text', 'placeholder': 'Which grade level?', 'required': True},
                    {'label': 'Duration', 'type': 'text', 'placeholder': 'How long is the lesson?'},
                    {'label': 'Materials', 'type': 'textarea', 'placeholder': 'What materials are needed?'},
                    {'label': 'Introduction Activity', 'type': 'textarea', 'placeholder': 'How will you start the lesson?', 'required': True},
                    {'label': 'Main Activity', 'type': 'textarea', 'placeholder': 'What is the main learning activity?', 'required': True},
                    {'label': 'Conclusion Activity', 'type': 'textarea', 'placeholder': 'How will you wrap up?'},
                    {'label': 'Assessment Methods', 'type': 'textarea', 'placeholder': 'How will you assess learning?'},
                    {'label': 'Homework', 'type': 'textarea', 'placeholder': 'Any homework or extension activities?'}
                ]
            },
            
            # Creative Writing Templates
            {
                'title': 'Character Development Worksheet',
                'description': 'Develop rich, complex characters for your stories with detailed backgrounds, motivations, and character arcs.',
                'category': 'creative-writing',
                'template_content': '''# Character Profile: {{character_name}}

## Basic Information
**Full Name:** {{full_name}}
**Age:** {{age}}
**Occupation:** {{occupation}}
**Location:** {{location}}

## Physical Description
{{physical_description}}

## Personality
**Core Traits:** {{personality_traits}}
**Strengths:** {{strengths}}
**Weaknesses:** {{weaknesses}}
**Fears:** {{fears}}

## Background
**Family:** {{family_background}}
**Education:** {{education}}
**Life Events:** {{key_life_events}}

## Story Role
**Goal:** {{character_goal}}
**Motivation:** {{motivation}}
**Conflict:** {{internal_conflict}}
**Character Arc:** {{character_arc}}

## Dialogue Style
{{dialogue_notes}}

## Additional Notes
{{additional_notes}}''',
                'tags': ['creative-writing', 'character', 'storytelling'],
                'fields': [
                    {'label': 'Character Name', 'type': 'text', 'placeholder': 'What is your character called?', 'required': True},
                    {'label': 'Full Name', 'type': 'text', 'placeholder': 'Full legal name'},
                    {'label': 'Age', 'type': 'number', 'placeholder': 'How old are they?'},
                    {'label': 'Occupation', 'type': 'text', 'placeholder': 'What do they do for work?'},
                    {'label': 'Location', 'type': 'text', 'placeholder': 'Where do they live?'},
                    {'label': 'Physical Description', 'type': 'textarea', 'placeholder': 'Describe their appearance...'},
                    {'label': 'Personality Traits', 'type': 'textarea', 'placeholder': 'What are their main personality traits?'},
                    {'label': 'Character Goal', 'type': 'textarea', 'placeholder': 'What does this character want?', 'required': True},
                    {'label': 'Motivation', 'type': 'textarea', 'placeholder': 'Why do they want this?', 'required': True}
                ]
            },
            
            # Technical Templates
            {
                'title': 'API Documentation Template',
                'description': 'Create comprehensive API documentation with endpoints, parameters, examples, and response formats.',
                'category': 'technical',
                'template_content': '''# {{api_name}} API Documentation

## Overview
{{api_description}}

**Base URL:** `{{base_url}}`
**Version:** {{version}}
**Authentication:** {{auth_method}}

## Endpoints

### {{endpoint_name}}
**Method:** `{{http_method}}`
**Endpoint:** `{{endpoint_path}}`

**Description:** {{endpoint_description}}

#### Parameters
{{#parameters}}
- `{{param_name}}` ({{param_type}}) - {{param_description}} {{#required}}**Required**{{/required}}
{{/parameters}}

#### Request Example
```{{request_format}}
{{request_example}}
```

#### Response Example
```{{response_format}}
{{response_example}}
```

#### Error Codes
{{#error_codes}}
- `{{code}}` - {{description}}
{{/error_codes}}

## Rate Limiting
{{rate_limiting}}

## SDK Examples
{{sdk_examples}}''',
                'tags': ['api', 'documentation', 'technical'],
                'fields': [
                    {'label': 'API Name', 'type': 'text', 'placeholder': 'Name of your API', 'required': True},
                    {'label': 'API Description', 'type': 'textarea', 'placeholder': 'What does this API do?', 'required': True},
                    {'label': 'Base URL', 'type': 'text', 'placeholder': 'https://api.example.com'},
                    {'label': 'Version', 'type': 'text', 'placeholder': 'v1.0'},
                    {'label': 'Authentication Method', 'type': 'dropdown', 'options': ['API Key', 'Bearer Token', 'OAuth 2.0', 'Basic Auth', 'None']},
                    {'label': 'Endpoint Name', 'type': 'text', 'placeholder': 'Name of the main endpoint'},
                    {'label': 'HTTP Method', 'type': 'dropdown', 'options': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']},
                    {'label': 'Endpoint Path', 'type': 'text', 'placeholder': '/api/v1/resource'},
                    {'label': 'Request Example', 'type': 'textarea', 'placeholder': 'Show an example request...'},
                    {'label': 'Response Example', 'type': 'textarea', 'placeholder': 'Show an example response...'}
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
                template_content=template_data['template_content'],
                author=admin_user,
                tags=template_data['tags'],
                is_featured=template_data.get('is_featured', False),
                is_public=True,
                # Add some realistic metrics
                usage_count=self.random_usage_count(),
                average_rating=self.random_rating(),
                completion_rate=self.random_completion_rate()
            )
            
            # Create and add fields
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
            
            # Update popularity score
            template.update_popularity_score()
            
            created_count += 1
            self.stdout.write(f'  Created template: {template.title}')
        
        self.stdout.write(f'Created {created_count} templates')

    def random_usage_count(self):
        """Generate random but realistic usage count"""
        import random
        return random.randint(5, 500)

    def random_rating(self):
        """Generate random but realistic rating"""
        import random
        return round(random.uniform(3.5, 5.0), 1)

    def random_completion_rate(self):
        """Generate random but realistic completion rate"""
        import random
        return round(random.uniform(0.6, 0.95), 2)