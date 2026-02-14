from rest_framework import serializers
from .models import PromptHistory, SavedPrompt, PromptIteration, ConversationThread


class PromptHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptHistory
        fields = [
            'id', 'user', 'source', 'original_prompt', 'optimized_prompt', 'model_used',
            'tokens_input', 'tokens_output', 'credits_spent', 'intent_category', 'tags', 'meta',
            'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'credits_spent', 'tokens_input', 'tokens_output', 'created_at', 'updated_at']


class PromptHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptHistory
        fields = ['source', 'original_prompt', 'intent_category', 'tags', 'meta']

    def validate_original_prompt(self, value):
        if len(value) > 16000:
            raise serializers.ValidationError('Original prompt too long (max 16000 chars)')
        return value

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Tags must be a list')
        if len(value) > 20:
            raise serializers.ValidationError('Maximum 20 tags allowed')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        return PromptHistory.objects.create(user=user, **validated_data)


class PromptHistoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptHistory
        fields = ['optimized_prompt', 'model_used', 'tokens_input', 'tokens_output', 'credits_spent', 'tags', 'meta']

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Tags must be a list')
        if len(value) > 20:
            raise serializers.ValidationError('Maximum 20 tags allowed')
        return value


# ==================== SavedPrompt Serializers ====================

class SavedPromptSerializer(serializers.ModelSerializer):
    """Full serializer for SavedPrompt model"""
    class Meta:
        model = SavedPrompt
        fields = [
            'id', 'user', 'title', 'content', 'description',
            'category', 'tags', 'use_count', 'last_used_at',
            'is_favorite', 'is_public', 'metadata',
            'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'use_count', 'last_used_at', 'is_deleted', 'created_at', 'updated_at']


class SavedPromptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new SavedPrompt"""
    class Meta:
        model = SavedPrompt
        fields = ['title', 'content', 'description', 'category', 'tags', 'is_favorite', 'is_public', 'metadata']

    def validate_title(self, value):
        if len(value) > 200:
            raise serializers.ValidationError('Title too long (max 200 chars)')
        return value

    def validate_content(self, value):
        if len(value) > 50000:
            raise serializers.ValidationError('Content too long (max 50000 chars)')
        return value

    def validate_tags(self, value):
        if value and not isinstance(value, list):
            raise serializers.ValidationError('Tags must be a list')
        if value and len(value) > 20:
            raise serializers.ValidationError('Maximum 20 tags allowed')
        return value or []

    def create(self, validated_data):
        user = self.context['request'].user
        return SavedPrompt.objects.create(user=user, **validated_data)


class SavedPromptUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing SavedPrompt"""
    class Meta:
        model = SavedPrompt
        fields = ['title', 'content', 'description', 'category', 'tags', 'is_favorite', 'is_public', 'metadata']

    def validate_title(self, value):
        if value and len(value) > 200:
            raise serializers.ValidationError('Title too long (max 200 chars)')
        return value

    def validate_content(self, value):
        if value and len(value) > 50000:
            raise serializers.ValidationError('Content too long (max 50000 chars)')
        return value

    def validate_tags(self, value):
        if value and not isinstance(value, list):
            raise serializers.ValidationError('Tags must be a list')
        if value and len(value) > 20:
            raise serializers.ValidationError('Maximum 20 tags allowed')
        return value


class SavedPromptListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing SavedPrompts"""
    class Meta:
        model = SavedPrompt
        fields = [
            'id', 'title', 'content', 'description', 'category', 
            'tags', 'use_count', 'is_favorite', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'use_count', 'created_at', 'updated_at']


# ==================== PromptIteration Serializers ====================

class PromptIterationSerializer(serializers.ModelSerializer):
    """Full serializer for PromptIteration model"""
    iteration_chain_length = serializers.IntegerField(read_only=True)
    has_next_iteration = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PromptIteration
        fields = [
            'id', 'user', 'parent_prompt', 'previous_iteration',
            'iteration_number', 'version_tag', 'prompt_text', 'system_message',
            'ai_response', 'response_model', 'interaction_type',
            'tokens_input', 'tokens_output', 'response_time_ms', 'credits_spent',
            'user_rating', 'feedback_notes', 'changes_summary', 'diff_size',
            'parameters', 'tags', 'metadata', 'is_active', 'is_bookmarked',
            'is_deleted', 'created_at', 'updated_at',
            'iteration_chain_length', 'has_next_iteration'
        ]
        read_only_fields = [
            'id', 'user', 'iteration_number', 'diff_size', 
            'is_deleted', 'created_at', 'updated_at',
            'iteration_chain_length', 'has_next_iteration'
        ]


class PromptIterationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new PromptIteration"""
    class Meta:
        model = PromptIteration
        fields = [
            'parent_prompt', 'previous_iteration', 'prompt_text', 
            'system_message', 'ai_response', 'response_model', 'interaction_type',
            'tokens_input', 'tokens_output', 'response_time_ms', 'credits_spent',
            'user_rating', 'feedback_notes', 'changes_summary',
            'parameters', 'tags', 'metadata', 'version_tag'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        parent_prompt = validated_data.get('parent_prompt')
        
        # Calculate iteration number
        last_iteration = PromptIteration.objects.filter(
            parent_prompt=parent_prompt
        ).order_by('-iteration_number').first()
        
        iteration_number = (last_iteration.iteration_number + 1) if last_iteration else 1
        
        iteration = PromptIteration.objects.create(
            user=user,
            iteration_number=iteration_number,
            **validated_data
        )
        
        # Calculate diff size
        iteration.calculate_diff_size()
        iteration.save()
        
        return iteration


# ==================== ConversationThread Serializers ====================

class ConversationThreadSerializer(serializers.ModelSerializer):
    """Full serializer for ConversationThread model"""
    class Meta:
        model = ConversationThread
        fields = [
            'id', 'user', 'title', 'description', 'total_iterations',
            'total_tokens', 'total_credits', 'status', 'is_shared',
            'is_deleted', 'created_at', 'updated_at', 'last_activity_at'
        ]
        read_only_fields = [
            'id', 'user', 'total_iterations', 'total_tokens', 'total_credits',
            'is_deleted', 'created_at', 'updated_at', 'last_activity_at'
        ]


class ConversationThreadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new ConversationThread"""
    class Meta:
        model = ConversationThread
        fields = ['title', 'description', 'status']

    def create(self, validated_data):
        user = self.context['request'].user
        return ConversationThread.objects.create(user=user, **validated_data)
