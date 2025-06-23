from rest_framework import serializers
from django.db import transaction
from .models import Template, PromptField, TemplateCategory, TemplateUsage, TemplateRating, TemplateBookmark
from apps.users.serializers import UserMinimalSerializer

class PromptFieldSerializer(serializers.ModelSerializer):
    """
    Serializer for individual prompt fields
    
    Handles validation of field configuration
    """
    
    class Meta:
        model = PromptField
        fields = [
            'id', 'label', 'placeholder', 'field_type', 'is_required', 
            'default_value', 'validation_pattern', 'help_text', 
            'options', 'order'
        ]

    def validate_options(self, value):
        """Validate options for choice fields"""
        field_type = self.initial_data.get('field_type')
        choice_types = ['dropdown', 'radio', 'checkbox']
        
        if field_type in choice_types:
            if not value or len(value) == 0:
                raise serializers.ValidationError(
                    f"{field_type} fields must have at least one option"
                )
            
            # Ensure all options are strings
            if not all(isinstance(option, str) for option in value):
                raise serializers.ValidationError(
                    "All options must be strings"
                )
        
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        field_type = attrs.get('field_type')
        options = attrs.get('options', [])
        default_value = attrs.get('default_value', '')
        
        # For choice fields, validate default value is in options
        if field_type in ['dropdown', 'radio'] and default_value:
            if default_value not in options:
                raise serializers.ValidationError(
                    "Default value must be one of the provided options"
                )
        
        return attrs


class TemplateCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for template categories
    """
    
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 
            'color', 'is_active', 'order', 'template_count'
        ]
    
    def get_template_count(self, obj):
        """Get count of public, active templates in this category"""
        return obj.templates.filter(is_active=True, is_public=True).count()


class TemplateListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for template lists
    
    Optimized for performance with minimal data
    """
    
    author = serializers.StringRelatedField()
    category = TemplateCategorySerializer(read_only=True)
    field_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'title', 'description', 'category', 'author', 
            'version', 'tags', 'usage_count', 'completion_rate', 
            'average_rating', 'popularity_score', 'is_featured',
            'field_count', 'created_at', 'updated_at'
        ]


class TemplateDetailSerializer(serializers.ModelSerializer):
    """
    Complete template serializer with all details
    
    Includes:
    - All template data
    - Associated fields
    - Author information
    - Category details
    """
    
    author = UserMinimalSerializer(read_only=True)
    category = TemplateCategorySerializer(read_only=True)
    fields = PromptFieldSerializer(many=True, read_only=True)
    field_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'title', 'description', 'category', 'template_content',
            'author', 'fields', 'version', 'tags', 'is_ai_generated',
            'ai_confidence', 'extracted_keywords', 'smart_suggestions',
            'usage_count', 'completion_rate', 'average_rating', 
            'popularity_score', 'is_public', 'is_featured', 'field_count',
            'localizations', 'created_at', 'updated_at'
        ]


class TemplateCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating templates
    
    Handles:
    - Template creation with fields
    - Field validation
    - Author assignment
    - Transaction safety
    """
    
    fields_data = PromptFieldSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Template
        fields = [
            'title', 'description', 'category', 'template_content',
            'version', 'tags', 'is_public', 'fields_data'
        ]

    def validate_template_content(self, value):
        """Validate template content has proper placeholder format"""
        import re
        
        # Check for valid placeholder format {{variable_name}}
        placeholder_pattern = r'\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}'
        placeholders = re.findall(placeholder_pattern, value)
        
        # Check for invalid placeholder formats
        invalid_pattern = r'\{[^{].*?[^}]\}'
        invalid_placeholders = re.findall(invalid_pattern, value)
        
        if invalid_placeholders:
            raise serializers.ValidationError(
                f"Invalid placeholder format. Use {{variable_name}} format. "
                f"Found: {invalid_placeholders}"
            )
        
        return value

    def validate_fields_data(self, value):
        """Validate fields data array"""
        if not value:
            return value
        
        # Check for duplicate field labels
        labels = [field['label'] for field in value]
        if len(labels) != len(set(labels)):
            raise serializers.ValidationError(
                "Field labels must be unique within a template"
            )
        
        # Validate each field
        for i, field_data in enumerate(value):
            field_serializer = PromptFieldSerializer(data=field_data)
            if not field_serializer.is_valid():
                raise serializers.ValidationError(
                    f"Field {i + 1} validation error: {field_serializer.errors}"
                )
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create template with associated fields"""
        fields_data = validated_data.pop('fields_data', [])
        validated_data['author'] = self.context['request'].user
        
        # Create template
        template = Template.objects.create(**validated_data)
        
        # Create and associate fields
        for order, field_data in enumerate(fields_data):
            field_data['order'] = order
            field = PromptField.objects.create(**field_data)
            template.fields.add(field)
        
        # Update user stats
        user = template.author
        user.templates_created += 1
        user.save(update_fields=['templates_created'])
        
        return template

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update template and fields"""
        fields_data = validated_data.pop('fields_data', None)
        
        # Update template fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update fields if provided
        if fields_data is not None:
            # Remove existing fields (cascade delete)
            instance.fields.clear()
            
            # Add new fields
            for order, field_data in enumerate(fields_data):
                field_data['order'] = order
                field = PromptField.objects.create(**field_data)
                instance.fields.add(field)
        
        return instance


class TemplateUsageSerializer(serializers.ModelSerializer):
    """
    Serializer for template usage tracking
    
    Handles usage session data and metrics
    """
    
    template_title = serializers.CharField(source='template.title', read_only=True)
    template_id = serializers.UUIDField(source='template.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    completion_rate_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TemplateUsage
        fields = [
            'id', 'template', 'template_id', 'template_title', 
            'user', 'user_username', 'started_at', 'completed_at', 
            'was_completed', 'time_spent_seconds', 'duration_minutes',
            'generated_prompt_length', 'field_completion_data',
            'device_type', 'app_version', 'referrer_source',
            'user_satisfaction', 'completion_rate_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'started_at', 'created_at', 'updated_at',
            'template_id', 'template_title', 'user_username',
            'duration_minutes', 'completion_rate_percentage'
        ]

    def validate_user_satisfaction(self, value):
        """Validate satisfaction rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Satisfaction rating must be between 1 and 5"
            )
        return value

    def validate_field_completion_data(self, value):
        """Validate field completion data structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Field completion data must be a dictionary"
            )
        
        # Validate structure of each field entry
        for field_key, field_data in value.items():
            if not isinstance(field_data, dict):
                raise serializers.ValidationError(
                    f"Field data for '{field_key}' must be a dictionary"
                )
            
            required_keys = ['completed', 'value']
            if not all(key in field_data for key in required_keys):
                raise serializers.ValidationError(
                    f"Field data for '{field_key}' must contain 'completed' and 'value' keys"
                )
        
        return value


class TemplateUsageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating template usage sessions
    
    Used when starting a new template usage session
    """
    
    class Meta:
        model = TemplateUsage
        fields = [
            'template', 'device_type', 'app_version', 'referrer_source'
        ]

    def create(self, validated_data):
        """Create usage session with user from request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TemplateRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for template ratings and reviews
    
    Handles user feedback and rating data
    """
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_level = serializers.IntegerField(source='user.level', read_only=True)
    template_title = serializers.CharField(source='template.title', read_only=True)
    helpfulness_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TemplateRating
        fields = [
            'id', 'template', 'template_title', 'user', 'user_username', 
            'user_level', 'rating', 'review', 'ease_of_use', 
            'quality_of_output', 'design_rating', 'would_recommend',
            'helpful_votes', 'total_votes', 'helpfulness_percentage',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_username', 'user_level', 'template_title',
            'helpful_votes', 'total_votes', 'helpfulness_percentage',
            'is_verified', 'created_at', 'updated_at'
        ]

    def validate_rating(self, value):
        """Validate main rating"""
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5 stars"
            )
        return value

    def validate_ease_of_use(self, value):
        """Validate ease of use rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Ease of use rating must be between 1 and 5"
            )
        return value

    def validate_quality_of_output(self, value):
        """Validate quality rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Quality rating must be between 1 and 5"
            )
        return value

    def validate_design_rating(self, value):
        """Validate design rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Design rating must be between 1 and 5"
            )
        return value

    def validate_review(self, value):
        """Validate review content"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Review must be at least 10 characters long"
            )
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        template = attrs.get('template')
        user = self.context['request'].user
        
        # Check if user has completed this template
        has_completed = TemplateUsage.objects.filter(
            template=template,
            user=user,
            was_completed=True
        ).exists()
        
        if not has_completed:
            raise serializers.ValidationError(
                "You must complete this template before rating it"
            )
        
        return attrs

    def create(self, validated_data):
        """Create rating with user from request context"""
        validated_data['user'] = self.context['request'].user
        
        # Mark as verified if user completed the template
        validated_data['is_verified'] = True
        
        return super().create(validated_data)


class TemplateRatingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for rating lists
    
    Used in template detail views to show ratings
    """
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_level = serializers.IntegerField(source='user.level', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    helpfulness_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TemplateRating
        fields = [
            'id', 'user_username', 'user_level', 'user_avatar',
            'rating', 'review', 'ease_of_use', 'quality_of_output',
            'design_rating', 'would_recommend', 'helpful_votes',
            'total_votes', 'helpfulness_percentage', 'is_verified',
            'created_at'
        ]

    def get_user_avatar(self, obj):
        """Get user avatar URL"""
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
            return obj.user.avatar.url
        return None


class TemplateBookmarkSerializer(serializers.ModelSerializer):
    """
    Serializer for template bookmarks
    
    Handles user bookmark management
    """
    
    template_title = serializers.CharField(source='template.title', read_only=True)
    template_category = serializers.CharField(source='template.category.name', read_only=True)
    
    class Meta:
        model = TemplateBookmark
        fields = [
            'id', 'template', 'template_title', 'template_category',
            'folder_name', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'template_title', 'template_category', 'created_at']

    def create(self, validated_data):
        """Create bookmark with user from request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, attrs):
        """Prevent duplicate bookmarks"""
        template = attrs.get('template')
        user = self.context['request'].user
        
        if TemplateBookmark.objects.filter(template=template, user=user).exists():
            raise serializers.ValidationError(
                "You have already bookmarked this template"
            )
        
        return attrs


class TemplateStatsSerializer(serializers.Serializer):
    """
    Serializer for template statistics summary
    
    Provides aggregated data for dashboard views
    """
    
    total_templates = serializers.IntegerField()
    total_usages = serializers.IntegerField()
    completed_usages = serializers.IntegerField()
    average_completion_rate = serializers.FloatField()
    average_rating = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    popular_categories = serializers.ListField()
    trending_templates = serializers.ListField()
    recent_activity = serializers.ListField()
    
    class Meta:
        fields = [
            'total_templates', 'total_usages', 'completed_usages',
            'average_completion_rate', 'average_rating', 'total_ratings',
            'popular_categories', 'trending_templates', 'recent_activity'
        ]


class TemplateAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed template analytics
    
    Provides comprehensive analytics data for template owners
    """
    
    usage_stats = serializers.SerializerMethodField()
    completion_stats = serializers.SerializerMethodField()
    rating_stats = serializers.SerializerMethodField()
    time_series_data = serializers.SerializerMethodField()
    geographic_data = serializers.SerializerMethodField()
    device_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'title', 'created_at', 'usage_count', 'completion_rate',
            'average_rating', 'popularity_score', 'usage_stats', 
            'completion_stats', 'rating_stats', 'time_series_data',
            'geographic_data', 'device_breakdown'
        ]
    
    def get_usage_stats(self, instance):
        """Get comprehensive usage statistics"""
        return {
            'total_usage': instance.usage_count,
            'unique_users': instance.usage_logs.values('user').distinct().count(),
            'completion_rate': instance.completion_rate,
            'average_time_spent': self._calculate_average_time(instance),
            'total_sessions': instance.usage_logs.count(),
            'successful_completions': instance.usage_logs.filter(was_completed=True).count(),
        }
    
    def get_completion_stats(self, instance):
        """Get completion-related statistics"""
        total_sessions = instance.usage_logs.count()
        completed_sessions = instance.usage_logs.filter(was_completed=True).count()
        abandoned_sessions = total_sessions - completed_sessions
        
        return {
            'completed': completed_sessions,
            'abandoned': abandoned_sessions,
            'success_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'average_completion_time': self._calculate_average_time(instance),
        }
    
    def get_rating_stats(self, instance):
        """Get rating and review statistics"""
        ratings = instance.ratings.all()
        
        return {
            'average_rating': instance.average_rating,
            'total_ratings': ratings.count(),
            'rating_distribution': self._get_rating_distribution(instance),
            'review_count': ratings.filter(review__isnull=False).exclude(review='').count(),
            'verified_ratings': ratings.filter(is_verified=True).count(),
        }
    
    def get_time_series_data(self, instance):
        """Get usage over time (last 30 days)"""
        from django.utils import timezone
        from django.db.models import Count
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        daily_usage = instance.usage_logs.filter(
            started_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(started_at)'}
        ).values('day').annotate(
            usage_count=Count('id'),
            completion_count=Count('id', filter=Q(was_completed=True))
        ).order_by('day')
        
        return list(daily_usage)
    
    def get_geographic_data(self, instance):
        """Get geographic usage data (placeholder)"""
        # This would typically come from user location data or IP geolocation
        return {
            'top_countries': [
                {'country': 'United States', 'usage_count': 45},
                {'country': 'United Kingdom', 'usage_count': 23},
                {'country': 'Canada', 'usage_count': 18},
                {'country': 'Germany', 'usage_count': 12},
                {'country': 'Australia', 'usage_count': 8},
            ]
        }
    
    def get_device_breakdown(self, instance):
        """Get device type breakdown"""
        from django.db.models import Count
        
        device_stats = instance.usage_logs.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Fill in any missing data with defaults
        device_data = {item['device_type'] or 'unknown': item['count'] for item in device_stats}
        
        return {
            'desktop': device_data.get('desktop', 0),
            'mobile': device_data.get('mobile', 0),
            'tablet': device_data.get('tablet', 0),
            'unknown': device_data.get('unknown', 0),
        }
    
    def _calculate_average_time(self, template):
        """Calculate average completion time"""
        from django.db.models import Avg
        avg_time = template.usage_logs.filter(
            was_completed=True,
            time_spent_seconds__isnull=False
        ).aggregate(avg=Avg('time_spent_seconds'))['avg']
        
        return int(avg_time) if avg_time else 0
    
    def _get_rating_distribution(self, template):
        """Get rating distribution (1-5 stars)"""
        from django.db.models import Count
        distribution = template.ratings.values('rating').annotate(
            count=Count('rating')
        ).order_by('rating')
        
        # Create a complete distribution with 0 for missing ratings
        result = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            result[str(item['rating'])] = item['count']
        return result
        return result