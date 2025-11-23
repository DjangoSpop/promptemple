from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.prompt_history.models import PromptHistory
try:
    from apps.templates.models import PromptLibrary
except Exception:
    PromptLibrary = None
import json
import logging

logger = logging.getLogger(__name__)


SAMPLE_PROMPTS = [
    {
        'title': 'Welcome Email for New Users',
        'content': 'Write a friendly welcome email to a new user, include next steps and links.',
        'category': 'email',
        'tags': ['welcome', 'email']
    },
    {
        'title': 'Product Description for Smart Mug',
        'content': 'Create a 3-line product description for a smart mug focused on office workers.',
        'category': 'product',
        'tags': ['marketing', 'product']
    },
]


class Command(BaseCommand):
    help = 'Seed a small set of prompts (200-500 recommended) - idempotent by title'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        if PromptLibrary is None:
            self.stdout.write(self.style.WARNING('PromptLibrary model not found; skipping library seeding'))
            return
        for item in SAMPLE_PROMPTS:
            title = item['title']
            try:
                obj, was_created = PromptLibrary.objects.update_or_create(
                    title=title,
                    defaults={
                        'content': item['content'],
                        'category': item.get('category', ''),
                        'tags': item.get('tags', []),
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                logger.exception('Error seeding prompt %s: %s', title, e)

        self.stdout.write(self.style.SUCCESS(f'Seed complete. created={created} updated={updated}'))
