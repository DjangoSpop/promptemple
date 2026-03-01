"""
Migration: Add monetization / freemium gating fields to Template model.

All fields are nullable with safe defaults so existing rows are unaffected.

Rollback:
    python manage.py migrate templates 0008
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            'templates',
            '0008_rename_chat_messag_session_597c4e_idx_template_ch_session_b195ab_idx_and_more',
        ),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='is_premium_required',
            field=models.BooleanField(
                blank=True,
                default=False,
                null=True,
                help_text='Whether a premium subscription is required to use this template',
            ),
        ),
        migrations.AddField(
            model_name='template',
            name='required_subscription',
            field=models.CharField(
                blank=True,
                choices=[
                    ('free', 'Free'),
                    ('basic', 'Basic'),
                    ('premium', 'Premium'),
                    ('enterprise', 'Enterprise'),
                ],
                default='free',
                max_length=20,
                null=True,
                help_text='Minimum subscription tier required to access this template',
            ),
        ),
        migrations.AddField(
            model_name='template',
            name='token_cost',
            field=models.PositiveIntegerField(
                blank=True,
                default=0,
                null=True,
                help_text='Credit cost deducted per use (0 = free)',
            ),
        ),
        migrations.AddField(
            model_name='template',
            name='copy_limit_per_day',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text='Maximum number of copies per user per day; null means unlimited',
            ),
        ),
    ]
