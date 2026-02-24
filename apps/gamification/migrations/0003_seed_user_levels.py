"""
Seed the UserLevel table with the default XP ladder.
Each level requires 200 XP more than the previous (progressive difficulty).
"""
from django.db import migrations


LEVELS = [
    # (level, name, experience_required, credits_reward, title_reward,
    #  max_templates, ai_requests_per_day, can_create_premium)
    (1,  "Temple Initiate",    0,     0,    "",                     10,  5,  False),
    (2,  "Apprentice Scribe",  200,   10,   "",                     15,  8,  False),
    (3,  "Junior Architect",   500,   20,   "",                     20,  10, False),
    (4,  "Prompt Artisan",     900,   30,   "Artisan",              25,  15, False),
    (5,  "Temple Scholar",     1400,  50,   "Scholar",              35,  20, False),
    (6,  "Hieroglyph Master",  2000,  75,   "Master",               50,  25, True),
    (7,  "Oracle of Prompts",  2800,  100,  "Oracle",               75,  35, True),
    (8,  "High Priest",        3800,  150,  "High Priest",          100, 50, True),
    (9,  "Pyramid Builder",    5000,  200,  "Pyramid Builder",      150, 75, True),
    (10, "Temple Guardian",    6500,  300,  "Temple Guardian",      200, 100, True),
]


def seed_levels(apps, schema_editor):
    UserLevel = apps.get_model("gamification", "UserLevel")
    for (level, name, xp, credits, title, max_tmpl, ai_req, premium) in LEVELS:
        UserLevel.objects.get_or_create(
            level=level,
            defaults=dict(
                name=name,
                experience_required=xp,
                credits_reward=credits,
                title_reward=title,
                max_templates=max_tmpl,
                ai_requests_per_day=ai_req,
                can_create_premium=premium,
            ),
        )


def remove_levels(apps, schema_editor):
    UserLevel = apps.get_model("gamification", "UserLevel")
    UserLevel.objects.filter(level__in=[l[0] for l in LEVELS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(seed_levels, remove_levels),
    ]
