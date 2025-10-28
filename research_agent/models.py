from django.db import models
import uuid

try:
    from pgvector.django import VectorField
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class ResearchJob(models.Model):
    STATUS = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("done", "Done"),
        ("error", "Error"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.TextField()
    top_k = models.IntegerField(default=6)
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=12, choices=STATUS, default="queued")
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Research Job: {self.query[:50]}..."


class SourceDoc(models.Model):
    job = models.ForeignKey(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name="docs"
    )
    url = models.URLField(max_length=1000)
    title = models.CharField(max_length=500, blank=True, default="")
    raw_html = models.TextField(blank=True, default="")
    text = models.TextField(blank=True, default="")
    status_code = models.IntegerField(null=True, blank=True)
    fetched_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Doc: {self.title or self.url}"


class Chunk(models.Model):
    doc = models.ForeignKey(
        SourceDoc,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    text = models.TextField()
    tokens = models.IntegerField()

    # Vector field - conditional on pgvector availability
    if HAS_PGVECTOR:
        embedding = VectorField(dimensions=384)  # sentence-transformers all-MiniLM-L6-v2
    else:
        # Fallback to JSONField for SQLite compatibility
        embedding = models.JSONField(default=list)

    # Helpful denormalization
    url = models.URLField(max_length=1000)
    title = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["url"]),
            models.Index(fields=["doc"]),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Chunk: {self.text[:50]}..."


class ResearchAnswer(models.Model):
    job = models.OneToOneField(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name="answer"
    )
    answer_md = models.TextField()  # final markdown
    citations = models.JSONField(default=list)  # [{"url":..., "title":...}, ...]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer for: {self.job.query[:50]}..."
