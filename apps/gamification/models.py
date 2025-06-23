from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

class Achievement(models.Model):
    """
    Achievements that users can unlock
    
    Types of achievements:
    - Usage-based (create X templates)
    - Streak-based (login X days)
    - Quality-based (get high ratings)
    - Social-based (share templates)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(
        max_length=50, 
        default='emoji_events',
        help_text="Icon identifier for UI"
    )
    
    # Achievement requirements
    requirement_type = models.CharField(
        max_length=50,
        help_text="Type of requirement (templates_created, streak_days, etc.)"
    )
    requirement_value = models.IntegerField(
        help_text="Target value to unlock achievement"
    )
    requirement_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable requirement description"
    )
    
    # Rewards
    credits_reward = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Credits awarded for this achievement"
    )
    experience_reward = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Experience points awarded"
    )
    
    # Metadata
    category = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Achievement category for organization"
    )
    rarity = models.CharField(
        max_length=20,
        choices=[
            ('common', 'Common'),
            ('uncommon', 'Uncommon'),
            ('rare', 'Rare'),
            ('epic', 'Epic'),
            ('legendary', 'Legendary')
        ],
        default='common',
        help_text="Achievement rarity level"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this achievement is currently available"
    )
    is_hidden = models.BooleanField(
        default=False,
        help_text="Hidden until user meets requirements"
    )
    
    # Ordering and timing
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this achievement becomes available"
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this achievement expires (null = permanent)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achievements'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['requirement_type']),
            models.Index(fields=['is_active', 'is_hidden']),
            models.Index(fields=['rarity']),
        ]

    def __str__(self):
        return self.name

    def is_available(self):
        """Check if achievement is currently available"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.available_from and now < self.available_from:
            return False
        
        if self.available_until and now > self.available_until:
            return False
        
        return True


class UserAchievement(models.Model):
    """
    Achievements unlocked by users
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_achievements'
    )
    achievement = models.ForeignKey(
        Achievement, 
        on_delete=models.CASCADE,
        related_name='user_unlocks'
    )
    
    # Progress tracking
    progress_value = models.IntegerField(
        default=0,
        help_text="Current progress towards achievement"
    )
    is_unlocked = models.BooleanField(
        default=False,
        help_text="Whether user has unlocked this achievement"
    )
    unlocked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When achievement was unlocked"
    )
    
    # Reward claiming
    is_claimed = models.BooleanField(
        default=False,
        help_text="Whether user has claimed the reward"
    )
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When reward was claimed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']
        indexes = [
            models.Index(fields=['user', 'is_unlocked']),
            models.Index(fields=['user', 'is_claimed']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

    @property
    def progress_percentage(self):
        """Calculate progress as percentage"""
        if self.achievement.requirement_value == 0:
            return 100
        return min(100, (self.progress_value / self.achievement.requirement_value) * 100)

    def check_unlock(self):
        """Check if achievement should be unlocked"""
        if self.is_unlocked:
            return False
        
        if self.progress_value >= self.achievement.requirement_value:
            self.is_unlocked = True
            self.unlocked_at = timezone.now()
            self.save(update_fields=['is_unlocked', 'unlocked_at'])
            return True
        
        return False


class DailyChallenge(models.Model):
    """
    Daily challenges for users
    
    Provides daily goals to encourage engagement
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Challenge requirements
    challenge_type = models.CharField(
        max_length=50,
        help_text="Type of challenge (complete_templates, use_ai_assistant, etc.)"
    )
    target_value = models.IntegerField(
        help_text="Target value to complete challenge"
    )
    
    # Rewards
    credits_reward = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0)],
        help_text="Credits awarded for completion"
    )
    experience_reward = models.IntegerField(
        default=25,
        validators=[MinValueValidator(0)],
        help_text="Experience points awarded"
    )
    
    # Timing
    date = models.DateField(
        help_text="Date this challenge is active"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this challenge is active"
    )
    
    # Difficulty and rarity
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
            ('expert', 'Expert')
        ],
        default='easy'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_challenges'
        unique_together = ['date', 'challenge_type']
        indexes = [
            models.Index(fields=['date', 'is_active']),
            models.Index(fields=['challenge_type']),
        ]

    def __str__(self):
        return f"{self.date} - {self.title}"


class UserDailyChallenge(models.Model):
    """
    User progress on daily challenges
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='daily_challenge_progress'
    )
    challenge = models.ForeignKey(
        DailyChallenge, 
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    
    # Progress tracking
    progress_value = models.IntegerField(
        default=0,
        help_text="Current progress towards challenge completion"
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="Whether challenge is completed"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When challenge was completed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_daily_challenges'
        unique_together = ['user', 'challenge']
        indexes = [
            models.Index(fields=['user', 'challenge']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"

    @property
    def progress_percentage(self):
        """Calculate progress as percentage"""
        if self.challenge.target_value == 0:
            return 100
        return min(100, (self.progress_value / self.challenge.target_value) * 100)


class CreditTransaction(models.Model):
    """
    Credit transaction history for transparency
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='credit_transactions'
    )
    
    # Transaction details
    amount = models.IntegerField(
        help_text="Amount of credits (positive for earning, negative for spending)"
    )
    balance_after = models.IntegerField(
        help_text="User's credit balance after this transaction"
    )
    transaction_type = models.CharField(
        max_length=50,
        choices=[
            ('earned_ad', 'Earned from Advertisement'),
            ('earned_achievement', 'Earned from Achievement'),
            ('earned_challenge', 'Earned from Daily Challenge'),
            ('earned_completion', 'Earned from Template Completion'),
            ('earned_rating', 'Earned from Template Rating'),
            ('earned_referral', 'Earned from Referral'),
            ('spent_ai', 'Spent on AI Features'),
            ('spent_premium', 'Spent on Premium Features'),
            ('spent_template', 'Spent on Premium Template'),
            ('bonus', 'Bonus Credits'),
            ('refund', 'Refund'),
            ('admin_adjustment', 'Admin Adjustment'),
        ],
        help_text="Type of transaction"
    )
    description = models.CharField(
        max_length=200,
        help_text="Human-readable description of transaction"
    )
    
    # Related objects (for tracking)
    related_object_type = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Type of related object (achievement, template, etc.)"
    )
    related_object_id = models.CharField(
        max_length=100, 
        blank=True,
        help_text="ID of related object"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['related_object_type', 'related_object_id']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.amount} credits ({self.transaction_type})"


class UserLevel(models.Model):
    """
    Level definitions and rewards
    """
    
    level = models.PositiveIntegerField(
        unique=True,
        help_text="Level number"
    )
    name = models.CharField(
        max_length=100,
        help_text="Level name/title"
    )
    experience_required = models.IntegerField(
        help_text="Total experience points required to reach this level"
    )
    
    # Level rewards
    credits_reward = models.IntegerField(
        default=0,
        help_text="Credits awarded when reaching this level"
    )
    title_reward = models.CharField(
        max_length=100,
        blank=True,
        help_text="Special title awarded at this level"
    )
    
    # Perks unlocked at this level
    max_templates = models.IntegerField(
        default=10,
        help_text="Maximum templates user can create at this level"
    )
    ai_requests_per_day = models.IntegerField(
        default=5,
        help_text="AI requests allowed per day at this level"
    )
    can_create_premium = models.BooleanField(
        default=False,
        help_text="Can create premium templates"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_levels'
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level}: {self.name}"