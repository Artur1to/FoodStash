from django.core.management.base import BaseCommand
from recipes.models import Achievement


ACHIEVEMENTS = [
    {'code': 'first_recipe', 'name': 'Первый шаг', 'icon': '🥄',
     'description': 'Опубликовал первый рецепт', 'category': 'author', 'order': 1},
    {'code': 'cook_5', 'name': 'Кулинар-новичок', 'icon': '🍳',
     'description': 'Опубликовал 5 рецептов', 'category': 'author', 'order': 2},
    {'code': 'cook_10', 'name': 'Опытный повар', 'icon': '👨‍🍳',
     'description': 'Опубликовал 10 рецептов', 'category': 'author', 'order': 3},
    {'code': 'cook_25', 'name': 'Шеф-повар', 'icon': '🎩',
     'description': 'Опубликовал 25 рецептов', 'category': 'author', 'order': 4},
    {'code': 'cook_50', 'name': 'Мастер кухни', 'icon': '🏆',
     'description': 'Опубликовал 50 рецептов', 'category': 'author', 'order': 5},

    {'code': 'first_like', 'name': 'Первая любовь', 'icon': '💕',
     'description': 'Получил первый лайк на рецепт', 'category': 'social', 'order': 1},
    {'code': 'likes_50', 'name': 'Народный любимец', 'icon': '❤️',
     'description': 'Набрал 50 лайков на одном рецепте', 'category': 'social', 'order': 2},
    {'code': 'likes_100', 'name': 'Хит кухни', 'icon': '🔥',
     'description': 'Набрал 100 лайков на одном рецепте', 'category': 'social', 'order': 3},
    {'code': 'likes_1000', 'name': 'Миллионник', 'icon': '💎',
     'description': 'Суммарно 1000 лайков на всех рецептах', 'category': 'social', 'order': 4},

    {'code': 'first_comment', 'name': 'Первый отзыв', 'icon': '💬',
     'description': 'Оставил первый комментарий', 'category': 'activity', 'order': 1},
    {'code': 'comments_50', 'name': 'Активный критик', 'icon': '📝',
     'description': 'Оставил 50 комментариев', 'category': 'activity', 'order': 2},
    {'code': 'photo_recipe', 'name': 'С картинкой', 'icon': '📷',
     'description': 'Опубликовал рецепт с фото', 'category': 'activity', 'order': 3},
    {'code': 'five_categories', 'name': 'Пять категорий', 'icon': '🎯',
     'description': 'Опубликовал рецепты в 5 разных категориях', 'category': 'activity', 'order': 4},
    {'code': 'judge_10', 'name': 'Судья', 'icon': '⚖️',
     'description': 'Проголосовал за 10 комментариев', 'category': 'activity', 'order': 5},
]


class Command(BaseCommand):
    help = 'Создать базовые ачивки'

    def handle(self, *args, **options):
        created = 0
        for data in ACHIEVEMENTS:
            obj, was_created = Achievement.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"✓ {data['icon']} {data['name']}"))

        self.stdout.write(self.style.SUCCESS(f"\nСоздано ачивок: {created}"))