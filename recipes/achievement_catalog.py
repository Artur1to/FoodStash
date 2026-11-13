from dataclasses import dataclass


@dataclass(frozen=True)
class Milestone:
    code: str
    name: str
    description: str
    icon: str
    metric: str
    target: int
    tier: str


# Порядок групп и наград задаёт порядок коллекции.
CATALOG = {
    'author': (
        Milestone('first_recipe', 'Проба пера', 'Опубликуй первый рецепт.', '🥄', 'recipes', 1, 'bronze'),
        Milestone('cook_5', 'Своя рецептурная книга', 'Опубликуй 5 рецептов.', '📒', 'recipes', 5, 'bronze'),
        Milestone('cook_10', 'На своей кухне', 'Опубликуй 10 рецептов.', '🍳', 'recipes', 10, 'silver'),
        Milestone('cook_25', 'Шеф у плиты', 'Опубликуй 25 рецептов.', '🧑‍🍳', 'recipes', 25, 'silver'),
        Milestone('cook_50', 'Мастер кухни', 'Опубликуй 50 рецептов.', '🏆', 'recipes', 50, 'gold'),
        Milestone('photo_recipe', 'Первый кадр', 'Добавь фото к одному своему рецепту.', '📸', 'photos', 1, 'bronze'),
        Milestone('photo_5', 'Съедобный кадр', 'Добавь фото к 5 своим рецептам.', '🖼️', 'photos', 5, 'silver'),
        Milestone('three_categories', 'Разные вкусы', 'Опубликуй рецепты в 3 разных категориях.', '🧂', 'categories', 3, 'bronze'),
        Milestone('five_categories', 'Широкое меню', 'Опубликуй рецепты в 5 разных категориях.', '🍱', 'categories', 5, 'silver'),
    ),
    'social': (
        Milestone('first_like', 'Первая симпатия', 'Получи первый лайк от другого участника на свой рецепт.', '❤️', 'likes_total', 1, 'bronze'),
        Milestone('likes_10', 'Десять симпатий', 'Получи в сумме 10 лайков от других участников.', '💌', 'likes_total', 10, 'silver'),
        Milestone('likes_1000', 'Тысяча симпатий', 'Получи в сумме 1 000 лайков от других участников.', '💎', 'likes_total', 1000, 'gold'),
        Milestone('likes_50', 'Любимое блюдо', 'Получи 50 лайков от других участников на одном рецепте.', '🍽️', 'likes_best', 50, 'silver'),
        Milestone('likes_100', 'Хит кухни', 'Получи 100 лайков от других участников на одном рецепте.', '🔥', 'likes_best', 100, 'gold'),
        Milestone('first_subscriber', 'Первый подписчик', 'Получи первого подписчика на FoodStash.', '👋', 'followers', 1, 'bronze'),
        Milestone('followers_5', 'Постоянные гости', 'Собери 5 подписчиков.', '☕', 'followers', 5, 'silver'),
        Milestone('followers_15', 'Полная посадка', 'Собери 15 подписчиков.', '🎉', 'followers', 15, 'gold'),
    ),
    'activity': (
        Milestone('first_comment', 'Первый отзыв', 'Оставь первый комментарий к рецепту.', '💬', 'comments', 1, 'bronze'),
        Milestone('comments_10', 'Завсегдатай', 'Оставь 10 комментариев к рецептам.', '🗣️', 'comments', 10, 'silver'),
        Milestone('comments_50', 'Голос сообщества', 'Оставь 50 комментариев к рецептам.', '📣', 'comments', 50, 'gold'),
        Milestone('judge_10', 'Есть мнение', 'Проголосуй за 10 разных комментариев.', '⚖️', 'votes', 10, 'silver'),
        Milestone('rate_1', 'Первая оценка', 'Оцени первый рецепт другого автора.', '⭐', 'ratings', 1, 'bronze'),
        Milestone('rate_5', 'Дегустатор', 'Оцени 5 рецептов других авторов.', '🍴', 'ratings', 5, 'silver'),
        Milestone('rate_15', 'Знаток вкуса', 'Оцени 15 рецептов других авторов.', '🏅', 'ratings', 15, 'gold'),
    ),
    'hidden': (
        Milestone('culinary_circle', 'Кулинарный круг', 'Подпишись на 5 разных авторов.', '🤝', 'following', 5, 'gold'),
    ),
}

MILESTONES = {milestone.code: milestone for group in CATALOG.values() for milestone in group}
CATEGORY_LABELS = {
    'author': 'Своя кухня',
    'social': 'Признание',
    'activity': 'За общим столом',
    'hidden': 'Секретные',
}
TIER_LABELS = {'bronze': 'Бронза', 'silver': 'Серебро', 'gold': 'Золото'}
