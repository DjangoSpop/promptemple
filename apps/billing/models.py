"""
Billing and Subscription Models
Handles freemium features, subscriptions, and payment processing
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from decimal import Decimal

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Available subscription plans"""
    
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_INTERVALS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    billing_interval = models.CharField(max_length=20, choices=BILLING_INTERVALS)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    
    # Features and limits
    daily_template_limit = models.IntegerField(default=5)
    daily_copy_limit = models.IntegerField(default=3)
    premium_templates_access = models.BooleanField(default=False)
    ads_free = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    collaboration_features = models.BooleanField(default=False)
    
    # Configuration
    features = models.JSONField(default=list, blank=True)  # List of feature names
    limitations = models.JSONField(default=dict, blank=True)  # Feature limits
    
    # Stripe integration
    stripe_price_id = models.CharField(max_length=100, blank=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)  # Show "Most Popular" badge
    
    # Display
    description = models.TextField(blank=True)
    features_list = models.JSONField(default=list, blank=True)  # For display
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} ({self.billing_interval})"
    
    @property
    def is_free(self):
        return self.plan_type == 'free'
    
    @property
    def monthly_price(self):
        """Convert price to monthly equivalent for comparison"""
        if self.billing_interval == 'yearly':
            return self.price / 12
        elif self.billing_interval == 'lifetime':
            return self.price / 120  # Assume 10 year lifetime
        return self.price


class UserSubscription(models.Model):
    """User subscription status and details"""
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
        ('past_due', 'Past Due'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Trial information
    is_trial = models.BooleanField(default=False)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    
    # Usage tracking
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    
    # Billing
    auto_renew = models.BooleanField(default=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status in ['active', 'trial']:
            if self.expires_at:
                return timezone.now() < self.expires_at
            return True
        return False
    
    @property
    def is_premium(self):
        """Check if user has premium access"""
        return self.is_active and self.plan.plan_type in ['premium', 'enterprise']
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return None
    
    def can_access_feature(self, feature_name):
        """Check if user can access a specific feature"""
        if not self.is_active:
            return False
        return feature_name in self.plan.features
    
    def get_daily_limits(self):
        """Get current daily usage limits"""
        return {
            'templates': self.plan.daily_template_limit,
            'copies': self.plan.daily_copy_limit,
        }


class UsageQuota(models.Model):
    """Track daily/monthly usage quotas for users"""
    
    QUOTA_TYPES = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_quotas')
    quota_type = models.CharField(max_length=20, choices=QUOTA_TYPES)
    quota_date = models.DateField()  # The date this quota applies to
    
    # Usage tracking
    templates_used = models.IntegerField(default=0)
    copies_made = models.IntegerField(default=0)
    api_calls_made = models.IntegerField(default=0)
    
    # Limits (copied from subscription plan for historical tracking)
    template_limit = models.IntegerField()
    copy_limit = models.IntegerField()
    api_call_limit = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usage_quotas'
        unique_together = ['user', 'quota_type', 'quota_date']
        indexes = [
            models.Index(fields=['user', 'quota_date']),
            models.Index(fields=['quota_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.quota_type} {self.quota_date}"
    
    @property
    def templates_remaining(self):
        return max(0, self.template_limit - self.templates_used)
    
    @property
    def copies_remaining(self):
        return max(0, self.copy_limit - self.copies_made)
    
    @property
    def usage_percentage(self):
        """Get overall usage percentage"""
        total_limit = self.template_limit + self.copy_limit
        total_used = self.templates_used + self.copies_made
        if total_limit == 0:
            return 0
        return min(100, (total_used / total_limit) * 100)


class PaymentHistory(models.Model):
    """Track payment history and transactions"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_history')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    
    # External references
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timing
    payment_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_history'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"


class BillingAddress(models.Model):
    """Store billing addresses for users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_addresses')
    
    # Address fields
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2)  # ISO country code
    
    # Tax information
    tax_id = models.CharField(max_length=50, blank=True)  # VAT, SSN, etc.
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_addresses'
    
    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"


class Coupon(models.Model):
    """Discount coupons and promotional codes"""
    
    COUPON_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_trial', 'Free Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Discount configuration
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Usage limits
    max_redemptions = models.IntegerField(null=True, blank=True)
    current_redemptions = models.IntegerField(default=0)
    max_redemptions_per_user = models.IntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Restrictions
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    first_time_users_only = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Stripe integration
    stripe_coupon_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_redemptions is None or self.current_redemptions < self.max_redemptions)
        )
    
    def can_be_used_by(self, user):
        """Check if coupon can be used by a specific user"""
        if not self.is_valid:
            return False
        
        # Check first-time user restriction
        if self.first_time_users_only and UserSubscription.objects.filter(user=user).exists():
            return False
        
        # Check per-user redemption limit
        user_redemptions = CouponRedemption.objects.filter(coupon=self, user=user).count()
        if user_redemptions >= self.max_redemptions_per_user:
            return False
        
        return True


class CouponRedemption(models.Model):
    """Track coupon usage"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_redemptions')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='coupon_redemptions')
    
    # Discount applied
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Context
    redeemed_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(PaymentHistory, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'coupon_redemptions'
        unique_together = ['coupon', 'user']  # Prevent duplicate redemptions
    
    def __str__(self):
        return f"{self.user.username} redeemed {self.coupon.code}"


class Invoice(models.Model):
    """Store invoice information"""
    
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('uncollectible', 'Uncollectible'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Billing period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # External references
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Files
    pdf_url = models.URLField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.username}"


class SubscriptionChangeRequest(models.Model):
    """Track subscription plan changes"""
    
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    CHANGE_TYPES = [
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('cancel', 'Cancel'),
        ('pause', 'Pause'),
        ('resume', 'Resume'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_changes')
    current_subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='change_requests')
    
    # Change details
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    new_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    effective_date = models.DateTimeField()  # When change should take effect
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Reason and notes
    reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Proration and billing
    proration_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'subscription_change_requests'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.change_type} to {self.new_plan}"