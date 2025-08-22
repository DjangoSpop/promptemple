# enterprise/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True)
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
            ('enterprise_plus', 'Enterprise Plus'),
        ],
        default='starter'
    )
    monthly_credit_limit = models.IntegerField(default=10000)
    seat_limit = models.IntegerField(default=10)
    api_rate_limit = models.IntegerField(default=1000)  # requests per hour
    custom_branding = models.BooleanField(default=False)
    sso_enabled = models.BooleanField(default=False)
    advanced_analytics = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrganizationMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_teams')
    members = models.ManyToManyField(User, through='TeamMembership', related_name='teams')
    credit_allocation = models.IntegerField(default=1000)
    template_sharing = models.CharField(
        max_length=20,
        choices=[
            ('private', 'Private to Team'),
            ('organization', 'Organization Wide'),
            ('public', 'Public'),
        ],
        default='organization'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ('lead', 'Team Lead'),
            ('member', 'Member'),
            ('contributor', 'Contributor'),
        ],
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

class UsageAnalytics(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    
    # Usage metrics
    prompts_optimized = models.IntegerField(default=0)
    credits_used = models.IntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    templates_created = models.IntegerField(default=0)
    templates_used = models.IntegerField(default=0)
    
    # Quality metrics
    average_wow_score = models.FloatField(default=0.0)
    total_wow_score = models.IntegerField(default=0)
    high_quality_prompts = models.IntegerField(default=0)  # wow_score >= 8
    
    # Efficiency metrics
    average_processing_time = models.FloatField(default=0.0)
    user_satisfaction_score = models.FloatField(default=0.0)
    
    # Cost metrics
    estimated_ai_costs = models.FloatField(default=0.0)
    cost_per_optimization = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ('organization', 'user', 'team', 'date')

class TemplateLibrary(models.Model):
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('team', 'Team Only'),
        ('organization', 'Organization'),
        ('public', 'Public'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='organization')
    is_curated = models.BooleanField(default=False)
    curator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    templates = models.ManyToManyField('PromptTemplate', related_name='libraries')
    created_at = models.DateTimeField(auto_now_add=True)

class ComplianceLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

# enterprise/services/analytics_service.py
from django.db.models import Count, Avg, Sum, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from ..models import Organization, UsageAnalytics, OptimizationHistory

class EnterpriseAnalyticsService:
    def __init__(self, organization: Organization):
        self.organization = organization
    
    async def generate_executive_dashboard(self, date_range: int = 30) -> Dict:
        """Generate executive-level dashboard data"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=date_range)
        
        # High-level KPIs
        kpis = await self._calculate_executive_kpis(start_date, end_date)
        
        # Trend analysis
        trends = await self._analyze_trends(start_date, end_date)
        
        # Department performance
        department_metrics = await self._get_department_metrics(start_date, end_date)
        
        # ROI analysis
        roi_analysis = await self._calculate_roi_metrics(start_date, end_date)
        
        # Risk indicators
        risk_indicators = await self._assess_risk_indicators(start_date, end_date)
        
        return {
            'kpis': kpis,
            'trends': trends,
            'department_metrics': department_metrics,
            'roi_analysis': roi_analysis,
            'risk_indicators': risk_indicators,
            'generated_at': timezone.now().isoformat(),
            'date_range': {'start': start_date, 'end': end_date}
        }
    
    async def _calculate_executive_kpis(self, start_date, end_date) -> Dict:
        """Calculate high-level KPIs for executives"""
        analytics = UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        )
        
        total_usage = await analytics.aggregate(
            total_optimizations=Sum('prompts_optimized'),
            total_credits_used=Sum('credits_used'),
            total_api_calls=Sum('api_calls'),
            avg_quality=Avg('average_wow_score'),
            total_templates=Sum('templates_created')
        )
        
        active_users = await analytics.values('user').distinct().acount()
        total_members = await self.organization.members.filter(is_active=True).acount()
        
        # Calculate productivity metrics
        optimizations_per_user = (total_usage['total_optimizations'] or 0) / max(active_users, 1)
        adoption_rate = (active_users / max(total_members, 1)) * 100
        
        # Cost efficiency
        cost_per_optimization = (total_usage['total_credits_used'] or 0) / max(total_usage['total_optimizations'] or 1, 1)
        
        return {
            'total_optimizations': total_usage['total_optimizations'] or 0,
            'total_credits_used': total_usage['total_credits_used'] or 0,
            'active_users': active_users,
            'adoption_rate': round(adoption_rate, 2),
            'average_quality_score': round(total_usage['avg_quality'] or 0, 2),
            'optimizations_per_user': round(optimizations_per_user, 2),
            'cost_per_optimization': round(cost_per_optimization, 2),
            'total_api_calls': total_usage['total_api_calls'] or 0,
            'templates_created': total_usage['total_templates'] or 0
        }
    
    async def _analyze_trends(self, start_date, end_date) -> Dict:
        """Analyze usage trends over time"""
        daily_analytics = UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).values('date').annotate(
            daily_optimizations=Sum('prompts_optimized'),
            daily_credits=Sum('credits_used'),
            daily_quality=Avg('average_wow_score'),
            active_users=Count('user', distinct=True)
        ).order_by('date')
        
        trends_data = []
        async for day in daily_analytics:
            trends_data.append({
                'date': day['date'].isoformat(),
                'optimizations': day['daily_optimizations'] or 0,
                'credits_used': day['daily_credits'] or 0,
                'quality_score': round(day['daily_quality'] or 0, 2),
                'active_users': day['active_users']
            })
        
        # Calculate growth rates
        if len(trends_data) >= 2:
            first_week = trends_data[:7]
            last_week = trends_data[-7:]
            
            first_week_avg = sum(d['optimizations'] for d in first_week) / len(first_week)
            last_week_avg = sum(d['optimizations'] for d in last_week) / len(last_week)
            
            growth_rate = ((last_week_avg - first_week_avg) / max(first_week_avg, 1)) * 100
        else:
            growth_rate = 0
        
        return {
            'daily_data': trends_data,
            'growth_rate': round(growth_rate, 2),
            'trend_direction': 'up' if growth_rate > 5 else 'down' if growth_rate < -5 else 'stable'
        }
    
    async def _get_department_metrics(self, start_date, end_date) -> List[Dict]:
        """Get performance metrics by department"""
        department_data = UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date,
            user__organizationmember__organization=self.organization
        ).values(
            'user__organizationmember__department'
        ).annotate(
            total_optimizations=Sum('prompts_optimized'),
            total_credits=Sum('credits_used'),
            avg_quality=Avg('average_wow_score'),
            user_count=Count('user', distinct=True)
        ).filter(user__organizationmember__department__isnull=False)
        
        departments = []
        async for dept in department_data:
            department_name = dept['user__organizationmember__department']
            if department_name:
                departments.append({
                    'name': department_name,
                    'total_optimizations': dept['total_optimizations'] or 0,
                    'total_credits': dept['total_credits'] or 0,
                    'average_quality': round(dept['avg_quality'] or 0, 2),
                    'active_users': dept['user_count'],
                    'optimizations_per_user': round((dept['total_optimizations'] or 0) / max(dept['user_count'], 1), 2),
                    'efficiency_score': round(((dept['avg_quality'] or 0) * (dept['total_optimizations'] or 0)) / max(dept['total_credits'] or 1, 1), 2)
                })
        
        return sorted(departments, key=lambda x: x['efficiency_score'], reverse=True)
    
    async def _calculate_roi_metrics(self, start_date, end_date) -> Dict:
        """Calculate return on investment metrics"""
        total_credits_used = await UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('credits_used'))['total'] or 0
        
        # Estimate cost savings (assuming each optimization saves 30 minutes at $50/hour)
        total_optimizations = await UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('prompts_optimized'))['total'] or 0
        
        estimated_time_saved_hours = total_optimizations * 0.5  # 30 minutes per optimization
        estimated_cost_savings = estimated_time_saved_hours * 50  # $50/hour
        
        # Calculate subscription cost (simplified)
        plan_costs = {
            'starter': 99,
            'professional': 299,
            'enterprise': 999,
            'enterprise_plus': 2999
        }
        monthly_cost = plan_costs.get(self.organization.plan_type, 299)
        period_cost = monthly_cost * (date_range / 30)
        
        roi_percentage = ((estimated_cost_savings - period_cost) / max(period_cost, 1)) * 100
        
        return {
            'total_optimizations': total_optimizations,
            'estimated_time_saved_hours': round(estimated_time_saved_hours, 1),
            'estimated_cost_savings': round(estimated_cost_savings, 2),
            'subscription_cost': round(period_cost, 2),
            'roi_percentage': round(roi_percentage, 2),
            'payback_period_days': round((period_cost / max(estimated_cost_savings / (date_range or 30), 1)) * 30, 1) if estimated_cost_savings > 0 else 0
        }
    
    async def _assess_risk_indicators(self, start_date, end_date) -> Dict:
        """Assess risk indicators for the organization"""
        # Usage risk indicators
        current_credits = await UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=Sum('credits_used'))['total'] or 0
        
        credit_utilization = (current_credits / max(self.organization.monthly_credit_limit, 1)) * 100
        
        # Quality risk indicators
        avg_quality = await UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(avg=Avg('average_wow_score'))['avg'] or 0
        
        # Adoption risk indicators
        active_users = await UsageAnalytics.objects.filter(
            organization=self.organization,
            date__gte=start_date,
            date__lte=end_date
        ).values('user').distinct().acount()
        
        total_seats = await self.organization.members.filter(is_active=True).acount()
        adoption_rate = (active_users / max(total_seats, 1)) * 100
        
        risks = []
        risk_level = 'low'
        
        if credit_utilization > 90:
            risks.append('Credit limit approaching - consider upgrading plan')
            risk_level = 'high'
        elif credit_utilization > 75:
            risks.append('High credit usage - monitor consumption')
            risk_level = 'medium'
        
        if avg_quality < 6.0:
            risks.append('Low average quality scores - training recommended')
            risk_level = 'high'
        elif avg_quality < 7.0:
            risks.append('Quality scores below optimal - consider best practices training')
            if risk_level == 'low':
                risk_level = 'medium'
        
        if adoption_rate < 30:
            risks.append('Low adoption rate - change management needed')
            risk_level = 'high'
        elif adoption_rate < 60:
            risks.append('Moderate adoption - consider user training programs')
            if risk_level == 'low':
                risk_level = 'medium'
        
        return {
            'overall_risk_level': risk_level,
            'risk_indicators': risks,
            'credit_utilization': round(credit_utilization, 1),
            'quality_score': round(avg_quality, 2),
            'adoption_rate': round(adoption_rate, 1),
            'recommendations': self._generate_recommendations(risks, credit_utilization, avg_quality, adoption_rate)
        }
    
    def _generate_recommendations(self, risks, credit_util, quality, adoption) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        if credit_util > 80:
            recommendations.append("Consider upgrading to a higher plan or implementing usage quotas")
        
        if quality < 7.0:
            recommendations.append("Implement prompt engineering training program for users")
            recommendations.append("Create template library with high-quality examples")
        
        if adoption < 50:
            recommendations.append("Launch user onboarding and training initiative")
            recommendations.append("Identify and support power users as champions")
            recommendations.append("Integrate tool into existing workflows")
        
        if not risks:
            recommendations.append("Performance is strong - consider expanding use cases")
            recommendations.append("Share success stories across the organization")
        
        return recommendations

# enterprise/services/team_management_service.py
class TeamManagementService:
    def __init__(self, organization: Organization):
        self.organization = organization
    
    async def create_team_dashboard(self, team_id: str, date_range: int = 30) -> Dict:
        """Create comprehensive team dashboard"""
        try:
            team = await Team.objects.aget(id=team_id, organization=self.organization)
        except Team.DoesNotExist:
            raise ValueError("Team not found")
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=date_range)
        
        # Team performance metrics
        team_metrics = await self._get_team_performance(team, start_date, end_date)
        
        # Individual member performance
        member_performance = await self._get_member_performance(team, start_date, end_date)
        
        # Template sharing metrics
        template_metrics = await self._get_template_sharing_metrics(team, start_date, end_date)
        
        # Collaboration insights
        collaboration_data = await self._analyze_team_collaboration(team, start_date, end_date)
        
        return {
            'team_info': {
                'id': str(team.id),
                'name': team.name,
                'member_count': await team.members.acount(),
                'credit_allocation': team.credit_allocation,
                'lead': team.lead.username if team.lead else None
            },
            'performance_metrics': team_metrics,
            'member_performance': member_performance,
            'template_metrics': template_metrics,
            'collaboration_insights': collaboration_data,
            'recommendations': await self._generate_team_recommendations(team, team_metrics)
        }
    
    async def _get_team_performance(self, team: Team, start_date, end_date) -> Dict:
        """Get overall team performance metrics"""
        team_analytics = UsageAnalytics.objects.filter(
            team=team,
            date__gte=start_date,
            date__lte=end_date
        )
        
        performance = await team_analytics.aggregate(
            total_optimizations=Sum('prompts_optimized'),
            total_credits=Sum('credits_used'),
            avg_quality=Avg('average_wow_score'),
            total_templates=Sum('templates_created'),
            avg_processing_time=Avg('average_processing_time')
        )
        
        # Calculate team efficiency metrics
        credit_efficiency = (performance['total_optimizations'] or 0) / max(performance['total_credits'] or 1, 1)
        quality_consistency = await self._calculate_quality_consistency(team_analytics)
        
        return {
            'total_optimizations': performance['total_optimizations'] or 0,
            'credits_used': performance['total_credits'] or 0,
            'credit_utilization': round(((performance['total_credits'] or 0) / team.credit_allocation) * 100, 1),
            'average_quality': round(performance['avg_quality'] or 0, 2),
            'quality_consistency': round(quality_consistency, 2),
            'templates_created': performance['total_templates'] or 0,
            'credit_efficiency': round(credit_efficiency, 3),
            'avg_processing_time': round(performance['avg_processing_time'] or 0, 2)
        }
    
    async def _get_member_performance(self, team: Team, start_date, end_date) -> List[Dict]:
        """Get individual member performance within the team"""
        member_data = UsageAnalytics.objects.filter(
            team=team,
            date__gte=start_date,
            date__lte=end_date
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            optimizations=Sum('prompts_optimized'),
            credits_used=Sum('credits_used'),
            avg_quality=Avg('average_wow_score'),
            templates_created=Sum('templates_created'),
            days_active=Count('date', distinct=True)
        )
        
        members = []
        async for member in member_data:
            efficiency = (member['optimizations'] or 0) / max(member['credits_used'] or 1, 1)
            activity_rate = (member['days_active'] / (end_date - start_date).days) * 100
            
            members.append({
                'username': member['user__username'],
                'name': f"{member['user__first_name']} {member['user__last_name']}".strip(),
                'optimizations': member['optimizations'] or 0,
                'credits_used': member['credits_used'] or 0,
                'average_quality': round(member['avg_quality'] or 0, 2),
                'templates_created': member['templates_created'] or 0,
                'efficiency_score': round(efficiency, 3),
                'activity_rate': round(activity_rate, 1),
                'days_active': member['days_active']
            })
        
        return sorted(members, key=lambda x: x['efficiency_score'], reverse=True)
    
    async def _calculate_quality_consistency(self, analytics_queryset) -> float:
        """Calculate how consistent the team's quality scores are"""
        quality_scores = []
        async for analytics in analytics_queryset:
            if analytics.average_wow_score > 0:
                quality_scores.append(analytics.average_wow_score)
        
        if len(quality_scores) < 2:
            return 1.0
        
        import statistics
        mean_quality = statistics.mean(quality_scores)
        std_dev = statistics.stdev(quality_scores)
        
        # Consistency score: higher is more consistent (lower standard deviation)
        consistency = max(0, 1 - (std_dev / mean_quality)) if mean_quality > 0 else 0
        return consistency

# enterprise/api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .services.analytics_service import EnterpriseAnalyticsService
from .services.team_management_service import TeamManagementService

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def enterprise_dashboard(request):
    """Get enterprise-level dashboard data"""
    try:
        org_member = await OrganizationMember.objects.select_related('organization').aget(
            user=request.user,
            role__in=['owner', 'admin']
        )
        
        date_range = int(request.GET.get('days', 30))
        analytics_service = EnterpriseAnalyticsService(org_member.organization)
        
        dashboard_data = await analytics_service.generate_executive_dashboard(date_range)
        
        return Response(dashboard_data)
        
    except OrganizationMember.DoesNotExist:
        return Response(
            {'error': 'Access denied. Admin role required.'}, 
            status=status.HTTP_403_FORBIDDEN
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def team_dashboard(request, team_id):
    """Get team-specific dashboard data"""
    try:
        org_member = await OrganizationMember.objects.select_related('organization').aget(
            user=request.user
        )
        
        # Check if user has access to this team
        team = get_object_or_404(Team, id=team_id, organization=org_member.organization)
        
        # Check permissions
        if (org_member.role not in ['owner', 'admin'] and 
            not await team.members.filter(id=request.user.id).aexists()):
            return Response(
                {'error': 'Access denied to this team.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        date_range = int(request.GET.get('days', 30))
        team_service = TeamManagementService(org_member.organization)
        
        dashboard_data = await team_service.create_team_dashboard(str(team_id), date_range)
        
        return Response(dashboard_data)
        
    except OrganizationMember.DoesNotExist:
        return Response(
            {'error': 'User not part of any organization'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def export_analytics(request):
    """Export analytics data in various formats"""
    try:
        org_member = await OrganizationMember.objects.select_related('organization').aget(
            user=request.user,
            role__in=['owner', 'admin', 'manager']
        )
        
        export_format = request.data.get('format', 'csv')  # csv, excel, pdf
        date_range = int(request.data.get('days', 30))
        include_teams = request.data.get('include_teams', True)
        include_users = request.data.get('include_users', False)
        
        analytics_service = EnterpriseAnalyticsService(org_member.organization)
        
        if export_format == 'csv':
            export_data = await analytics_service.export_to_csv(
                date_range, include_teams, include_users
            )
            response = HttpResponse(export_data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="analytics_{timezone.now().strftime("%Y%m%d")}.csv"'
            
        elif export_format == 'excel':
            export_data = await analytics_service.export_to_excel(
                date_range, include_teams, include_users
            )
            response = HttpResponse(
                export_data, 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="analytics_{timezone.now().strftime("%Y%m%d")}.xlsx"'
            
        else:
            return Response(
                {'error': 'Unsupported export format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response
        
    except OrganizationMember.DoesNotExist:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    