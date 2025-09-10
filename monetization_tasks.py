# tasks/monetization_tasks.py
"""
Background tasks for monetization and revenue processing
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.contrib.auth import get_user_model

try:
    from monetization_models import (
        UserSubscription, TemplateRevenue, UserCredit, 
        PlatformRevenue, UserTemplateAccess
    )
    from monetization_services import (
        subscription_service, monetization_service, 
        credit_service, analytics_service
    )
    from apps.chat.models import ExtractedTemplate
    from django_models import Template
except ImportError:
    pass

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True)
def process_revenue_sharing(self):
    """Process revenue sharing for template authors"""
    try:
        # Find unpaid revenue records
        unpaid_revenue = TemplateRevenue.objects.filter(
            payment_status='completed',
            author_share__gt=0,
            template_author__isnull=False
        ).select_related('template_author')
        
        processed_count = 0
        total_credits_awarded = 0
        
        for revenue in unpaid_revenue:
            try:
                # Convert revenue share to credits (e.g., $1 = 100 credits)
                credits_to_award = int(revenue.author_share * 100)
                
                if credits_to_award > 0:
                    credit_service.add_credits(
                        revenue.template_author,
                        credits_to_award,
                        'revenue_share',
                        f"Revenue share from template: {revenue.template.title}",
                        reference_id=str(revenue.id)
                    )
                    
                    total_credits_awarded += credits_to_award
                    processed_count += 1
                    
                    logger.info(f"Awarded {credits_to_award} credits to {revenue.template_author.username}")
                    
            except Exception as e:
                logger.error(f"Error processing revenue share for {revenue.id}: {e}")
                continue
        
        return {
            'processed_count': processed_count,
            'total_credits_awarded': total_credits_awarded,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in process_revenue_sharing: {e}")
        raise


@shared_task(bind=True)
def update_subscription_statuses(self):
    """Update subscription statuses and handle expirations"""
    try:
        now = timezone.now()
        
        # Find expired subscriptions
        expired_subscriptions = UserSubscription.objects.filter(
            status='active',
            expires_at__lt=now
        )
        
        expired_count = 0
        
        for subscription in expired_subscriptions:
            try:
                with transaction.atomic():
                    # Update subscription status
                    subscription.status = 'expired'
                    subscription.save()
                    
                    # Update user premium status
                    user = subscription.user
                    user.is_premium = False
                    user.premium_expires_at = subscription.expires_at
                    user.save(update_fields=['is_premium', 'premium_expires_at'])
                    
                    expired_count += 1
                    logger.info(f"Expired subscription for user {user.username}")
                    
            except Exception as e:
                logger.error(f"Error expiring subscription {subscription.id}: {e}")
                continue
        
        # Reset monthly usage counters for new billing periods
        reset_count = self._reset_monthly_usage_counters()
        
        return {
            'expired_subscriptions': expired_count,
            'usage_counters_reset': reset_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in update_subscription_statuses: {e}")
        raise


def _reset_monthly_usage_counters(self):
    """Reset monthly usage counters for subscriptions in new billing periods"""
    now = timezone.now()
    
    # Find subscriptions that have entered a new billing period
    subscriptions_to_reset = UserSubscription.objects.filter(
        status='active',
        current_period_end__lt=now
    )
    
    reset_count = 0
    
    for subscription in subscriptions_to_reset:
        try:
            # Calculate new billing period
            if subscription.plan.billing_cycle == 'monthly':
                new_period_end = now + timedelta(days=30)
            elif subscription.plan.billing_cycle == 'quarterly':
                new_period_end = now + timedelta(days=90)
            elif subscription.plan.billing_cycle == 'yearly':
                new_period_end = now + timedelta(days=365)
            else:
                continue  # Skip lifetime subscriptions
            
            # Reset usage counters
            subscription.monthly_template_usage = 0
            subscription.monthly_ai_requests = 0
            subscription.current_period_start = now
            subscription.current_period_end = new_period_end
            subscription.save()
            
            reset_count += 1
            logger.info(f"Reset usage counters for user {subscription.user.username}")
            
        except Exception as e:
            logger.error(f"Error resetting usage for subscription {subscription.id}: {e}")
            continue
    
    return reset_count


@shared_task(bind=True)
def calculate_platform_revenue(self, date: str = None):
    """Calculate daily platform revenue metrics"""
    try:
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()
        
        # Calculate revenue by source
        revenue_sources = {
            'subscriptions': self._calculate_subscription_revenue(target_date),
            'template_sales': self._calculate_template_sales_revenue(target_date),
            'bundle_sales': self._calculate_bundle_sales_revenue(target_date),
            'credit_purchases': self._calculate_credit_purchases_revenue(target_date),
        }
        
        # Create or update platform revenue records
        for source, data in revenue_sources.items():
            if data['gross_revenue'] > 0:
                PlatformRevenue.objects.update_or_create(
                    date=target_date,
                    revenue_source=source,
                    defaults={
                        'gross_revenue': data['gross_revenue'],
                        'net_revenue': data['net_revenue'],
                        'transaction_count': data['transaction_count'],
                        'unique_customers': data['unique_customers'],
                        'metrics': data.get('metrics', {})
                    }
                )
        
        total_gross = sum(data['gross_revenue'] for data in revenue_sources.values())
        total_net = sum(data['net_revenue'] for data in revenue_sources.values())
        
        return {
            'date': target_date.isoformat(),
            'total_gross_revenue': float(total_gross),
            'total_net_revenue': float(total_net),
            'revenue_by_source': {
                source: {
                    'gross': float(data['gross_revenue']),
                    'net': float(data['net_revenue']),
                    'transactions': data['transaction_count']
                }
                for source, data in revenue_sources.items()
            },
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in calculate_platform_revenue: {e}")
        raise


def _calculate_subscription_revenue(target_date):
    """Calculate subscription revenue for a specific date"""
    # This would calculate new subscriptions and renewals for the date
    subscriptions = UserSubscription.objects.filter(
        started_at__date=target_date,
        status='active'
    )
    
    gross_revenue = sum(sub.plan.price for sub in subscriptions)
    net_revenue = gross_revenue * Decimal('0.97')  # 3% payment processing fee
    
    return {
        'gross_revenue': gross_revenue,
        'net_revenue': net_revenue,
        'transaction_count': subscriptions.count(),
        'unique_customers': subscriptions.values('user').distinct().count(),
        'metrics': {
            'average_subscription_value': float(gross_revenue / max(subscriptions.count(), 1))
        }
    }


def _calculate_template_sales_revenue(target_date):
    """Calculate template sales revenue for a specific date"""
    template_sales = TemplateRevenue.objects.filter(
        created_at__date=target_date,
        revenue_type='individual_purchase'
    )
    
    gross_revenue = template_sales.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    platform_share = template_sales.aggregate(total=Sum('platform_share'))['total'] or Decimal('0')
    
    return {
        'gross_revenue': gross_revenue,
        'net_revenue': platform_share,
        'transaction_count': template_sales.count(),
        'unique_customers': template_sales.values('user').distinct().count(),
        'metrics': {
            'average_template_price': float(gross_revenue / max(template_sales.count(), 1))
        }
    }


def _calculate_bundle_sales_revenue(target_date):
    """Calculate bundle sales revenue for a specific date"""
    # This would be implemented when bundle sales are tracked
    return {
        'gross_revenue': Decimal('0'),
        'net_revenue': Decimal('0'),
        'transaction_count': 0,
        'unique_customers': 0,
        'metrics': {}
    }


def _calculate_credit_purchases_revenue(target_date):
    """Calculate credit purchases revenue for a specific date"""
    # This would be implemented when credit purchases are tracked
    return {
        'gross_revenue': Decimal('0'),
        'net_revenue': Decimal('0'),
        'transaction_count': 0,
        'unique_customers': 0,
        'metrics': {}
    }


@shared_task(bind=True)
def send_subscription_reminders(self):
    """Send reminders for subscription expirations"""
    try:
        # Find subscriptions expiring in 3 days
        reminder_date = timezone.now() + timedelta(days=3)
        
        expiring_subscriptions = UserSubscription.objects.filter(
            status='active',
            expires_at__date=reminder_date.date(),
            auto_renew=False
        ).select_related('user', 'plan')
        
        reminders_sent = 0
        
        for subscription in expiring_subscriptions:
            try:
                # This would send email notification
                # For now, just log
                logger.info(f"Subscription reminder: {subscription.user.username} expires on {subscription.expires_at}")
                reminders_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending reminder for subscription {subscription.id}: {e}")
                continue
        
        return {
            'reminders_sent': reminders_sent,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in send_subscription_reminders: {e}")
        raise


@shared_task(bind=True)
def process_template_contribution_rewards(self):
    """Process rewards for users who contribute templates"""
    try:
        # Find recently published templates from extractions
        recent_extractions = ExtractedTemplate.objects.filter(
            status='approved',
            published_template__isnull=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('user', 'published_template')
        
        rewards_processed = 0
        total_credits_awarded = 0
        
        for extraction in recent_extractions:
            try:
                # Check if rewards already processed
                existing_reward = UserCredit.objects.filter(
                    user=extraction.user,
                    transaction_type='template_contribution',
                    reference_id=str(extraction.id)
                ).exists()
                
                if not existing_reward:
                    rewards = monetization_service.process_template_extraction_reward(extraction)
                    if rewards['credits_earned'] > 0:
                        total_credits_awarded += rewards['credits_earned']
                        rewards_processed += 1
                        
                        logger.info(f"Processed rewards for {extraction.user.username}: {rewards}")
                        
            except Exception as e:
                logger.error(f"Error processing rewards for extraction {extraction.id}: {e}")
                continue
        
        return {
            'rewards_processed': rewards_processed,
            'total_credits_awarded': total_credits_awarded,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in process_template_contribution_rewards: {e}")
        raise


@shared_task(bind=True)
def cleanup_expired_template_access(self):
    """Clean up expired template access records"""
    try:
        now = timezone.now()
        
        # Find expired access records
        expired_access = UserTemplateAccess.objects.filter(
            expires_at__lt=now,
            expires_at__isnull=False
        )
        
        deleted_count = expired_access.count()
        expired_access.delete()
        
        logger.info(f"Cleaned up {deleted_count} expired template access records")
        
        return {
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_template_access: {e}")
        raise