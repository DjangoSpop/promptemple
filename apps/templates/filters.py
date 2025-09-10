import django_filters
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from .models import Template, TemplateCategory

class TemplateFilter(django_filters.FilterSet):
    """
    Advanced filtering for templates
    """
    
    # Text search across multiple fields
    search = django_filters.CharFilter(method='filter_search')
    
    # Category filtering
    category = django_filters.ModelChoiceFilter(
        queryset=TemplateCategory.objects.filter(is_active=True)
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact'
    )
    
    # Tag filtering
    tags = django_filters.CharFilter(method='filter_tags')
    
    # Rating filtering
    min_rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte'
    )
    
    # Usage filtering
    min_usage = django_filters.NumberFilter(
        field_name='usage_count',
        lookup_expr='gte'
    )
    
    # Author filtering
    author_username = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='iexact'
    )
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_ai_generated = django_filters.BooleanFilter()
    
    class Meta:
        model = Template
        fields = [
            'search', 'category', 'category_slug', 'tags',
            'min_rating', 'min_usage', 'author_username',
            'created_after', 'created_before', 'is_featured',
            'is_ai_generated'
        ]
    
    def filter_search(self, queryset, name, value):
        """
        Full-text search across title, description, and tags
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__icontains=value) |
            Q(template_content__icontains=value)
        ).distinct()
    
    def filter_tags(self, queryset, name, value):
        """
        Filter by tags (comma-separated)
        """
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',')]
        query = Q()
        
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query).distinct()
    
    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr):
        """
        Override to handle JSONField filtering
        """
        from django.contrib.postgres.fields import JSONField
        
        if isinstance(field, JSONField):
            return django_filters.CharFilter(
                field_name=field_name,
                lookup_expr='icontains',
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
        
        return super().filter_for_field(field, field_name, lookup_expr)