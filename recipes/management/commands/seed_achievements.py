from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.achievement_catalog import CATALOG
from recipes.achievements import grant
from recipes.models import Achievement, User


class Command(BaseCommand):
    help = 'Обновить каталог достижений и начислить награды за уже выполненные условия.'

    @transaction.atomic
    def handle(self, *args, **options):
        for category, milestones in CATALOG.items():
            for order, milestone in enumerate(milestones, start=1):
                Achievement.objects.update_or_create(
                    code=milestone.code,
                    defaults={
                        'name': milestone.name,
                        'description': milestone.description,
                        'icon': milestone.icon,
                        'category': category,
                        'is_hidden': category == 'hidden',
                        'order': order,
                    },
                )

        users = User.objects.filter(is_active=True, email_confirmation_requested_at__isnull=True)
        granted = sum(grant(user, notify=False) for user in users.iterator())
        self.stdout.write(self.style.SUCCESS(f'Каталог обновлён. Начислено наград за прошлые действия: {granted}.'))
