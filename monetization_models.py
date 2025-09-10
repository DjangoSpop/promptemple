# apps/monetization/models.py
"""
Monetization models for template library and premium features
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Subscription plans for premium access"""
    
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Features
    features = models.JSONField(default=dict)  # Store plan features
    
    # Limits
    monthly_template_generations = models.IntegerField(default=100)
    monthly_ai_requests = models.IntegerField(default=50)
    max_saved_templates = models.IntegerField(default=20)
    max_custom_categories = models.IntegerField(default=5)
    
    # Premium features
    access_premium_templates = models.BooleanField(default=False)
    template_export_enabled = models.BooleanField(default=False)
    api_access_enabled = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Display
    description = models.TextField()
    highlight_color = models.CharField(max_length=7, default='#6366F1')
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['order', 'price']
        
    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()}"


class UserSubscription(models.Model):
    """User subscription tracking"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Billing
    current_period_start = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    # Usage tracking
    monthly_template_usage = models.IntegerField(default=0)
    monthly_ai_requests = models.IntegerField(default=0)
    total_templates_saved = models.IntegerField(default=0)
    
    # Trial info
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trial']
    
    @property
    def can_access_premium_templates(self):
        return self.is_active and self.plan.access_premium_templates
    
    @property
    def remaining_template_generations(self):
        return max(0, self.plan.monthly_template_generations - self.monthly_template_usage)
    
    @property
    def remaining_ai_requests(self):
        return max(0, self.plan.monthly_ai_requests - self.monthly_ai_requests)


class TemplateAccessTier(models.Model):
    """Template access tiers for monetization"""
    
    TIER_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tier_type = models.CharField(max_length=20, choices=TIER_TYPES)
    
    # Pricing for individual access
    price_per_template = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    credits_required = models.IntegerField(default=0)
    
    # Requirements
    min_subscription_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='template_tiers'
    )
    
    # Features
    description = models.TextField()
    features = models.JSONField(default=list)
    
    # Display
    color = models.CharField(max_length=7, default='#6B7280')
    icon = models.CharField(max_length=50, default='star')
    
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'template_access_tiers'
        ordering = ['order']
        
    def __str__(self):
        return f"{self.name} ({self.tier_type})"


class TemplateRevenue(models.Model):
    """Track revenue from individual templates"""
    
    REVENUE_TYPES = [
        ('individual_purchase', 'Individual Purchase'),
        ('subscription_access', 'Subscription Access'),
        ('credit_purchase', 'Credit Purchase'),
        ('bundle_purchase', 'Bundle Purchase'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='revenue_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_purchases')
    
    # Revenue details
    revenue_type = models.CharField(max_length=30, choices=REVENUE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Template access
    access_tier = models.ForeignKey(TemplateAccessTier, on_delete=models.CASCADE)
    access_granted_at = models.DateTimeField(auto_now_add=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Attribution
    template_author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='authored_template_revenue',
        null=True,
        blank=True
    )
    author_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment details
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, default='completed')
    
    # Context
    purchase_context = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'template_revenue'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['template_author', 'created_at']),
        ]
        
    def __str__(self):
        return f"${self.amount} - {self.template.title} - {self.user.username}"


class UserCredit(models.Model):
    """User credit balance and transactions"""
    
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('bonus', 'Bonus'),
        ('referral', 'Referral'),
        ('template_spend', 'Template Access'),
        ('ai_request_spend', 'AI Request'),
        ('refund', 'Refund'),
        ('admin_adjustment', 'Admin Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Positive for credits added, negative for spent
    balance_after = models.IntegerField()
    
    # Context
    description = models.CharField(max_length=200)
    reference_id = models.CharField(max_length=100, blank=True)  # Reference to related object
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_credits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
        
    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.user.username}: {sign}{self.amount} credits ({self.transaction_type})"


class TemplateBundleManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def featured(self):
        return self.filter(is_featured=True, is_active=True)


class TemplateBundle(models.Model):
    """Curated bundles of templates for sale"""
    
    BUNDLE_TYPES = [
        ('curated', 'Curated Collection'),
        ('category', 'Category Bundle'),
        ('user_created', 'User Created'),
        ('ai_recommended', 'AI Recommended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    
    # Bundle details
    bundle_type = models.CharField(max_length=20, choices=BUNDLE_TYPES)
    templates = models.ManyToManyField('templates.Template', related_name='bundles')
    
    # Pricing
    access_tier = models.ForeignKey(TemplateAccessTier, on_delete=models.CASCADE)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    bundle_price = models.DecimalField(max_digits=10, decimal_places=2)
    credits_price = models.IntegerField(default=0)
    
    # Author/Creator
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_bundles')
    
    # Marketing
    cover_image = models.ImageField(upload_to='bundle_covers/', null=True, blank=True)
    marketing_text = models.TextField(blank=True)
    highlights = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Analytics
    purchase_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = TemplateBundleManager()
    
    class Meta:
        db_table = 'template_bundles'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    @property
    def template_count(self):
        return self.templates.count()
    
    @property
    def savings_amount(self):
        return self.original_price - self.bundle_price
    
    @property
    def savings_percentage(self):
        if self.original_price > 0:
            return round((self.savings_amount / self.original_price) * 100, 1)
        return 0


class UserTemplateAccess(models.Model):
    """Track user access to premium templates"""
    
    ACCESS_TYPES = [
        ('subscription', 'Subscription Access'),
        ('individual', 'Individual Purchase'),
        ('bundle', 'Bundle Purchase'),
        ('free', 'Free Access'),
        ('admin_granted', 'Admin Granted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_access')
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='user_access')
    
    # Access details
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Purchase info
    bundle = models.ForeignKey(TemplateBundle, on_delete=models.SET_NULL, null=True, blank=True)
    revenue_record = models.ForeignKey(TemplateRevenue, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Usage tracking
    first_used_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_template_access'
        unique_together = ['user', 'template']
        indexes = [
            models.Index(fields=['user', 'access_type']),
            models.Index(fields=['template', 'access_type']),
        ]
        
    def __str__(self):
        return f"{self.user.username} -> {self.template.title} ({self.access_type})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True


class PlatformRevenue(models.Model):
    """Track overall platform revenue and analytics"""
    
    REVENUE_SOURCES = [
        ('subscriptions', 'Subscriptions'),
        ('template_sales', 'Template Sales'),
        ('bundle_sales', 'Bundle Sales'),
        ('credit_purchases', 'Credit Purchases'),
        ('api_usage', 'API Usage'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Date tracking
    date = models.DateField()
    revenue_source = models.CharField(max_length=30, choices=REVENUE_SOURCES)
    
    # Revenue metrics
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Transaction metrics
    transaction_count = models.PositiveIntegerField(default=0)
    unique_customers = models.PositiveIntegerField(default=0)
    
    # Additional metrics
    metrics = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'platform_revenue'
        unique_together = ['date', 'revenue_source']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.date} - {self.revenue_source}: ${self.gross_revenue}"