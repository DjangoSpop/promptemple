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


class PromptIteration(models.Model):
    """
    Tracks iterations and versions of prompts, enabling version control
    for prompt engineering workflows and AI interactions history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="prompt_iterations"
    )
    parent_prompt = models.ForeignKey(
        PromptHistory,
        on_delete=models.CASCADE,
        related_name="iterations",
        help_text="The original prompt this iteration is based on"
    )
    previous_iteration = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_iterations",
        help_text="The previous version in the iteration chain"
    )
    
    # Version tracking
    iteration_number = models.IntegerField(
        default=1,
        help_text="Sequential iteration number for this prompt chain"
    )
    version_tag = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional semantic version tag (e.g., 'v1.0', 'draft-2')"
    )
    
    # Prompt content
    prompt_text = models.TextField(
        help_text="The current iteration of the prompt"
    )
    system_message = models.TextField(
        blank=True,
        help_text="Optional system message for this iteration"
    )
    
    # AI Response
    ai_response = models.TextField(
        blank=True,
        help_text="AI generated response for this iteration"
    )
    response_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="AI model used for this response"
    )
    
    # Interaction metadata
    interaction_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual Edit'),
            ('optimization', 'AI Optimization'),
            ('refinement', 'User Refinement'),
            ('extension', 'Extension/Add-on'),
            ('correction', 'Error Correction'),
            ('experiment', 'Experimental Variation'),
        ],
        default='manual',
        help_text="Type of iteration/modification"
    )
    
    # Performance metrics
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(
        default=0,
        help_text="Response time in milliseconds"
    )
    credits_spent = models.IntegerField(default=0)
    
    # Quality tracking
    user_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="User rating (1-5) for this iteration"
    )
    feedback_notes = models.TextField(
        blank=True,
        help_text="User notes about this iteration"
    )
    
    # Change tracking
    changes_summary = models.TextField(
        blank=True,
        help_text="Summary of changes from previous iteration"
    )
    diff_size = models.IntegerField(
        default=0,
        help_text="Character difference from previous iteration"
    )
    
    # Metadata
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Model parameters used (temperature, max_tokens, etc.)"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization and search"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional flexible metadata"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this is the active/current iteration"
    )
    is_bookmarked = models.BooleanField(
        default=False,
        help_text="User bookmark for important iterations"
    )
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prompt_iterations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent_prompt', 'iteration_number']),
            models.Index(fields=['is_active', 'is_deleted']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['is_bookmarked']),
        ]
        unique_together = [['parent_prompt', 'iteration_number']]

    def soft_delete(self):
        """Soft delete the iteration"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def calculate_diff_size(self):
        """Calculate character difference from previous iteration"""
        if self.previous_iteration:
            prev_text = self.previous_iteration.prompt_text
            current_text = self.prompt_text
            self.diff_size = abs(len(current_text) - len(prev_text))
        return self.diff_size

    def set_as_active(self):
        """Mark this iteration as the active one"""
        # Deactivate all other iterations in the chain
        PromptIteration.objects.filter(
            parent_prompt=self.parent_prompt
        ).exclude(id=self.id).update(is_active=False)
        
        self.is_active = True
        self.save(update_fields=['is_active'])

    @property
    def iteration_chain_length(self):
        """Get the total number of iterations in this chain"""
        return PromptIteration.objects.filter(
            parent_prompt=self.parent_prompt,
            is_deleted=False
        ).count()

    @property
    def has_next_iteration(self):
        """Check if there's a next iteration after this one"""
        return self.next_iterations.filter(is_deleted=False).exists()

    def __str__(self):
        return f"Iteration {self.iteration_number} of {self.parent_prompt.id}"


class ConversationThread(models.Model):
    """
    Groups multiple prompt iterations into a conversation thread,
    enabling multi-turn AI conversations with full history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_threads"
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Conversation title/summary"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of conversation purpose"
    )
    
    # Thread metadata
    total_iterations = models.IntegerField(
        default=0,
        help_text="Total number of iterations in this thread"
    )
    total_tokens = models.IntegerField(
        default=0,
        help_text="Total tokens consumed in this thread"
    )
    total_credits = models.IntegerField(
        default=0,
        help_text="Total credits spent on this thread"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('archived', 'Archived'),
            ('completed', 'Completed'),
        ],
        default='active'
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether this thread is shared with others"
    )
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversation_threads"
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_activity_at']),
            models.Index(fields=['is_shared', 'is_deleted']),
        ]

    def add_iteration(self, iteration):
        """Add an iteration to this thread"""
        ThreadMessage.objects.create(
            thread=self,
            iteration=iteration,
            message_order=self.total_iterations + 1
        )
        self.total_iterations += 1
        self.total_tokens += iteration.tokens_input + iteration.tokens_output
        self.total_credits += iteration.credits_spent
        self.last_activity_at = iteration.created_at
        self.save()

    def __str__(self):
        return f"Thread: {self.title or self.id} ({self.total_iterations} messages)"


class ThreadMessage(models.Model):
    """
    Links prompt iterations to conversation threads with ordering.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        ConversationThread,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    iteration = models.ForeignKey(
        PromptIteration,
        on_delete=models.CASCADE,
        related_name="thread_memberships"
    )
    message_order = models.IntegerField(
        help_text="Order of this message in the thread"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thread_messages"
        ordering = ['message_order']
        unique_together = [['thread', 'message_order']]
        indexes = [
            models.Index(fields=['thread', 'message_order']),
        ]

    def __str__(self):
        return f"Message {self.message_order} in {self.thread.title or self.thread.id}"
