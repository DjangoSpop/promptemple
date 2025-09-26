# services/viral_marketing_service.py
import asyncio
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import requests
from celery import shared_task

@dataclass
class ViralEvent:
    user_id: str
    event_type: str
    data: Dict
    timestamp: datetime
    viral_score: int
    platform: str

@dataclass
class ViralTrigger:
    trigger_type: str
    threshold: float
    action: str
    template: str
    delay_minutes: int = 0

class ViralMarketingService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.viral_triggers = self._load_viral_triggers()
        self.social_templates = self._load_social_templates()
        
    def _load_viral_triggers(self) -> List[ViralTrigger]:
        """Load viral triggers configuration"""
        return [
            ViralTrigger(
                trigger_type='high_wow_score',
                threshold=8.0,
                action='prompt_share',
                template='high_wow_share',
                delay_minutes=2
            ),
            ViralTrigger(
                trigger_type='optimization_count',
                threshold=10,
                action='milestone_share',
                template='milestone_achievement',
                delay_minutes=0
            ),
            ViralTrigger(
                trigger_type='streak_achievement',
                threshold=7,
                action='streak_share',
                template='streak_celebration',
                delay_minutes=5
            ),
            ViralTrigger(
                trigger_type='level_up',
                threshold=1,
                action='level_share',
                template='level_up_celebration',
                delay_minutes=1
            ),
            ViralTrigger(
                trigger_type='first_optimization',
                threshold=1,
                action='welcome_share',
                template='first_time_success',
                delay_minutes=3
            )
        ]
    
    def _load_social_templates(self) -> Dict[str, Dict[str, str]]:
        """Load social sharing templates"""
        return {
            'high_wow_share': {
                'twitter': "Just got a {wow_score}/10 result optimizing my AI prompt with @PromptTemple! 🚀\n\nBEFORE: '{original_prompt}'\nAFTER: Professional-grade optimization\n\nMy AI responses are now 10x better! Try it: https://prompttemple.com/ref/{referral_code}",
                'linkedin': "Incredible! Just optimized my AI prompts and got {wow_score}/10 results with Prompt Temple. The transformation is remarkable - what used to be basic requests are now sophisticated, professional prompts that generate amazing AI responses.\n\nIf you're using AI tools, this is a game-changer for productivity: https://prompttemple.com",
                'copy': "Check out this amazing AI prompt optimizer! I just got {wow_score}/10 results - my prompts went from basic to professional-grade instantly. https://prompttemple.com/extension"
            },
            'milestone_achievement': {
                'twitter': "🎉 Just hit {count} optimized prompts with @PromptTemple! Each one gets better AI results than the last. The compound effect is incredible! #AIProductivity https://prompttemple.com",
                'linkedin': "Milestone achieved: {count} AI prompts optimized! The productivity gains from better prompt engineering are remarkable. Every interaction with AI tools is now more effective and professional.",
                'copy': "Hit {count} optimized prompts! The productivity boost is incredible. https://prompttemple.com"
            },
            'streak_celebration': {
                'twitter': "🔥 {streak_days} day streak with @PromptTemple! Consistently getting better AI results daily. The habit of good prompt engineering is paying off big time! https://prompttemple.com",
                'linkedin': "Celebrating a {streak_days}-day streak of optimizing my AI prompts! The consistency is building incredible momentum in my productivity workflow.",
                'copy': "{streak_days} days straight of better AI prompts! The momentum is building. https://prompttemple.com"
            },
            'level_up_celebration': {
                'twitter': "🏆 Level {level} achieved with @PromptTemple! Each level unlock brings better optimization techniques. The gamification makes improving AI prompts actually fun! https://prompttemple.com",
                'linkedin': "Just reached Level {level} in prompt optimization! The structured progression and achievement system makes mastering AI prompts engaging and rewarding.",
                'copy': "Level {level} unlocked! The gamified approach to prompt engineering is brilliant. https://prompttemple.com"
            },
            'first_time_success': {
                'twitter': "Mind blown! 🤯 Just tried @PromptTemple and my basic '{original_prompt}' became a professional-grade prompt instantly. The difference in AI responses is night and day! https://prompttemple.com",
                'linkedin': "Just discovered Prompt Temple and the results are astounding. My simple prompts are now sophisticated, professional requests that generate significantly better AI responses. This is the future of AI interaction.",
                'copy': "Just discovered this AI prompt optimizer - the results are incredible! My basic prompts became professional-grade instantly. https://prompttemple.com"
            }
        }
    
    async def track_viral_event(self, event: ViralEvent) -> None:
        """Track and process viral events"""
        # Store event in Redis for real-time processing
        event_key = f"viral_event:{event.user_id}:{event.timestamp.timestamp()}"
        event_data = {
            'user_id': event.user_id,
            'event_type': event.event_type,
            'data': event.data,
            'timestamp': event.timestamp.isoformat(),
            'viral_score': event.viral_score,
            'platform': event.platform
        }
        
        await self.redis_client.setex(
            event_key, 
            timedelta(days=7).total_seconds(),
            json.dumps(event_data)
        )
        
        # Check for viral triggers
        await self._check_viral_triggers(event)
        
        # Update viral metrics
        await self._update_viral_metrics(event)
        
        # Log for analytics
        await self._log_viral_analytics(event)
    
    async def _check_viral_triggers(self, event: ViralEvent) -> None:
        """Check if event triggers viral actions"""
        for trigger in self.viral_triggers:
            if await self._evaluate_trigger(trigger, event):
                await self._execute_viral_action(trigger, event)
    
    async def _evaluate_trigger(self, trigger: ViralTrigger, event: ViralEvent) -> bool:
        """Evaluate if trigger conditions are met"""
        if trigger.trigger_type == 'high_wow_score':
            return event.event_type == 'optimization_complete' and \
                   event.data.get('wow_score', 0) >= trigger.threshold
                   
        elif trigger.trigger_type == 'optimization_count':
            user_count = await self._get_user_optimization_count(event.user_id)
            return user_count >= trigger.threshold and user_count % 10 == 0
            
        elif trigger.trigger_type == 'streak_achievement':
            return event.event_type == 'daily_streak' and \
                   event.data.get('streak_days', 0) >= trigger.threshold
                   
        elif trigger.trigger_type == 'level_up':
            return event.event_type == 'level_up'
            
        elif trigger.trigger_type == 'first_optimization':
            user_count = await self._get_user_optimization_count(event.user_id)
            return user_count == 1
            
        return False
    
    async def _execute_viral_action(self, trigger: ViralTrigger, event: ViralEvent) -> None:
        """Execute viral action based on trigger"""
        if trigger.delay_minutes > 0:
            # Schedule delayed action
            schedule_viral_action.apply_async(
                args=[trigger.action, trigger.template, event.user_id, event.data],
                countdown=trigger.delay_minutes * 60
            )
        else:
            # Execute immediately
            await self._perform_viral_action(
                trigger.action, 
                trigger.template, 
                event.user_id, 
                event.data
            )
    
    async def _perform_viral_action(
        self, 
        action: str, 
        template: str, 
        user_id: str, 
        data: Dict
    ) -> None:
        """Perform the actual viral action"""
        if action == 'prompt_share':
            await self._show_share_suggestion(user_id, template, data)
        elif action == 'milestone_share':
            await self._show_milestone_celebration(user_id, template, data)
        elif action == 'streak_share':
            await self._show_streak_celebration(user_id, template, data)
        elif action == 'level_share':
            await self._show_level_celebration(user_id, template, data)
        elif action == 'welcome_share':
            await self._show_welcome_share(user_id, template, data)
    
    async def _show_share_suggestion(self, user_id: str, template: str, data: Dict) -> None:
        """Show share suggestion to user"""
        user_data = await self._get_user_data(user_id)
        share_content = self._generate_share_content(template, {**data, **user_data})
        
        # Send real-time notification to user
        notification = {
            'type': 'viral_share_suggestion',
            'title': f'🔥 Amazing {data.get("wow_score", 0)}/10 Result!',
            'message': 'Your optimization is incredible! Share it with your network?',
            'share_content': share_content,
            'show_referral_bonus': True,
            'urgency': 'high'
        }
        
        await self._send_realtime_notification(user_id, notification)
        
        # Track suggestion shown
        await self._track_viral_metric('share_suggestion_shown', user_id, data)
    
    def _generate_share_content(self, template: str, data: Dict) -> Dict[str, str]:
        """Generate platform-specific share content"""
        templates = self.social_templates.get(template, {})
        share_content = {}
        
        for platform, template_text in templates.items():
            try:
                share_content[platform] = template_text.format(**data)
            except KeyError as e:
                # Fallback to basic template if data missing
                share_content[platform] = f"Check out this amazing AI prompt optimization result! https://prompttemple.com"
        
        return share_content
    
    async def _get_user_optimization_count(self, user_id: str) -> int:
        """Get user's total optimization count"""
        # This would query the database
        from ..models import OptimizationHistory
        return await OptimizationHistory.objects.filter(user_id=user_id).acount()
    
    async def _get_user_data(self, user_id: str) -> Dict:
        """Get user data for personalization"""
        from django.contrib.auth.models import User
        from ..models import UserProfile
        
        user = await User.objects.aget(id=user_id)
        profile = await UserProfile.objects.aget(user=user)
        
        return {
            'username': user.username,
            'level': profile.level,
            'total_optimizations': profile.total_optimizations,
            'referral_code': profile.referral_code or 'SHARE123',
            'streak_days': profile.streak_days
        }
    
    async def _send_realtime_notification(self, user_id: str, notification: Dict) -> None:
        """Send real-time notification via WebSocket"""
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'viral_notification',
                'notification': notification
            }
        )
    
    async def _update_viral_metrics(self, event: ViralEvent) -> None:
        """Update viral metrics in Redis"""
        metrics_key = f"viral_metrics:{datetime.now().strftime('%Y-%m-%d')}"
        
        # Update daily viral events count
        await self.redis_client.hincrby(metrics_key, f"events_{event.event_type}", 1)
        await self.redis_client.hincrby(metrics_key, f"platform_{event.platform}", 1)
        await self.redis_client.hincrby(metrics_key, "total_viral_score", event.viral_score)
        
        # Set expiry for metrics (30 days)
        await self.redis_client.expire(metrics_key, timedelta(days=30).total_seconds())
    
    async def _track_viral_metric(self, metric_name: str, user_id: str, data: Dict) -> None:
        """Track specific viral metrics"""
        metric_data = {
            'metric': metric_name,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Store in Redis for real-time analytics
        metric_key = f"viral_metric:{metric_name}:{datetime.now().timestamp()}"
        await self.redis_client.setex(
            metric_key,
            timedelta(hours=24).total_seconds(),
            json.dumps(metric_data)
        )

# Celery tasks for asynchronous viral processing
@shared_task
def schedule_viral_action(action: str, template: str, user_id: str, data: Dict):
    """Celery task for delayed viral actions"""
    viral_service = ViralMarketingService()
    asyncio.run(viral_service._perform_viral_action(action, template, user_id, data))

@shared_task  
def process_viral_analytics():
    """Process viral analytics data"""
    viral_service = ViralMarketingService()
    asyncio.run(viral_service._process_daily_analytics())

# Viral Analytics Dashboard Service
class ViralAnalyticsService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
    
    async def get_viral_dashboard_data(self, days: int = 7) -> Dict:
        """Get viral marketing dashboard data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        dashboard_data = {
            'viral_coefficient': await self._calculate_viral_coefficient(start_date, end_date),
            'share_metrics': await self._get_share_metrics(start_date, end_date),
            'top_viral_content': await self._get_top_viral_content(start_date, end_date),
            'user_engagement': await self._get_viral_engagement_metrics(start_date, end_date),
            'platform_performance': await self._get_platform_performance(start_date, end_date),
            'conversion_funnel': await self._get_viral_conversion_funnel(start_date, end_date),
            'trending_hashtags': await self._get_trending_hashtags(),
            'referral_performance': await self._get_referral_performance(start_date, end_date)
        }
        
        return dashboard_data
    
    async def _calculate_viral_coefficient(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate viral coefficient (invites sent / users acquired)"""
        # Query database for viral metrics
        from ..models import ViralShare, User
        
        period_users = await User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).acount()
        
        period_shares = await ViralShare.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).acount()
        
        return period_shares / max(period_users, 1)
    
    async def _get_share_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get detailed sharing metrics"""
        metrics = {}
        
        # Get platform-wise sharing data
        platforms = ['twitter', 'linkedin', 'copy', 'email']
        for platform in platforms:
            metrics[platform] = await self._get_platform_shares(platform, start_date, end_date)
        
        # Get sharing triggers performance
        triggers = ['high_wow_score', 'milestone_achievement', 'streak_celebration']
        metrics['triggers'] = {}
        for trigger in triggers:
            metrics['triggers'][trigger] = await self._get_trigger_performance(trigger, start_date, end_date)
        
        return metrics
    
    async def _get_top_viral_content(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get top performing viral content"""
        # Query most shared optimizations
        from ..models import OptimizationHistory, ViralShare
        
        top_content = []
        
        # Get optimizations with most shares
        optimizations = await OptimizationHistory.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            wow_factor_score__gte=8
        ).values(
            'id', 'original_prompt', 'optimized_prompt', 'wow_factor_score'
        ).order_by('-wow_factor_score')[:10]
        
        for opt in optimizations:
            share_count = await ViralShare.objects.filter(
                optimization_id=opt['id']
            ).acount()
            
            top_content.append({
                'optimization_id': opt['id'],
                'original_prompt': opt['original_prompt'][:100] + '...',
                'wow_score': opt['wow_factor_score'],
                'share_count': share_count,
                'viral_score': share_count * opt['wow_factor_score']
            })
        
        return sorted(top_content, key=lambda x: x['viral_score'], reverse=True)
    
    async def _get_viral_engagement_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get user engagement with viral features"""
        return {
            'share_suggestion_ctr': await self._calculate_share_suggestion_ctr(start_date, end_date),
            'referral_conversion_rate': await self._calculate_referral_conversion_rate(start_date, end_date),
            'viral_user_retention': await self._calculate_viral_user_retention(start_date, end_date),
            'avg_shares_per_user': await self._calculate_avg_shares_per_user(start_date, end_date),
            'viral_session_length': await self._calculate_viral_session_length(start_date, end_date)
        }
    
    async def track_share_event(
        self, 
        user_id: str, 
        platform: str, 
        content_type: str, 
        optimization_id: str = None
    ) -> None:
        """Track when user shares content"""
        from ..models import ViralShare
        
        await ViralShare.objects.acreate(
            user_id=user_id,
            platform=platform,
            content_type=content_type,
            optimization_id=optimization_id,
            created_at=datetime.now()
        )
        
        # Update real-time metrics
        await self._update_realtime_share_metrics(platform, content_type)
        
        # Trigger viral bonuses
        await self._trigger_viral_bonuses(user_id, platform)
    
    async def _trigger_viral_bonuses(self, user_id: str, platform: str) -> None:
        """Trigger bonuses for viral sharing"""
        from ..models import UserProfile, CreditTransaction
        
        # Award sharing credits
        sharing_credits = {
            'twitter': 25,
            'linkedin': 35,
            'copy': 15,
            'email': 20
        }
        
        credits = sharing_credits.get(platform, 10)
        
        profile = await UserProfile.objects.aget(user_id=user_id)
        profile.credits += credits
        await profile.asave()
        
        # Create transaction record
        await CreditTransaction.objects.acreate(
            user_id=user_id,
            amount=credits,
            transaction_type='earned',
            reason=f'Shared on {platform}'
        )
        
        # Check for viral achievements
        await self._check_viral_achievements(user_id)

# A/B Testing Service for Viral Features
class ViralABTestingService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.active_tests = self._load_active_tests()
    
    def _load_active_tests(self) -> List[Dict]:
        """Load active A/B tests for viral features"""
        return [
            {
                'test_id': 'share_button_text',
                'variants': {
                    'A': 'Share This Result',
                    'B': 'Show Off This WOW Result! 🔥',
                    'C': 'This Result is Share-Worthy!'
                },
                'traffic_split': [33, 33, 34],
                'success_metric': 'share_click_rate'
            },
            {
                'test_id': 'viral_notification_timing',
                'variants': {
                    'A': 0,    # Immediate
                    'B': 120,  # 2 minutes
                    'C': 300   # 5 minutes
                },
                'traffic_split': [33, 33, 34],
                'success_metric': 'share_completion_rate'
            },
            {
                'test_id': 'referral_incentive',
                'variants': {
                    'A': 25,   # 25 credits per referral
                    'B': 50,   # 50 credits per referral
                    'C': 100   # 100 credits per referral
                },
                'traffic_split': [33, 33, 34],
                'success_metric': 'referral_conversion_rate'
            }
        ]
    
    async def get_variant_for_user(self, test_id: str, user_id: str) -> str:
        """Get A/B test variant for user"""
        # Use consistent hash to assign users to variants
        import hashlib
        
        test = next((t for t in self.active_tests if t['test_id'] == test_id), None)
        if not test:
            return 'A'  # Default variant
        
        # Create consistent hash for user+test
        hash_input = f"{user_id}:{test_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Assign variant based on traffic split
        cumulative = 0
        for i, (variant, split) in enumerate(zip(test['variants'].keys(), test['traffic_split'])):
            cumulative += split
            if (hash_value % 100) < cumulative:
                return variant
        
        return 'A'  # Fallback
    
    async def track_test_event(
        self, 
        test_id: str, 
        user_id: str, 
        variant: str, 
        event_type: str, 
        value: float = 1.0
    ) -> None:
        """Track A/B test events"""
        event_data = {
            'test_id': test_id,
            'user_id': user_id,
            'variant': variant,
            'event_type': event_type,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in Redis for real-time analysis
        key = f"ab_test:{test_id}:{variant}:{event_type}"
        await self.redis_client.lpush(key, json.dumps(event_data))
        await self.redis_client.expire(key, timedelta(days=30).total_seconds())
    
    async def get_test_results(self, test_id: str) -> Dict:
        """Get A/B test results and statistical significance"""
        test = next((t for t in self.active_tests if t['test_id'] == test_id), None)
        if not test:
            return {}
        
        results = {}
        
        for variant in test['variants'].keys():
            variant_data = await self._get_variant_metrics(test_id, variant, test['success_metric'])
            results[variant] = variant_data
        
        # Calculate statistical significance
        results['statistical_significance'] = await self._calculate_significance(results)
        results['winning_variant'] = await self._determine_winning_variant(results)
        
        return results

# Real-time Viral Notifications via WebSocket
# consumers.py (add to existing consumers)
class ViralNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.room_group_name = f'viral_notifications_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def viral_notification(self, event):
        """Send viral notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'viral_notification',
            'notification': event['notification']
        }))
    
    async def receive(self, text_data):
        """Handle viral notification interactions"""
        data = json.loads(text_data)
        
        if data['action'] == 'share_clicked':
            await self._handle_share_clicked(data)
        elif data['action'] == 'dismiss_notification':
            await self._handle_notification_dismissed(data)
    
    async def _handle_share_clicked(self, data):
        """Handle when user clicks share from notification"""
        viral_service = ViralAnalyticsService()
        await viral_service.track_share_event(
            user_id=str(self.user_id),
            platform=data['platform'],
            content_type='viral_notification',
            optimization_id=data.get('optimization_id')
        )

# API Views for Viral Features
# views/viral_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def track_viral_share(request):
    """Track viral sharing events"""
    data = request.data
    user = request.user
    
    viral_service = ViralAnalyticsService()
    await viral_service.track_share_event(
        user_id=str(user.id),
        platform=data['platform'],
        content_type=data['content_type'],
        optimization_id=data.get('optimization_id')
    )
    
    return Response({'success': True, 'credits_earned': 25})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_viral_suggestions(request):
    """Get personalized viral sharing suggestions"""
    user = request.user
    
    # Get user's recent high-scoring optimizations
    recent_optimizations = await OptimizationHistory.objects.filter(
        user=user,
        wow_factor_score__gte=8,
        created_at__gte=datetime.now() - timedelta(days=7)
    ).order_by('-created_at')[:3]
    
    suggestions = []
    for opt in recent_optimizations:
        viral_service = ViralMarketingService()
        share_content = viral_service._generate_share_content('high_wow_share', {
            'wow_score': opt.wow_factor_score,
            'original_prompt': opt.original_prompt[:50] + '...',
            'referral_code': user.profile.referral_code
        })
        
        suggestions.append({
            'optimization_id': str(opt.id),
            'wow_score': opt.wow_factor_score,
            'share_content': share_content,
            'potential_viral_score': opt.wow_factor_score * 10
        })
    
    return Response({'suggestions': suggestions})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_viral_dashboard(request):
    """Get viral marketing dashboard for admin users"""
    if not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=403)
    
    days = int(request.GET.get('days', 7))
    
    viral_analytics = ViralAnalyticsService()
    dashboard_data = await viral_analytics.get_viral_dashboard_data(days)
    
    return Response(dashboard_data)