import uuid
from django.db import models
from django.conf import settings


class PromptHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prompt_histories")
    source = models.CharField(max_length=50, blank=True)
    original_prompt = models.TextField()
    optimized_prompt = models.TextField(blank=True)
    model_used = models.CharField(max_length=100, blank=True)
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    credits_spent = models.IntegerField(default=0)
    intent_category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prompt_history"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["intent_category"]),
            models.Index(fields=["is_deleted"]),
        ]

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def __str__(self):
        return f"PromptHistory<{self.id}> by {self.user}"
