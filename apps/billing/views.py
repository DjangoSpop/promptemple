import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def _get_billing_models():
    """Lazy import billing models — returns (SubscriptionPlan, UserSubscription, UsageQuota) or Nones."""
    try:
        from apps.billing.models import SubscriptionPlan, UserSubscription, UsageQuota
        return SubscriptionPlan, UserSubscription, UsageQuota
    except ImportError:
        return None, None, None


def _serialise_plan(plan) -> dict:
    features = getattr(plan, 'features_list', []) or getattr(plan, 'features', []) or []
    return {
        'id': str(plan.pk),
        'name': getattr(plan, 'name', ''),
        'plan_type': getattr(plan, 'plan_type', 'free'),
        'description': getattr(plan, 'description', ''),
        'price': str(getattr(plan, 'price', '0.00')),
        'price_monthly': str(getattr(plan, 'price', '0.00')),
        'billing_interval': getattr(plan, 'billing_interval', 'monthly'),
        'currency': getattr(plan, 'currency', 'USD'),
        'features': features if isinstance(features, list) else [],
        'limits': {
            'daily_template_limit': getattr(plan, 'daily_template_limit', 5),
            'daily_copy_limit': getattr(plan, 'daily_copy_limit', 3),
        },
        'perks': {
            'premium_templates': getattr(plan, 'premium_templates_access', False),
            'ads_free': getattr(plan, 'ads_free', False),
            'priority_support': getattr(plan, 'priority_support', False),
            'analytics': getattr(plan, 'analytics_access', False),
            'api_access': getattr(plan, 'api_access', False),
            'collaboration': getattr(plan, 'collaboration_features', False),
        },
        'is_active': getattr(plan, 'is_active', True),
        'is_popular': getattr(plan, 'is_popular', False),
        'stripe_price_id': getattr(plan, 'stripe_price_id', ''),
    }


def _serialise_subscription(sub) -> dict:
    if sub is None:
        return {
            'plan': 'free',
            'status': 'active',
            'is_active': True,
            'trial_end': None,
            'current_period_end': None,
            'cancel_at_period_end': False,
        }
    return {
        'id': sub.pk,
        'plan': _serialise_plan(sub.plan) if hasattr(sub, 'plan') and sub.plan else {'name': 'free'},
        'status': getattr(sub, 'status', 'active'),
        'is_active': getattr(sub, 'is_active', True),
        'trial_end': sub.trial_end.isoformat() if getattr(sub, 'trial_end', None) else None,
        'current_period_end': sub.current_period_end.isoformat() if getattr(sub, 'current_period_end', None) else None,
        'cancel_at_period_end': getattr(sub, 'cancel_at_period_end', False),
        'stripe_customer_id': getattr(sub, 'stripe_customer_id', ''),
        'stripe_subscription_id': getattr(sub, 'stripe_subscription_id', ''),
    }


class BillingPlanListView(APIView):
    """List all active billing plans."""
    permission_classes = [AllowAny]

    def get(self, request):
        SubscriptionPlan, _, _ = _get_billing_models()
        if not SubscriptionPlan:
            # Fallback: return sensible free-tier plan if model not available
            return Response({
                'plans': [
                    {
                        'id': 'free',
                        'name': 'free',
                        'display_name': 'Free',
                        'description': 'Get started with PromptTemple for free',
                        'price_monthly': '0.00',
                        'price_yearly': '0.00',
                        'currency': 'USD',
                        'features': ['5 AI requests/day', '10 templates', 'Basic analytics'],
                        'limits': {'max_templates': 10, 'ai_requests_per_day': 5, 'max_storage_mb': 100},
                        'is_active': True,
                        'is_popular': False,
                    }
                ]
            })

        try:
            plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
            return Response({'plans': [_serialise_plan(p) for p in plans]})
        except Exception as e:
            logger.error(f"BillingPlanList error: {e}")
            return Response({'plans': []})


class BillingPlanDetailView(APIView):
    """Get details of a specific billing plan."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        SubscriptionPlan, _, _ = _get_billing_models()
        if not SubscriptionPlan:
            return Response({'error': 'Billing not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            plan = SubscriptionPlan.objects.get(pk=pk, is_active=True)
            return Response({'plan': _serialise_plan(plan)})
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"BillingPlanDetail error: {e}")
            return Response({'error': 'Internal error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSubscriptionView(APIView):
    """Get the authenticated user's current subscription."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, UserSubscription, _ = _get_billing_models()
        if not UserSubscription:
            return Response({'subscription': _serialise_subscription(None)})

        try:
            sub = UserSubscription.objects.filter(user=request.user).select_related('plan').first()
            return Response({'subscription': _serialise_subscription(sub)})
        except Exception as e:
            logger.error(f"UserSubscription error: {e}")
            return Response({'subscription': _serialise_subscription(None)})


class UserEntitlementsView(APIView):
    """Return the user's entitlements based on their subscription plan."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, UserSubscription, _ = _get_billing_models()
        user = request.user

        # Defaults (free tier)
        entitlements = {
            'daily_template_limit': 5,
            'daily_copy_limit': 3,
            'premium_templates': False,
            'ads_free': False,
            'priority_support': False,
            'analytics': False,
            'api_access': False,
            'collaboration': False,
            'plan_name': 'free',
            'plan_type': 'free',
        }

        if UserSubscription:
            try:
                sub = UserSubscription.objects.filter(
                    user=user, status__in=['active', 'trialing']
                ).select_related('plan').first()
                if sub and sub.plan:
                    plan = sub.plan
                    entitlements.update({
                        'daily_template_limit': getattr(plan, 'daily_template_limit', 5),
                        'daily_copy_limit': getattr(plan, 'daily_copy_limit', 3),
                        'premium_templates': getattr(plan, 'premium_templates_access', False),
                        'ads_free': getattr(plan, 'ads_free', False),
                        'priority_support': getattr(plan, 'priority_support', False),
                        'analytics': getattr(plan, 'analytics_access', False),
                        'api_access': getattr(plan, 'api_access', False),
                        'collaboration': getattr(plan, 'collaboration_features', False),
                        'plan_name': getattr(plan, 'name', 'free'),
                        'plan_type': getattr(plan, 'plan_type', 'free'),
                    })
            except Exception as e:
                logger.error(f"UserEntitlements error: {e}")

        return Response({'entitlements': entitlements})


class UserUsageView(APIView):
    """Get the user's current AI usage against their quota."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Re-use the AIUsageQuota from billing or ai_services
        try:
            from apps.billing.models import UsageQuota
            quota, _ = UsageQuota.objects.get_or_create(user=request.user)
            today = timezone.now().date()
            # Reset daily counter if needed
            last_reset = getattr(quota, 'last_reset_date', None)
            if last_reset != today:
                quota.tokens_used_today = 0
                quota.last_reset_date = today
                quota.save(update_fields=['tokens_used_today', 'last_reset_date'])

            daily_limit = getattr(quota, 'daily_token_limit', 50000)
            monthly_limit = getattr(quota, 'monthly_token_limit', 1000000)
            used_today = getattr(quota, 'tokens_used_today', 0)
            used_monthly = getattr(quota, 'tokens_used_monthly', 0)

            return Response({
                'usage': {
                    'tokens_today': used_today,
                    'tokens_monthly': used_monthly,
                    'daily_limit': daily_limit,
                    'monthly_limit': monthly_limit,
                    'remaining_today': max(0, daily_limit - used_today),
                    'remaining_monthly': max(0, monthly_limit - used_monthly),
                    'cost_estimate_today': round(used_today * 0.0014 / 1000, 4),
                    'cost_estimate_monthly': round(used_monthly * 0.0014 / 1000, 4),
                    'reset_date': today.isoformat(),
                }
            })
        except Exception as e:
            logger.error(f"UserUsage billing error: {e}")
            # Try ai_services.AIUsageQuota as fallback
            try:
                from apps.ai_services.models import AIUsageQuota
                quota, _ = AIUsageQuota.objects.get_or_create(user=request.user)
                return Response({
                    'usage': {
                        'tokens_today': getattr(quota, 'tokens_used_today', 0),
                        'tokens_monthly': getattr(quota, 'tokens_used_monthly', 0),
                        'daily_limit': getattr(quota, 'daily_limit', 50000),
                        'monthly_limit': getattr(quota, 'monthly_limit', 1000000),
                        'remaining_today': max(0, getattr(quota, 'daily_limit', 50000) - getattr(quota, 'tokens_used_today', 0)),
                        'remaining_monthly': max(0, getattr(quota, 'monthly_limit', 1000000) - getattr(quota, 'tokens_used_monthly', 0)),
                    }
                })
            except Exception:
                return Response({'usage': {'tokens_today': 0, 'daily_limit': 50000, 'remaining_today': 50000}})


class CheckoutSessionView(APIView):
    """Create a Stripe checkout session (Stripe integration pending)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        billing_period = request.data.get('billing_period', 'monthly')  # monthly | yearly

        # Stripe not yet integrated — return informative response
        return Response(
            {
                'error': 'Stripe payment integration is not yet configured.',
                'message': 'Please contact support to upgrade your plan.',
                'plan_id': plan_id,
                'billing_period': billing_period,
                'checkout_url': '',
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class CustomerPortalView(APIView):
    """Create a Stripe customer portal session (Stripe integration pending)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {
                'error': 'Stripe billing portal is not yet configured.',
                'message': 'Please contact support for subscription management.',
                'portal_url': '',
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class StripeWebhookView(APIView):
    """Handle Stripe webhooks."""
    permission_classes = [AllowAny]

    def post(self, request):
        # Log the event type for monitoring; real processing requires Stripe SDK
        event_type = request.data.get('type', 'unknown')
        logger.info(f"Stripe webhook received: {event_type}")
        return Response({'status': 'ok', 'event_type': event_type})
