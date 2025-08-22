from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Billing plan endpoints
    path('plans/', views.BillingPlanListView.as_view(), name='plan-list'),
    path('plans/<int:pk>/', views.BillingPlanDetailView.as_view(), name='plan-detail'),
    
    # User subscription endpoints
    path('me/subscription/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('me/entitlements/', views.UserEntitlementsView.as_view(), name='user-entitlements'),
    path('me/usage/', views.UserUsageView.as_view(), name='user-usage'),
    
    # Stripe integration endpoints
    path('checkout/', views.CheckoutSessionView.as_view(), name='checkout'),
    path('portal/', views.CustomerPortalView.as_view(), name='customer-portal'),
    
    # Webhook endpoints
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
]
