from django.db import migrations, models
from django.db.models import Count, F, Max, Q, Sum
from django.utils import timezone


CATALOG = [
    ('first_recipe', 'Проба пера', 'Опубликуй первый рецепт.', '🥄', 'author', 1, 'recipes', 1),
    ('cook_5', 'Своя рецептурная книга', 'Опубликуй 5 рецептов.', '📒', 'author', 2, 'recipes', 5),
    ('cook_10', 'На своей кухне', 'Опубликуй 10 рецептов.', '🍳', 'author', 3, 'recipes', 10),
    ('cook_25', 'Шеф у плиты', 'Опубликуй 25 рецептов.', '🧑‍🍳', 'author', 4, 'recipes', 25),
    ('cook_50', 'Мастер кухни', 'Опубликуй 50 рецептов.', '🏆', 'author', 5, 'recipes', 50),
    ('photo_recipe', 'Первый кадр', 'Добавь фото к одному своему рецепту.', '📸', 'author', 6, 'photos', 1),
    ('photo_5', 'Съедобный кадр', 'Добавь фото к 5 своим рецептам.', '🖼️', 'author', 7, 'photos', 5),
    ('three_categories', 'Разные вкусы', 'Опубликуй рецепты в 3 разных категориях.', '🧂', 'author', 8, 'categories', 3),
    ('five_categories', 'Широкое меню', 'Опубликуй рецепты в 5 разных категориях.', '🍱', 'author', 9, 'categories', 5),
    ('first_like', 'Первая симпатия', 'Получи первый лайк от другого участника на свой рецепт.', '❤️', 'social', 1, 'likes_total', 1),
    ('likes_10', 'Десять симпатий', 'Получи в сумме 10 лайков от других участников.', '💌', 'social', 2, 'likes_total', 10),
    ('likes_1000', 'Тысяча симпатий', 'Получи в сумме 1 000 лайков от других участников.', '💎', 'social', 3, 'likes_total', 1000),
    ('likes_50', 'Любимое блюдо', 'Получи 50 лайков от других участников на одном рецепте.', '🍽️', 'social', 4, 'likes_best', 50),
    ('likes_100', 'Хит кухни', 'Получи 100 лайков от других участников на одном рецепте.', '🔥', 'social', 5, 'likes_best', 100),
    ('first_subscriber', 'Первый подписчик', 'Получи первого подписчика на FoodStash.', '👋', 'social', 6, 'followers', 1),
    ('followers_5', 'Постоянные гости', 'Собери 5 подписчиков.', '☕', 'social', 7, 'followers', 5),
    ('followers_15', 'Полная посадка', 'Собери 15 подписчиков.', '🎉', 'social', 8, 'followers', 15),
    ('first_comment', 'Первый отзыв', 'Оставь первый комментарий к рецепту.', '💬', 'activity', 1, 'comments', 1),
    ('comments_10', 'Завсегдатай', 'Оставь 10 комментариев к рецептам.', '🗣️', 'activity', 2, 'comments', 10),
    ('comments_50', 'Голос сообщества', 'Оставь 50 комментариев к рецептам.', '📣', 'activity', 3, 'comments', 50),
    ('judge_10', 'Есть мнение', 'Проголосуй за 10 разных комментариев.', '⚖️', 'activity', 4, 'votes', 10),
    ('rate_1', 'Первая оценка', 'Оцени первый рецепт другого автора.', '⭐', 'activity', 5, 'ratings', 1),
    ('rate_5', 'Дегустатор', 'Оцени 5 рецептов других авторов.', '🍴', 'activity', 6, 'ratings', 5),
    ('rate_15', 'Знаток вкуса', 'Оцени 15 рецептов других авторов.', '🏅', 'activity', 7, 'ratings', 15),
    ('culinary_circle', 'Кулинарный круг', 'Подпишись на 5 разных авторов.', '🤝', 'hidden', 1, 'following', 5),
]


def update_achievements(apps, schema_editor):
    Achievement = apps.get_model('recipes', 'Achievement')
    UserAchievement = apps.get_model('recipes', 'UserAchievement')
    User = apps.get_model('recipes', 'User')
    Recipe = apps.get_model('recipes', 'Recipe')
    Like = apps.get_model('recipes', 'Like')
    Comment = apps.get_model('recipes', 'Comment')
    CommentVote = apps.get_model('recipes', 'CommentVote')
    Rating = apps.get_model('recipes', 'Rating')
    Subscription = apps.get_model('recipes', 'Subscription')
    db = schema_editor.connection.alias
    awards = UserAchievement.objects.using(db)
    awards.update(notified_at=F('unlocked_at'))
    milestones = []
    for code, name, description, icon, category, order, metric, target in CATALOG:
        achievement, _ = Achievement.objects.using(db).update_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'icon': icon,
                'category': category,
                'order': order,
                'is_hidden': category == 'hidden',
            },
        )
        milestones.append((achievement.pk, metric, target))

    users = User.objects.using(db).filter(is_active=True, email_confirmation_requested_at__isnull=True)
    recorded_at = timezone.now()
    for user_id in users.values_list('pk', flat=True).iterator():
        values = Recipe.objects.using(db).filter(author_id=user_id).aggregate(
            recipes=Count('pk'),
            photos=Count('pk', filter=Q(image__isnull=False) & ~Q(image='')),
            categories=Count('category', distinct=True),
        )
        per_recipe = Like.objects.using(db).filter(recipe__author_id=user_id).exclude(user_id=user_id)
        per_recipe = per_recipe.order_by().values('recipe_id').annotate(like_count=Count('pk'))
        values.update(per_recipe.aggregate(
            likes_total=Sum('like_count', default=0),
            likes_best=Max('like_count', default=0),
        ))
        subscriptions = Subscription.objects.using(db).exclude(author_id=F('subscriber_id'))
        values.update(
            comments=Comment.objects.using(db).filter(user_id=user_id).count(),
            votes=CommentVote.objects.using(db).filter(user_id=user_id).count(),
            ratings=Rating.objects.using(db).filter(user_id=user_id).exclude(recipe__author_id=user_id).count(),
            followers=subscriptions.filter(author_id=user_id).count(),
            following=subscriptions.filter(subscriber_id=user_id).count(),
        )
        awards.bulk_create([
            UserAchievement(user_id=user_id, achievement_id=achievement_id, notified_at=recorded_at)
            for achievement_id, metric, target in milestones
            if values[metric] >= target
        ], ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0010_user_email_confirmation_requested_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userachievement',
            name='notified_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(update_achievements, migrations.RunPython.noop),
    ]
