from django.utils import timezone
from django.db import transaction
from django.db.models import F, Sum
from .models import (
    Achievement, UserAchievement, DailyChallenge, 
    UserDailyChallenge, CreditTransaction, UserLevel
)
import logging

logger = logging.getLogger(__name__)

class GamificationService:
    """
    Service for handling all gamification features
    
    Provides:
    - Credit management
    - Achievement checking
    - Level calculation
    - Daily challenge tracking
    - Reward distribution
    """
    
    @staticmethod
    def award_credits(user, amount, reason, transaction_type='bonus', related_object=None, metadata=None):
        """
        Award credits to user and create transaction record
        
        Args:
            user: User object
            amount: Number of credits to award (positive integer)
            reason: Human-readable reason for awarding credits
            transaction_type: Type of transaction for tracking
            related_object: Optional related object (template, achievement, etc.)
            metadata: Optional additional data
        
        Returns:
            New credit balance
        """
        user.credits += amount
        user.save(update_fields=['credits'])
        print(f"🎮 Gamification: Awarded {amount} credits to {user.username} - {reason}")
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        
        with transaction.atomic():
            # Update user credits
            user.credits = F('credits') + amount
            user.save(update_fields=['credits'])
            
            # Refresh to get actual value
            user.refresh_from_db(fields=['credits'])
            
            # Create transaction record
            transaction_data = {
                'user': user,
                'amount': amount,
                'balance_after': user.credits,
                'transaction_type': transaction_type,
                'description': reason,
                'metadata': metadata or {}
            }
            
            if related_object:
                transaction_data['related_object_type'] = related_object.__class__.__name__.lower()
                transaction_data['related_object_id'] = str(related_object.id)
            
            CreditTransaction.objects.create(**transaction_data)
            
            logger.info(f"Awarded {amount} credits to user {user.username}: {reason}")
            return user.credits
    
    @staticmethod
    def spend_credits(user, amount, reason, transaction_type='spent_ai', related_object=None):
        """
        Spend user credits with validation
        
        Args:
            user: User object
            amount: Number of credits to spend (positive integer)
            reason: Human-readable reason for spending credits
            transaction_type: Type of transaction
            related_object: Optional related object
        
        Returns:
            Remaining credit balance
        
        Raises:
            ValueError: If user has insufficient credits
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        
        if user.credits < amount:
            raise ValueError(f"Insufficient credits. Required: {amount}, Available: {user.credits}")
        
        with transaction.atomic():
            # Update user credits
            user.credits = F('credits') - amount
            user.save(update_fields=['credits'])
            
            # Refresh to get actual value
            user.refresh_from_db(fields=['credits'])
            
            # Create transaction record
            transaction_data = {
                'user': user,
                'amount': -amount,  # Negative for spending
                'balance_after': user.credits,
                'transaction_type': transaction_type,
                'description': reason,
            }
            
            if related_object:
                transaction_data['related_object_type'] = related_object.__class__.__name__.lower()
                transaction_data['related_object_id'] = str(related_object.id)
            
            CreditTransaction.objects.create(**transaction_data)
            
            logger.info(f"User {user.username} spent {amount} credits: {reason}")
            return user.credits
    
    @staticmethod
    def check_achievements(user):
        """
        Check and unlock achievements for user
        
        Args:
            user: User object
        
        Returns:
            List of newly unlocked UserAchievement objects
        """
        unlocked = []
        
        # Get all available achievements user hasn't unlocked yet
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(
            user_unlocks__user=user,
            user_unlocks__is_unlocked=True
        )
        
        for achievement in available_achievements:
            # Check if achievement is available (time-based)
            if not achievement.is_available():
                continue
            
            # Get or create user achievement record
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement,
                defaults={'progress_value': 0}
            )
            
            # Update progress based on achievement type
            current_progress = GamificationService._calculate_achievement_progress(user, achievement)
            user_achievement.progress_value = current_progress
            user_achievement.save(update_fields=['progress_value'])
            
            # Check if newly unlocked
            if user_achievement.check_unlock():
                unlocked.append(user_achievement)
                logger.info(f"User {user.username} unlocked achievement: {achievement.name}")
        
        return unlocked
    @staticmethod
    def update_daily_streak(user):
        """Update user's daily streak"""
        today = timezone.now().date()
        
        if user.last_login_date != today:
            if user.last_login_date and user.last_login_date == today - timezone.timedelta(days=1):
                # Consecutive day
                user.daily_streak += 1
            else:
                # First day or broken streak
                user.daily_streak = 1
            
            user.last_login_date = today
            user.save(update_fields=['daily_streak', 'last_login_date'])
            print(f"🔥 Streak updated for {user.username}: {user.daily_streak} days")
        
        return user.daily_streak
    @staticmethod
    def _calculate_achievement_progress(user, achievement):
        """
        Calculate user's current progress for a specific achievement
        
        Args:
            user: User object
            achievement: Achievement object
        
        Returns:
            Current progress value
        """
        req_type = achievement.requirement_type
        
        if req_type == 'templates_created':
            return user.templates_created
        elif req_type == 'templates_completed':
            return user.templates_completed
        elif req_type == 'daily_streak':
            return user.daily_streak
        elif req_type == 'level':
            return user.level
        elif req_type == 'credits_earned':
            total_earned = CreditTransaction.objects.filter(
                user=user, 
                amount__gt=0
            ).aggregate(total=Sum('amount'))['total'] or 0
            return total_earned
        elif req_type == 'prompts_generated':
            return user.total_prompts_generated
        elif req_type == 'ai_requests':
            from apps.ai_services.models import AIInteraction
            return AIInteraction.objects.filter(
                user=user,
                was_successful=True
            ).count()
        elif req_type == 'template_ratings':
            from apps.templates.models import TemplateRating
            return TemplateRating.objects.filter(user=user).count()
        
        return 0
    
    @staticmethod
    def claim_achievement_reward(user, achievement_id):
        """
        Claim reward for an unlocked achievement
        
        Args:
            user: User object
            achievement_id: Achievement ID to claim
        
        Returns:
            Dict with reward details
        
        Raises:
            ValueError: If achievement not unlocked or already claimed
        """
        try:
            user_achievement = UserAchievement.objects.get(
                user=user,
                achievement_id=achievement_id,
                is_unlocked=True,
                is_claimed=False
            )
        except UserAchievement.DoesNotExist:
            raise ValueError("Achievement not found, not unlocked, or already claimed")
        
        achievement = user_achievement.achievement
        
        with transaction.atomic():
            # Award credits
            if achievement.credits_reward > 0:
                GamificationService.award_credits(
                    user=user,
                    amount=achievement.credits_reward,
                    reason=f'Achievement reward: {achievement.name}',
                    transaction_type='earned_achievement',
                    related_object=achievement
                )
            
            # Award experience
            if achievement.experience_reward > 0:
                user.experience_points = F('experience_points') + achievement.experience_reward
                user.save(update_fields=['experience_points'])
                user.refresh_from_db(fields=['experience_points'])
                
                # Check for level up
                GamificationService.check_level_up(user)
            
            # Mark as claimed
            user_achievement.is_claimed = True
            user_achievement.claimed_at = timezone.now()
            user_achievement.save(update_fields=['is_claimed', 'claimed_at'])
        
        return {
            'achievement_name': achievement.name,
            'credits_earned': achievement.credits_reward,
            'experience_earned': achievement.experience_reward,
            'new_credit_balance': user.credits,
            'new_experience': user.experience_points
        }
    
    @staticmethod
    def update_daily_streak(user):
        """
        Update user's daily streak based on login patterns
        
        Args:
            user: User object
        
        Returns:
            Updated streak count
        """
        today = timezone.now().date()
        
        if user.last_login_date == today:
            # Already logged in today
            return user.daily_streak
        
        with transaction.atomic():
            if user.last_login_date == today - timezone.timedelta(days=1):
                # Consecutive day - increment streak
                user.daily_streak = F('daily_streak') + 1
            else:
                # Streak broken - reset to 1
                user.daily_streak = 1
            
            user.last_login_date = today
            user.save(update_fields=['daily_streak', 'last_login_date'])
            user.refresh_from_db(fields=['daily_streak'])
            
            # Award streak milestone bonuses
            if user.daily_streak in [7, 14, 30, 60, 100]:  # Milestone days
                bonus_credits = user.daily_streak * 2
                GamificationService.award_credits(
                    user=user,
                    amount=bonus_credits,
                    reason=f'Daily streak milestone: {user.daily_streak} days',
                    transaction_type='bonus',
                    metadata={'streak_milestone': user.daily_streak}
                )
            
            # Check for streak achievements
            GamificationService.check_achievements(user)
        
        return user.daily_streak
    
    @staticmethod
    def check_level_up(user):
        """
        Check if user should level up based on experience points
        
        Args:
            user: User object
        
        Returns:
            Dict with level up info or None if no level up
        """
        try:
            next_level = UserLevel.objects.filter(
                experience_required__lte=user.experience_points,
                level__gt=user.level
            ).order_by('level').first()
            
            if next_level:
                old_level = user.level
                user.level = next_level.level
                
                # Update user rank if level has title reward
                if next_level.title_reward:
                    user.user_rank = next_level.title_reward
                
                user.save(update_fields=['level', 'user_rank'])
                
                # Award level up rewards
                if next_level.credits_reward > 0:
                    GamificationService.award_credits(
                        user=user,
                        amount=next_level.credits_reward,
                        reason=f'Level up reward: Level {next_level.level}',
                        transaction_type='bonus',
                        metadata={'level_up': {'from': old_level, 'to': next_level.level}}
                    )
                
                # Check for level-based achievements
                GamificationService.check_achievements(user)
                
                logger.info(f"User {user.username} leveled up from {old_level} to {next_level.level}")
                
                return {
                    'old_level': old_level,
                    'new_level': next_level.level,
                    'new_rank': user.user_rank,
                    'credits_reward': next_level.credits_reward,
                    'new_perks': {
                        'max_templates': next_level.max_templates,
                        'ai_requests_per_day': next_level.ai_requests_per_day,
                        'can_create_premium': next_level.can_create_premium
                    }
                }
        
        except UserLevel.DoesNotExist:
            pass
        
        return None
    
    @staticmethod
    def update_daily_challenge_progress(user, challenge_type, value=1):
        """
        Update progress on daily challenges
        
        Args:
            user: User object
            challenge_type: Type of challenge to update
            value: Progress value to add (default 1)
        """
        today = timezone.now().date()
        
        # Get today's challenges of this type
        challenges = DailyChallenge.objects.filter(
            date=today,
            challenge_type=challenge_type,
            is_active=True
        )
        
        for challenge in challenges:
            user_challenge, created = UserDailyChallenge.objects.get_or_create(
                user=user,
                challenge=challenge,
                defaults={'progress_value': 0}
            )
            
            if not user_challenge.is_completed:
                # Update progress
                user_challenge.progress_value = F('progress_value') + value
                user_challenge.save(update_fields=['progress_value'])
                user_challenge.refresh_from_db(fields=['progress_value'])
                
                # Check if completed
                if user_challenge.progress_value >= challenge.target_value:
                    user_challenge.is_completed = True
                    user_challenge.completed_at = timezone.now()
                    user_challenge.save(update_fields=['is_completed', 'completed_at'])
                    
                    # Award rewards
                    if challenge.credits_reward > 0:
                        GamificationService.award_credits(
                            user=user,
                            amount=challenge.credits_reward,
                            reason=f'Daily challenge completed: {challenge.title}',
                            transaction_type='earned_challenge',
                            related_object=challenge
                        )
                    
                    if challenge.experience_reward > 0:
                        user.experience_points = F('experience_points') + challenge.experience_reward
                        user.save(update_fields=['experience_points'])
                        user.refresh_from_db(fields=['experience_points'])
                        
                        # Check for level up
                        GamificationService.check_level_up(user)
                    
                    logger.info(f"User {user.username} completed daily challenge: {challenge.title}")

    @staticmethod
    def calculate_level(experience_points):
        """Calculate user level based on experience points"""
        return max(1, experience_points // 100 + 1)
    
    @staticmethod
    def get_user_stats(user):
        """
        Get comprehensive user gamification stats
        
        Args:
            user: User object
        
        Returns:
            Dict with user statistics
        """
        # Get recent transactions
        recent_transactions = CreditTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Get unlocked achievements
        unlocked_achievements = UserAchievement.objects.filter(
            user=user,
            is_unlocked=True
        ).select_related('achievement').order_by('-unlocked_at')[:5]
        
        # Get today's challenges
        today = timezone.now().date()
        daily_challenges = UserDailyChallenge.objects.filter(
            user=user,
            challenge__date=today
        ).select_related('challenge')
        
        # Calculate next level info
        try:
            next_level = UserLevel.objects.filter(
                level__gt=user.level
            ).order_by('level').first()
            
            if next_level:
                exp_needed = next_level.experience_required - user.experience_points
                exp_progress = user.experience_points - UserLevel.objects.filter(
                    level=user.level
                ).first().experience_required
                current_level_obj = UserLevel.objects.get(level=user.level)
                exp_for_current_level = next_level.experience_required - current_level_obj.experience_required
                level_progress = exp_progress / exp_for_current_level if exp_for_current_level > 0 else 1
            else:
                exp_needed = 0
                level_progress = 1
        except (UserLevel.DoesNotExist, AttributeError):
            exp_needed = 0
            level_progress = 1
        
        return {
            'credits': user.credits,
            'level': user.level,
            'experience_points': user.experience_points,
            'daily_streak': user.daily_streak,
            'user_rank': user.user_rank,
            'templates_created': user.templates_created,
            'templates_completed': user.templates_completed,
            'total_prompts_generated': user.total_prompts_generated,
            'completion_rate': user.completion_rate,
            'level_progress': {
                'current_level': user.level,
                'next_level': next_level.level if next_level else user.level,
                'experience_needed': exp_needed,
                'progress_percentage': level_progress * 100
            },
            'recent_transactions': [
                {
                    'amount': tx.amount,
                    'type': tx.transaction_type,
                    'description': tx.description,
                    'created_at': tx.created_at
                }
                for tx in recent_transactions
            ],
            'recent_achievements': [
                {
                    'name': ua.achievement.name,
                    'description': ua.achievement.description,
                    'icon': ua.achievement.icon,
                    'rarity': ua.achievement.rarity,
                    'unlocked_at': ua.unlocked_at,
                    'is_claimed': ua.is_claimed
                }
                for ua in unlocked_achievements
            ],
            'daily_challenges': [
                {
                    'title': uc.challenge.title,
                    'description': uc.challenge.description,
                    'progress_value': uc.progress_value,
                    'target_value': uc.challenge.target_value,
                    'progress_percentage': uc.progress_percentage,
                    'is_completed': uc.is_completed,
                    'credits_reward': uc.challenge.credits_reward,
                    'experience_reward': uc.challenge.experience_reward
                }
                for uc in daily_challenges
            ]
        }
    
    @staticmethod
    def check_achievements(user):
        """Check and unlock any new achievements for the user"""
        # Placeholder implementation
        print(f"🏆 Gamification: Checking achievements for {user.username}")
        
        # This would normally check various conditions and unlock achievements
        # For now, just return empty list
        return []
    
    @staticmethod
    def update_daily_challenge_progress(user, challenge_type, value=1):
        """Update progress for daily challenges"""
        print(f"📅 Daily Challenge: Updated {challenge_type} progress by {value} for {user.username}")
        
        # Placeholder implementation
        # This would normally update UserDailyChallenge records
        return True
    
    @staticmethod
    def calculate_level(experience_points):
        """Calculate user level based on experience points"""
        return max(1, experience_points // 100 + 1)
    
    @staticmethod
    def get_level_progress(user):
        """Get detailed level progression information"""
        current_level_xp = (user.level - 1) * 100
        next_level_xp = user.level * 100
        progress_xp = user.experience_points - current_level_xp
        needed_xp = next_level_xp - user.experience_points
        
        return {
            'current_level': user.level,
            'current_xp': user.experience_points,
            'level_start_xp': current_level_xp,
            'next_level_xp': next_level_xp,
            'progress_xp': progress_xp,
            'needed_xp': max(0, needed_xp),
            'progress_percentage': min(100, (progress_xp / 100) * 100)
        }
