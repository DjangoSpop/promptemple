"""
Enhanced Django Admin for Templates with Markdown Support
Provides rich admin interface for managing templates, bulk operations, and markdown ingestion
"""

from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms import ModelForm, Textarea, TextInput
from django import forms
import json

from .models import (
    Template, TemplateCategory, PromptField, TemplateField, 
    TemplateUsage, TemplateRating, TemplateBookmark
)
from .services.md_ingestion_service import MarkdownIngestionManager


class MarkdownBulkUploadForm(forms.Form):
    """Form for bulk uploading templates via markdown"""
    
    markdown_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 20,
            'cols': 80,
            'placeholder': 'Paste your markdown content here...\n\nSupported formats:\n- Code blocks with template content\n- {{variable}} placeholders\n- **Category**: Category Name\n- **Target Audience**: Description'
        }),
        label='Markdown Content',
        help_text='Paste markdown content containing templates with {{variable}} placeholders'
    )
    
    default_category = forms.ModelChoiceField(
        queryset=TemplateCategory.objects.filter(is_active=True),
        required=False,
        help_text='Default category if not specified in markdown'
    )
    
    author_username = forms.CharField(
        initial='admin',
        help_text='Username for template author'
    )
    
    make_public = forms.BooleanField(
        initial=True,
        required=False,
        help_text='Make templates publicly visible'
    )
    
    make_featured = forms.BooleanField(
        initial=False,
        required=False,
        help_text='Mark templates as featured'
    )


class TemplateCategoryAdmin(admin.ModelAdmin):
    """Enhanced admin for template categories"""
    
    list_display = ['name', 'template_count', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def template_count(self, obj):
        """Display template count for category"""
        count = obj.templates.filter(is_active=True).count()
        url = reverse('admin:templates_template_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} templates</a>', url, count)
    template_count.short_description = 'Templates'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            template_count=Count('templates', filter=Q(templates__is_active=True))
        )


class PromptFieldInline(admin.TabularInline):
    """Inline admin for prompt fields"""
    
    model = TemplateField
    extra = 1
    fields = ['field', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('field')


class TemplateForm(ModelForm):
    """Custom form for template with enhanced features"""
    
    class Meta:
        model = Template
        fields = '__all__'
        widgets = {
            'template_content': Textarea(attrs={
                'rows': 15,
                'cols': 80,
                'placeholder': 'Enter your template content with {{variable}} placeholders...'
            }),
            'description': Textarea(attrs={'rows': 4}),
            'tags': TextInput(attrs={
                'placeholder': 'Enter tags separated by commas'
            }),
        }
    
    markdown_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 80,
            'placeholder': 'Alternatively, paste markdown content here to auto-generate template and fields...'
        }),
        required=False,
        help_text='Paste markdown content to automatically extract template content and generate fields'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Show current fields count
            field_count = self.instance.field_count
            self.fields['title'].help_text = f'Current template has {field_count} fields'


class TemplateAdmin(admin.ModelAdmin):
    """Enhanced admin for templates"""
    
    form = TemplateForm
    inlines = [PromptFieldInline]
    
    list_display = [
        'title', 'category', 'author', 'field_count', 'usage_count', 
        'average_rating', 'popularity_score', 'is_public', 'is_featured', 'created_at'
    ]
    
    list_filter = [
        'category', 'is_public', 'is_featured', 'is_active', 'is_ai_generated',
        'created_at', 'author'
    ]
    
    search_fields = ['title', 'description', 'tags']
    
    list_editable = ['is_public', 'is_featured']
    
    readonly_fields = [
        'id', 'usage_count', 'completion_rate', 'average_rating', 
        'popularity_score', 'created_at', 'updated_at'
    ]
    
    filter_horizontal = ['collaborators', 'related_templates']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'author')
        }),
        ('Template Content', {
            'fields': ('template_content', 'markdown_input'),
            'description': 'Use either template_content or markdown_input to define your template'
        }),
        ('Metadata', {
            'fields': ('version', 'tags'),
            'classes': ('collapse',)
        }),
        ('AI & Analytics', {
            'fields': (
                'is_ai_generated', 'ai_confidence', 'extracted_keywords',
                'usage_count', 'completion_rate', 'average_rating', 'popularity_score'
            ),
            'classes': ('collapse',)
        }),
        ('Collaboration', {
            'fields': ('collaborators', 'related_templates'),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('is_public', 'is_featured', 'is_active')
        }),
        ('Advanced', {
            'fields': ('smart_suggestions', 'localizations'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'make_public', 'make_private', 'feature_templates', 
        'unfeature_templates', 'bulk_update_popularity'
    ]
    
    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view),
                 name='templates_template_bulk_upload'),
            path('analytics/', self.admin_site.admin_view(self.analytics_view),
                 name='templates_template_analytics'),
            path('inflate-pro-prompts/', self.admin_site.admin_view(self.inflate_pro_prompts_view),
                 name='templates_template_inflate_pro'),
            path('import-md-file/', self.admin_site.admin_view(self.import_md_file_view),
                 name='templates_template_import_md'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """View for bulk uploading templates via markdown"""
        if request.method == 'POST':
            form = MarkdownBulkUploadForm(request.POST)
            if form.is_valid():
                return self._process_bulk_upload(request, form)
        else:
            form = MarkdownBulkUploadForm()
        
        context = {
            'form': form,
            'title': 'Bulk Upload Templates from Markdown',
            'opts': self.model._meta,
            'has_change_permission': True,
        }
        return render(request, 'admin/templates/bulk_upload.html', context)
    
    def _process_bulk_upload(self, request, form):
        """Process the bulk upload form"""
        try:
            # Create temporary markdown file content
            markdown_content = form.cleaned_data['markdown_content']
            
            # Initialize ingestion manager
            manager = MarkdownIngestionManager()
            
            # Extract prompts from markdown content
            prompts = manager.extractor._parse_markdown_content(
                markdown_content, 
                'admin_upload'
            )
            
            if not prompts:
                messages.error(request, 'No valid templates found in markdown content')
                return redirect('admin:templates_template_bulk_upload')
            
            # Apply form settings to prompts
            for prompt in prompts:
                if form.cleaned_data['default_category'] and not prompt.get('category'):
                    prompt['category'] = form.cleaned_data['default_category'].name
                
                # Override with form settings
                prompt['is_public'] = form.cleaned_data['make_public']
                prompt['is_featured'] = form.cleaned_data['make_featured']
            
            # Set custom author
            manager.ingestion_service.default_author = self._get_author(
                form.cleaned_data['author_username']
            )
            
            # Perform ingestion
            result = manager.ingestion_service.bulk_ingest_prompts(prompts)
            
            # Show results
            if result['successfully_created'] > 0:
                messages.success(
                    request, 
                    f'Successfully created {result["successfully_created"]} templates!'
                )
            
            if result['skipped_duplicates'] > 0:
                messages.warning(
                    request,
                    f'Skipped {result["skipped_duplicates"]} duplicate templates'
                )
            
            if result['errors'] > 0:
                messages.error(
                    request,
                    f'Failed to create {result["errors"]} templates'
                )
            
            return redirect('admin:templates_template_changelist')
            
        except Exception as e:
            messages.error(request, f'Error processing upload: {str(e)}')
            return redirect('admin:templates_template_bulk_upload')
    
    def _get_author(self, username):
        """Get or create author user"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            # Create user if doesn't exist
            user = User.objects.create_user(
                username=username,
                email=f'{username}@admin.local',
                first_name='Admin',
                last_name='User'
            )
            return user
    
    def analytics_view(self, request):
        """View for template analytics"""
        # Get analytics data
        total_templates = Template.objects.filter(is_active=True).count()
        public_templates = Template.objects.filter(is_active=True, is_public=True).count()
        featured_templates = Template.objects.filter(is_featured=True).count()
        
        # Category statistics
        category_stats = TemplateCategory.objects.annotate(
            template_count=Count('templates', filter=Q(templates__is_active=True)),
            avg_rating=Avg('templates__average_rating')
        ).order_by('-template_count')
        
        # Usage statistics
        usage_stats = Template.objects.filter(is_active=True).aggregate(
            total_usage=Count('usage_logs'),
            avg_usage=Avg('usage_count'),
            avg_rating=Avg('average_rating'),
            avg_popularity=Avg('popularity_score')
        )
        
        # Top templates
        top_templates = Template.objects.filter(
            is_active=True, is_public=True
        ).order_by('-popularity_score')[:10]
        
        context = {
            'title': 'Template Analytics Dashboard',
            'opts': self.model._meta,
            'total_templates': total_templates,
            'public_templates': public_templates,
            'featured_templates': featured_templates,
            'category_stats': category_stats,
            'usage_stats': usage_stats,
            'top_templates': top_templates,
        }
        
        return render(request, 'admin/templates/analytics.html', context)
    
    def save_model(self, request, obj, form, change):
        """Custom save with markdown processing"""
        # Process markdown input if provided
        markdown_input = form.cleaned_data.get('markdown_input', '').strip()
        
        if markdown_input and not change:  # Only for new templates
            manager = MarkdownIngestionManager()
            prompts = manager.extractor._parse_markdown_content(
                markdown_input, 'admin_form'
            )
            
            if prompts:
                # Use first extracted prompt to populate fields
                prompt_data = prompts[0]
                
                if not obj.template_content:
                    obj.template_content = prompt_data.get('template_content', '')
                
                if not obj.description:
                    obj.description = prompt_data.get('description', '')
                
                if not obj.tags and prompt_data.get('tags'):
                    obj.tags = prompt_data['tags']
        
        super().save_model(request, obj, form, change)
        
        # Auto-create fields from template content if it's a new template
        if not change and obj.template_content:
            self._auto_create_fields(obj, markdown_input)
    
    def _auto_create_fields(self, template, markdown_input):
        """Auto-create prompt fields from template content"""
        if markdown_input:
            # Use markdown processor to extract variables
            manager = MarkdownIngestionManager()
            variables = manager.extractor._extract_variables(template.template_content)
            
            for i, var_data in enumerate(variables):
                field = PromptField.objects.create(
                    label=var_data['label'],
                    placeholder=var_data.get('placeholder', ''),
                    field_type=var_data.get('type', 'text'),
                    is_required=var_data.get('required', True),
                    help_text=f"Variable: {var_data['name']}",
                    order=i,
                )
                
                TemplateField.objects.create(
                    template=template,
                    field=field,
                    order=i,
                )
    
    # Admin actions
    def make_public(self, request, queryset):
        """Make selected templates public"""
        count = queryset.update(is_public=True)
        messages.success(request, f'{count} templates made public')
    make_public.short_description = 'Make selected templates public'
    
    def make_private(self, request, queryset):
        """Make selected templates private"""
        count = queryset.update(is_public=False)
        messages.success(request, f'{count} templates made private')
    make_private.short_description = 'Make selected templates private'
    
    def feature_templates(self, request, queryset):
        """Feature selected templates"""
        count = queryset.update(is_featured=True)
        messages.success(request, f'{count} templates featured')
    feature_templates.short_description = 'Feature selected templates'
    
    def unfeature_templates(self, request, queryset):
        """Unfeature selected templates"""
        count = queryset.update(is_featured=False)
        messages.success(request, f'{count} templates unfeatured')
    unfeature_templates.short_description = 'Unfeature selected templates'
    
    def bulk_update_popularity(self, request, queryset):
        """Bulk update popularity scores"""
        count = 0
        for template in queryset:
            template.update_popularity_score()
            count += 1
        messages.success(request, f'Updated popularity scores for {count} templates')
    bulk_update_popularity.short_description = 'Update popularity scores'
    
    # ------------------------------------------------------------------
    # Inflate Pro Prompts admin view
    # ------------------------------------------------------------------

    def inflate_pro_prompts_view(self, request):
        """Admin one-click inflate: seeds 60 pro prompts from inflate_pro_prompts command."""
        from django.core.management import call_command
        from io import StringIO
        import traceback

        result = None
        error = None

        if request.method == 'POST':
            action = request.POST.get('action', 'seed')
            dry_run = (action == 'dry_run')
            clear = (action == 'clear')
            category_filter = request.POST.get('category', '').strip() or None

            out = StringIO()
            try:
                kwargs = {'stdout': out, 'stderr': out, 'dry_run': dry_run, 'clear': clear}
                if category_filter:
                    kwargs['category'] = category_filter
                call_command('inflate_pro_prompts', **kwargs)
                result = out.getvalue()
                if not dry_run:
                    if clear:
                        messages.success(request, 'Pro prompt library cleared and re-seeded successfully.')
                    else:
                        messages.success(request, 'Pro prompt library inflated successfully.')
            except Exception as exc:
                error = traceback.format_exc()
                messages.error(request, f'Error running inflate_pro_prompts: {exc}')

        # Import here to avoid circular at module load
        from apps.templates.management.commands.inflate_pro_prompts import CATEGORIES
        category_names = list(CATEGORIES.keys())
        total_count = Template.objects.filter(
            performance_metrics__source='inflate_pro_prompts'
        ).count()

        context = {
            'title': 'Inflate Pro Prompt Library',
            'opts': self.model._meta,
            'has_change_permission': True,
            'result': result,
            'error': error,
            'category_names': category_names,
            'already_seeded': total_count,
        }
        return render(request, 'admin/templates/inflate_pro_prompts.html', context)

    # ------------------------------------------------------------------
    # Import MD File admin view
    # ------------------------------------------------------------------

    def import_md_file_view(self, request):
        """Admin view to upload a .md file and ingest its prompts."""
        import tempfile
        import os
        import traceback

        result = None
        error = None
        stats = None

        if request.method == 'POST' and request.FILES.get('md_file'):
            uploaded = request.FILES['md_file']
            dry_run = request.POST.get('dry_run') == '1'
            make_public = request.POST.get('make_public', '1') == '1'
            make_featured = request.POST.get('make_featured') == '1'
            author_username = request.POST.get('author_username', 'admin').strip() or 'admin'

            # Write upload to a named temp file so ingestion service can open it
            suffix = os.path.splitext(uploaded.name)[1] or '.md'
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as tmp:
                    for chunk in uploaded.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                manager = MarkdownIngestionManager()
                prompts = manager.extractor.extract_prompts_from_md(tmp_path)

                lines = [f'Found {len(prompts)} prompt(s) in "{uploaded.name}".']

                if dry_run:
                    for i, p in enumerate(prompts[:20], 1):
                        lines.append(f'  [{i}] {p.get("title", "(no title)")} — category: {p.get("category", "-")}')
                    if len(prompts) > 20:
                        lines.append(f'  … and {len(prompts) - 20} more (truncated)')
                    result = '\n'.join(lines)
                    stats = {'found': len(prompts), 'created': 0, 'skipped': 0, 'errors': 0, 'dry_run': True}
                else:
                    # Apply visibility overrides
                    for p in prompts:
                        p['is_public'] = make_public
                        p['is_featured'] = make_featured

                    author = self._get_author(author_username)
                    manager.ingestion_service.default_author = author

                    res = manager.ingestion_service.bulk_ingest_prompts(prompts)
                    created = res.get('successfully_created', 0)
                    skipped = res.get('skipped_duplicates', 0)
                    errors = res.get('errors', 0)

                    lines.append(f'Created: {created}  |  Skipped (duplicates): {skipped}  |  Errors: {errors}')
                    result = '\n'.join(lines)
                    stats = {'found': len(prompts), 'created': created, 'skipped': skipped, 'errors': errors, 'dry_run': False}

                    if created:
                        messages.success(request, f'Imported {created} prompt(s) from "{uploaded.name}".')
                    if errors:
                        messages.warning(request, f'{errors} prompt(s) failed to import.')

            except Exception as exc:
                error = traceback.format_exc()
                messages.error(request, f'Error processing file: {exc}')
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        elif request.method == 'POST':
            messages.error(request, 'No file uploaded. Please select a .md file.')

        context = {
            'title': 'Import Prompts from Markdown File',
            'opts': self.model._meta,
            'has_change_permission': True,
            'result': result,
            'error': error,
            'stats': stats,
        }
        return render(request, 'admin/templates/import_md_file.html', context)

    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist"""
        extra_context = extra_context or {}
        extra_context['bulk_upload_url'] = reverse('admin:templates_template_bulk_upload')
        extra_context['analytics_url'] = reverse('admin:templates_template_analytics')
        extra_context['inflate_pro_url'] = reverse('admin:templates_template_inflate_pro')
        extra_context['import_md_url'] = reverse('admin:templates_template_import_md')
        return super().changelist_view(request, extra_context=extra_context)


class PromptFieldAdmin(admin.ModelAdmin):
    """Admin for prompt fields"""
    
    list_display = ['label', 'field_type', 'is_required', 'template_count', 'order']
    list_filter = ['field_type', 'is_required']
    search_fields = ['label', 'help_text']
    
    def template_count(self, obj):
        """Show number of templates using this field"""
        return obj.templates.count()
    template_count.short_description = 'Used in templates'


class TemplateUsageAdmin(admin.ModelAdmin):
    """Admin for template usage tracking"""
    
    list_display = [
        'user', 'template', 'started_at', 'was_completed', 
        'duration_minutes', 'user_satisfaction'
    ]
    list_filter = [
        'was_completed', 'started_at', 'template__category',
        'user_satisfaction', 'device_type'
    ]
    search_fields = ['user__username', 'template__title']
    readonly_fields = ['started_at', 'completed_at', 'created_at', 'updated_at']
    
    def duration_minutes(self, obj):
        """Show duration in readable format"""
        if obj.time_spent_seconds:
            minutes = obj.time_spent_seconds // 60
            seconds = obj.time_spent_seconds % 60
            return f'{minutes}m {seconds}s'
        return 'N/A'
    duration_minutes.short_description = 'Duration'


class TemplateRatingAdmin(admin.ModelAdmin):
    """Admin for template ratings"""
    
    list_display = [
        'template', 'user', 'rating', 'ease_of_use', 'quality_of_output',
        'would_recommend', 'is_verified', 'created_at'
    ]
    list_filter = [
        'rating', 'would_recommend', 'is_verified', 'is_flagged',
        'template__category', 'created_at'
    ]
    search_fields = ['template__title', 'user__username', 'review']
    readonly_fields = ['created_at', 'updated_at', 'helpful_votes', 'total_votes']


# Register admin classes
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(PromptField, PromptFieldAdmin)
admin.site.register(TemplateUsage, TemplateUsageAdmin)
admin.site.register(TemplateRating, TemplateRatingAdmin)

# Customize admin site
admin.site.site_header = 'PromptCraft Admin'
admin.site.site_title = 'PromptCraft Admin'
admin.site.index_title = 'Template Management System'
