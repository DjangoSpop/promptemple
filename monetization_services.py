# apps/monetization/services.py
"""
Monetization services for template library and premium features
"""
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q

try:
    from monetization_models import (
        SubscriptionPlan, UserSubscription, TemplateAccessTier,
        TemplateRevenue, UserCredit, TemplateBundle, UserTemplateAccess,
        PlatformRevenue
    )
    from apps.chat.models import ExtractedTemplate
    from django_models import Template, User
except ImportError:
    # Handle import errors gracefully
    pass

logger = logging.getLogger(__name__)
User = get_user_model()


class SubscriptionService:
    """Service for managing user subscriptions and access control"""
    
    def __init__(self):
        self.default_plan = self._get_default_plan()
    
    def _get_default_plan(self):
        """Get the default free plan"""
        try:
            return SubscriptionPlan.objects.get(plan_type='free', is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return None
    
    def get_user_subscription(self, user: User) -> Optional['UserSubscription']:
        """Get user's current subscription"""
        try:
            return UserSubscription.objects.get(user=user)
        except UserSubscription.DoesNotExist:
            # Create default subscription if none exists
            if self.default_plan:
                return self.create_subscription(user, self.default_plan)
            return None
    
    def create_subscription(self, user: User, plan: 'SubscriptionPlan', trial_days: int = 0) -> 'UserSubscription':
        """Create new subscription for user"""
        
        # Calculate trial period
        trial_end = None
        if trial_days > 0:
            trial_end = timezone.now() + timedelta(days=trial_days)
        
        # Calculate subscription period
        if plan.billing_cycle == 'monthly':
            period_end = timezone.now() + timedelta(days=30)
        elif plan.billing_cycle == 'quarterly':
            period_end = timezone.now() + timedelta(days=90)
        elif plan.billing_cycle == 'yearly':
            period_end = timezone.now() + timedelta(days=365)
        else:
            period_end = None  # Lifetime
        
        with transaction.atomic():
            # Cancel existing subscription
            existing = UserSubscription.objects.filter(user=user).first()
            if existing:
                existing.status = 'canceled'
                existing.canceled_at = timezone.now()
                existing.save()
            
            # Create new subscription
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status='trial' if trial_days > 0 else 'active',
                expires_at=period_end,
                current_period_end=period_end,
                trial_started_at=timezone.now() if trial_days > 0 else None,
                trial_ends_at=trial_end
            )
            
            # Update user premium status
            user.is_premium = plan.plan_type != 'free'
            if plan.plan_type != 'free':
                user.premium_expires_at = period_end
            user.save(update_fields=['is_premium', 'premium_expires_at'])
            
            logger.info(f"Created subscription for user {user.id}: {plan.name}")
            return subscription
    
    def check_template_access(self, user: User, template: 'Template') -> Dict[str, Any]:
        """Check if user can access a template"""
        subscription = self.get_user_subscription(user)
        
        result = {
            'has_access': False,
            'access_type': None,
            'reason': None,
            'upgrade_required': False,
            'subscription_plan': subscription.plan.name if subscription else 'No subscription'
        }
        
        # Check if template is free
        if not hasattr(template, 'access_tier') or not template.access_tier:
            result['has_access'] = True
            result['access_type'] = 'free'
            return result
        
        # Check if user owns the template
        if template.author == user:
            result['has_access'] = True
            result['access_type'] = 'owner'
            return result
        
        # Check individual access
        access_record = UserTemplateAccess.objects.filter(
            user=user, 
            template=template
        ).first()
        
        if access_record and access_record.is_active:
            result['has_access'] = True
            result['access_type'] = access_record.access_type
            return result
        
        # Check subscription access
        if subscription and subscription.is_active:
            if subscription.plan.access_premium_templates:
                result['has_access'] = True
                result['access_type'] = 'subscription'
                return result
        
        # Access denied
        result['reason'] = 'Premium template requires subscription or purchase'
        result['upgrade_required'] = True
        return result
    
    def can_generate_template(self, user: User) -> Dict[str, Any]:
        """Check if user can generate more templates"""
        subscription = self.get_user_subscription(user)
        
        if not subscription:
            return {
                'can_generate': False,
                'reason': 'No subscription found',
                'remaining': 0,
                'limit': 0
            }
        
        remaining = subscription.remaining_template_generations
        
        return {
            'can_generate': remaining > 0,
            'reason': 'Monthly limit reached' if remaining <= 0 else None,
            'remaining': remaining,
            'limit': subscription.plan.monthly_template_generations
        }
    
    def can_make_ai_request(self, user: User) -> Dict[str, Any]:
        """Check if user can make AI requests"""
        subscription = self.get_user_subscription(user)
        
        if not subscription:
            return {
                'can_request': False,
                'reason': 'No subscription found',
                'remaining': 0,
                'limit': 0
            }
        
        remaining = subscription.remaining_ai_requests
        
        return {
            'can_request': remaining > 0,
            'reason': 'Monthly limit reached' if remaining <= 0 else None,
            'remaining': remaining,
            'limit': subscription.plan.monthly_ai_requests
        }
    
    def record_template_generation(self, user: User):
        """Record template generation usage"""
        subscription = self.get_user_subscription(user)
        if subscription:
            subscription.monthly_template_usage += 1
            subscription.save(update_fields=['monthly_template_usage'])
    
    def record_ai_request(self, user: User):
        """Record AI request usage"""
        subscription = self.get_user_subscription(user)
        if subscription:
            subscription.monthly_ai_requests += 1
            subscription.save(update_fields=['monthly_ai_requests'])


class TemplateMonetizationService:
    """Service for template monetization and revenue tracking"""
    
    def __init__(self):
        self.credit_service = CreditService()
    
    def process_template_extraction_reward(self, extracted_template: 'ExtractedTemplate') -> Dict[str, Any]:
        """Process rewards for users who contribute high-quality templates"""
        
        if not extracted_template.published_template:
            return {'rewarded': False, 'reason': 'Template not published'}
        
        # Get monetization analysis
        analysis = extracted_template.langchain_analysis.get('monetization_analysis', {})
        potential = analysis.get('potential', 'low')
        
        rewards = {
            'credits_earned': 0,
            'revenue_share': Decimal('0.00'),
            'bonuses': []
        }
        
        # Base contribution reward
        if extracted_template.status == 'approved':
            base_credits = 10
            if potential == 'high':
                base_credits = 25
            elif potential == 'medium':
                base_credits = 15
            
            self.credit_service.add_credits(
                extracted_template.user,
                base_credits,
                'template_contribution',
                f"Contribution reward for: {extracted_template.title}"
            )
            rewards['credits_earned'] += base_credits
            rewards['bonuses'].append(f"Contribution: +{base_credits} credits")
        
        # Quality bonus
        if extracted_template.quality_rating == 'high' and extracted_template.confidence_score >= 0.8:
            quality_credits = 15
            self.credit_service.add_credits(
                extracted_template.user,
                quality_credits,
                'quality_bonus',
                f"Quality bonus for: {extracted_template.title}"
            )
            rewards['credits_earned'] += quality_credits
            rewards['bonuses'].append(f"Quality bonus: +{quality_credits} credits")
        
        # Set up revenue sharing for future purchases
        if potential in ['high', 'medium']:
            self._setup_revenue_sharing(extracted_template.published_template, extracted_template.user)
            rewards['bonuses'].append("Revenue sharing enabled")
        
        logger.info(f"Processed rewards for extracted template {extracted_template.id}: {rewards}")
        return rewards
    
    def _setup_revenue_sharing(self, template: 'Template', author: User):
        """Set up revenue sharing for template author"""
        # This would set metadata for revenue sharing
        # When someone purchases access to this template, author gets a share
        if not hasattr(template, 'monetization_metadata'):
            template.monetization_metadata = {}
        
        template.monetization_metadata.update({
            'revenue_sharing_enabled': True,
            'author_share_percentage': 30,  # 30% to author, 70% to platform
            'contributed_via_extraction': True
        })
        template.save(update_fields=['monetization_metadata'])
    
    def process_template_purchase(self, user: User, template: 'Template', access_tier: 'TemplateAccessTier') -> Dict[str, Any]:
        """Process template purchase and revenue distribution"""
        
        purchase_amount = access_tier.price_per_template
        credits_cost = access_tier.credits_required
        
        with transaction.atomic():
            # Check if user can afford it
            if credits_cost > 0:
                if not self.credit_service.has_sufficient_credits(user, credits_cost):
                    return {
                        'success': False,
                        'error': 'Insufficient credits',
                        'required': credits_cost,
                        'available': self.credit_service.get_credit_balance(user)
                    }
                
                # Deduct credits
                self.credit_service.spend_credits(
                    user,
                    credits_cost,
                    'template_purchase',
                    f"Purchase: {template.title}"
                )
            
            # Create revenue record
            revenue = TemplateRevenue.objects.create(
                template=template,
                user=user,
                revenue_type='individual_purchase',
                amount=purchase_amount,
                access_tier=access_tier,
                template_author=template.author,
                author_share=self._calculate_author_share(template, purchase_amount),
                platform_share=purchase_amount - self._calculate_author_share(template, purchase_amount)
            )
            
            # Grant template access
            access = UserTemplateAccess.objects.create(
                user=user,
                template=template,
                access_type='individual',
                revenue_record=revenue
            )
            
            # Process author revenue share
            self._process_author_revenue_share(template, revenue)
            
            return {
                'success': True,
                'access_id': str(access.id),
                'revenue_id': str(revenue.id),
                'amount_paid': purchase_amount,
                'credits_spent': credits_cost
            }
    
    def _calculate_author_share(self, template: 'Template', amount: Decimal) -> Decimal:
        """Calculate author's share of template revenue"""
        if hasattr(template, 'monetization_metadata'):
            metadata = template.monetization_metadata
            if metadata.get('revenue_sharing_enabled', False):
                share_percentage = metadata.get('author_share_percentage', 30)
                return amount * (share_percentage / 100)
        
        return Decimal('0.00')
    
    def _process_author_revenue_share(self, template: 'Template', revenue: 'TemplateRevenue'):
        """Process revenue share for template author"""
        if revenue.author_share > 0 and template.author:
            # Convert revenue share to credits (e.g., $1 = 100 credits)
            credits_to_award = int(revenue.author_share * 100)
            
            if credits_to_award > 0:
                self.credit_service.add_credits(
                    template.author,
                    credits_to_award,
                    'revenue_share',
                    f"Revenue share from: {template.title}"
                )
                
                logger.info(f"Awarded {credits_to_award} credits to {template.author.username} for template revenue")


class CreditService:
    """Service for managing user credits"""
    
    def get_credit_balance(self, user: User) -> int:
        """Get user's current credit balance"""
        last_transaction = UserCredit.objects.filter(user=user).order_by('-created_at').first()
        return last_transaction.balance_after if last_transaction else 0
    
    def has_sufficient_credits(self, user: User, amount: int) -> bool:
        """Check if user has sufficient credits"""
        return self.get_credit_balance(user) >= amount
    
    def add_credits(self, user: User, amount: int, transaction_type: str, description: str, reference_id: str = None) -> 'UserCredit':
        """Add credits to user account"""
        current_balance = self.get_credit_balance(user)
        new_balance = current_balance + amount
        
        return UserCredit.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=new_balance,
            description=description,
            reference_id=reference_id or ''
        )
    
    def spend_credits(self, user: User, amount: int, transaction_type: str, description: str, reference_id: str = None) -> 'UserCredit':
        """Spend credits from user account"""
        current_balance = self.get_credit_balance(user)
        
        if current_balance < amount:
            raise ValueError(f"Insufficient credits. Available: {current_balance}, Required: {amount}")
        
        new_balance = current_balance - amount
        
        return UserCredit.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=-amount,  # Negative for spending
            balance_after=new_balance,
            description=description,
            reference_id=reference_id or ''
        )
    
    def get_credit_history(self, user: User, limit: int = 50) -> List['UserCredit']:
        """Get user's credit transaction history"""
        return list(UserCredit.objects.filter(user=user).order_by('-created_at')[:limit])


class BundleService:
    """Service for managing template bundles"""
    
    def create_ai_recommended_bundle(self, user: User, templates: List['Template'], title: str = None) -> 'TemplateBundle':
        """Create AI-recommended bundle based on user behavior"""
        
        if not title:
            title = f"Recommended Templates for {user.username}"
        
        # Calculate pricing
        total_individual_price = sum(
            getattr(t, 'access_tier', {}).get('price_per_template', Decimal('5.00')) 
            for t in templates
        )
        bundle_discount = 0.25  # 25% discount
        bundle_price = total_individual_price * (1 - bundle_discount)
        
        # Create bundle
        bundle = TemplateBundle.objects.create(
            title=title,
            slug=f"ai-recommended-{user.id}-{timezone.now().strftime('%Y%m%d')}",
            description=f"AI-curated collection of {len(templates)} templates personalized for you",
            bundle_type='ai_recommended',
            original_price=total_individual_price,
            bundle_price=bundle_price,
            credits_price=int(bundle_price * 50),  # $1 = 50 credits for bundles
            created_by=user
        )
        
        # Add templates to bundle
        bundle.templates.set(templates)
        
        return bundle
    
    def get_bundle_recommendations(self, user: User) -> List[Dict[str, Any]]:
        """Get bundle recommendations for user"""
        # This would use AI to recommend bundles based on user behavior
        # For now, return popular bundles
        
        bundles = TemplateBundle.objects.featured().order_by('-purchase_count')[:5]
        
        recommendations = []
        for bundle in bundles:
            recommendations.append({
                'bundle_id': str(bundle.id),
                'title': bundle.title,
                'description': bundle.description,
                'template_count': bundle.template_count,
                'original_price': bundle.original_price,
                'bundle_price': bundle.bundle_price,
                'savings_percentage': bundle.savings_percentage,
                'reason': 'Popular choice'
            })
        
        return recommendations


class AnalyticsService:
    """Service for monetization analytics"""
    
    def get_user_monetization_stats(self, user: User) -> Dict[str, Any]:
        """Get monetization statistics for user"""
        
        # Template contributions
        contributed_templates = Template.objects.filter(author=user, is_ai_generated=True).count()
        
        # Revenue earned
        total_revenue = TemplateRevenue.objects.filter(template_author=user).aggregate(
            total=Sum('author_share')
        )['total'] or Decimal('0.00')
        
        # Credits
        credit_balance = CreditService().get_credit_balance(user)
        total_credits_earned = UserCredit.objects.filter(
            user=user, 
            amount__gt=0
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Template access
        templates_purchased = UserTemplateAccess.objects.filter(
            user=user,
            access_type__in=['individual', 'bundle']
        ).count()
        
        return {
            'contributed_templates': contributed_templates,
            'total_revenue_earned': float(total_revenue),
            'current_credit_balance': credit_balance,
            'total_credits_earned': total_credits_earned,
            'templates_purchased': templates_purchased,
            'subscription_status': self._get_subscription_status(user)
        }
    
    def _get_subscription_status(self, user: User) -> Dict[str, Any]:
        """Get user's subscription status"""
        subscription_service = SubscriptionService()
        subscription = subscription_service.get_user_subscription(user)
        
        if not subscription:
            return {'plan': 'None', 'status': 'inactive'}
        
        return {
            'plan': subscription.plan.name,
            'status': subscription.status,
            'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
            'remaining_templates': subscription.remaining_template_generations,
            'remaining_ai_requests': subscription.remaining_ai_requests
        }
    
    def get_platform_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get platform revenue summary"""
        since_date = timezone.now().date() - timedelta(days=days)
        
        revenue_data = PlatformRevenue.objects.filter(
            date__gte=since_date
        ).aggregate(
            total_gross=Sum('gross_revenue'),
            total_net=Sum('net_revenue'),
            total_transactions=Sum('transaction_count')
        )
        
        return {
            'period_days': days,
            'total_gross_revenue': float(revenue_data['total_gross'] or 0),
            'total_net_revenue': float(revenue_data['total_net'] or 0),
            'total_transactions': revenue_data['total_transactions'] or 0,
            'average_transaction_value': (
                float(revenue_data['total_gross'] or 0) / max(revenue_data['total_transactions'] or 1, 1)
            )
        }


# Initialize services
subscription_service = SubscriptionService()
monetization_service = TemplateMonetizationService()
credit_service = CreditService()
bundle_service = BundleService()
analytics_service = AnalyticsService()