"""
Serializers for AI Services and Ask-Me system
"""

from rest_framework import serializers
from .models import (
    AIProvider, AIModel, AIInteraction, AskMeSession, AskMeQuestion
)

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = '__all__'

class AIModelSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = AIModel
        fields = '__all__'

class AIInteractionSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='ai_model.name', read_only=True)

    class Meta:
        model = AIInteraction
        fields = '__all__'

class AskMeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AskMeQuestion
        fields = [
            'id', 'qid', 'title', 'help_text', 'variable', 'kind',
            'options', 'is_required', 'suggested_answer', 'answer',
            'is_answered', 'answered_at', 'order', 'created_at'
        ]

class AskMeSessionSerializer(serializers.ModelSerializer):
    questions = AskMeQuestionSerializer(many=True, read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    answered_questions_count = serializers.SerializerMethodField()

    class Meta:
        model = AskMeSession
        fields = [
            'id', 'intent', 'spec', 'answered_vars', 'current_questions',
            'preview_prompt', 'final_prompt', 'is_complete', 'good_enough_to_run',
            'metadata', 'created_at', 'updated_at', 'completed_at',
            'questions', 'completion_percentage', 'questions_count',
            'answered_questions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_answered_questions_count(self, obj):
        return obj.questions.filter(is_answered=True).count()

# Request/Response serializers for API
class AskMeStartRequestSerializer(serializers.Serializer):
    intent = serializers.CharField(max_length=1000, help_text="User's goal or intent")

class AskMeStartResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    questions = serializers.ListField()
    good_enough_to_run = serializers.BooleanField()

class AskMeAnswerRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    qid = serializers.CharField(max_length=50)
    value = serializers.CharField()

class AskMeAnswerResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    questions = serializers.ListField()
    good_enough_to_run = serializers.BooleanField()
    preview_prompt = serializers.CharField(allow_null=True)

class AskMeFinalizeRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()

class AskMeFinalizeResponseSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    metadata = serializers.DictField()