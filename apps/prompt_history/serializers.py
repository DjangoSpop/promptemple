from rest_framework import serializers
from .models import PromptHistory


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
