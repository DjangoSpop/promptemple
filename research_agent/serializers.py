"""
DRF Serializers for research agent API endpoints.
"""
from rest_framework import serializers
from .models import ResearchJob, SourceDoc, Chunk, ResearchAnswer


class CreateJobSerializer(serializers.Serializer):
    """Serializer for creating new research jobs."""
    query = serializers.CharField(
        max_length=1000,
        help_text="Research query to investigate"
    )
    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        default=6,
        help_text="Number of search results to process"
    )


class ResearchJobSerializer(serializers.ModelSerializer):
    """Serializer for research job details."""

    class Meta:
        model = ResearchJob
        fields = [
            'id',
            'query',
            'top_k',
            'status',
            'error',
            'created_at',
            'finished_at'
        ]
        read_only_fields = ['id', 'status', 'error', 'created_at', 'finished_at']


class SourceDocSerializer(serializers.ModelSerializer):
    """Serializer for source documents."""

    class Meta:
        model = SourceDoc
        fields = [
            'id',
            'url',
            'title',
            'text',
            'status_code',
            'fetched_ms',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        """Customize representation to limit text length in lists."""
        data = super().to_representation(instance)

        # Truncate text for list views
        request = self.context.get('request')
        if request and request.resolver_match.url_name != 'sourcedoc-detail':
            text = data.get('text', '')
            if len(text) > 200:
                data['text'] = text[:200] + "..."
                data['text_truncated'] = True

        return data


class ChunkSerializer(serializers.ModelSerializer):
    """Serializer for text chunks."""
    score = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Chunk
        fields = [
            'id',
            'text',
            'tokens',
            'url',
            'title',
            'score',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'score']

    def to_representation(self, instance):
        """Customize representation for different contexts."""
        data = super().to_representation(instance)

        # Add score if available (for search results)
        if hasattr(instance, 'score'):
            data['score'] = getattr(instance, 'score', 0)

        return data


class CitationSerializer(serializers.Serializer):
    """Serializer for answer citations."""
    n = serializers.IntegerField(help_text="Citation number")
    url = serializers.URLField(help_text="Source URL")
    title = serializers.CharField(help_text="Source title")
    score = serializers.FloatField(required=False, help_text="Relevance score")


class ResearchAnswerSerializer(serializers.ModelSerializer):
    """Serializer for research answers."""
    citations = CitationSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchAnswer
        fields = [
            'answer_md',
            'citations',
            'created_at'
        ]
        read_only_fields = ['created_at']


class JobWithAnswerSerializer(ResearchJobSerializer):
    """Extended job serializer that includes the answer when available."""
    answer = ResearchAnswerSerializer(read_only=True, required=False)
    docs_count = serializers.IntegerField(read_only=True)
    chunks_count = serializers.IntegerField(read_only=True)

    class Meta(ResearchJobSerializer.Meta):
        fields = ResearchJobSerializer.Meta.fields + [
            'answer',
            'docs_count',
            'chunks_count'
        ]

    def to_representation(self, instance):
        """Add computed fields."""
        data = super().to_representation(instance)

        # Add counts
        data['docs_count'] = instance.docs.count()

        # Count chunks through docs
        chunk_count = 0
        for doc in instance.docs.all():
            chunk_count += doc.chunks.count()
        data['chunks_count'] = chunk_count

        return data


class JobProgressSerializer(serializers.Serializer):
    """Serializer for job progress information."""
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    query = serializers.CharField()
    created_at = serializers.DateTimeField()
    finished_at = serializers.DateTimeField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_blank=True)
    docs_processed = serializers.IntegerField(required=False)
    chunks_created = serializers.IntegerField(required=False)
    answer_ready = serializers.BooleanField(required=False)
    answer_length = serializers.IntegerField(required=False)
    citations_count = serializers.IntegerField(required=False)
    summary = serializers.CharField(required=False)


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results."""
    url = serializers.URLField()
    title = serializers.CharField()
    score = serializers.FloatField(required=False)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check results."""
    timestamp = serializers.DateTimeField()
    database = serializers.BooleanField()
    embeddings = serializers.BooleanField()
    search = serializers.BooleanField()
    synthesis = serializers.BooleanField()
    overall = serializers.BooleanField()
    error = serializers.CharField(required=False)


class SystemStatsSerializer(serializers.Serializer):
    """Serializer for system statistics."""
    total_jobs = serializers.IntegerField()
    jobs_last_24h = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    avg_processing_time_seconds = serializers.FloatField(required=False)
    database_engine = serializers.CharField(required=False)
    supports_vector_search = serializers.BooleanField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Standardized error response serializer."""
    error = serializers.CharField()
    detail = serializers.CharField(required=False)
    code = serializers.CharField(required=False)


class SSEEventSerializer(serializers.Serializer):
    """Serializer for Server-Sent Events."""
    event = serializers.CharField(help_text="Event type")
    data = serializers.JSONField(help_text="Event data")

    def to_sse_format(self) -> str:
        """Convert to SSE format string."""
        event = self.validated_data['event']
        data = self.validated_data['data']

        import json
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# Rate limiting serializers
class RateLimitSerializer(serializers.Serializer):
    """Serializer for rate limiting information."""
    requests_remaining = serializers.IntegerField()
    requests_limit = serializers.IntegerField()
    reset_time = serializers.DateTimeField()
    retry_after = serializers.IntegerField(required=False)


# Batch operation serializers
class BatchJobSerializer(serializers.Serializer):
    """Serializer for batch job creation."""
    queries = serializers.ListField(
        child=serializers.CharField(max_length=1000),
        min_length=1,
        max_length=10,
        help_text="List of research queries to process"
    )
    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        default=6
    )


class JobSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for job lists."""

    class Meta:
        model = ResearchJob
        fields = [
            'id',
            'query',
            'status',
            'created_at',
            'finished_at'
        ]

    def to_representation(self, instance):
        """Add summary information."""
        data = super().to_representation(instance)

        # Truncate query for list view
        query = data.get('query', '')
        if len(query) > 100:
            data['query'] = query[:100] + "..."
            data['query_truncated'] = True

        # Add answer availability
        data['has_answer'] = hasattr(instance, 'answer')

        return data