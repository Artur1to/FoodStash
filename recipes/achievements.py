from .models import Achievement, UserAchievement, Recipe, Comment, CommentVote


def _grant(user, code):
    """Выдать ачивку, если её ещё нет. Возвращает True, если только что выдали."""
    try:
        ach = Achievement.objects.get(code=code)
    except Achievement.DoesNotExist:
        return False

    if UserAchievement.objects.filter(user=user, achievement=ach).exists():
        return False

    UserAchievement.objects.create(user=user, achievement=ach)
    return True


def check_recipe_achievements(user):
    """Проверка ачивок при публикации рецепта"""
    unlocked = []

    recipes = Recipe.objects.filter(author=user)
    count = recipes.count()

    if count >= 1 and _grant(user, 'first_recipe'):
        unlocked.append('first_recipe')
    if count >= 5 and _grant(user, 'cook_5'):
        unlocked.append('cook_5')
    if count >= 10 and _grant(user, 'cook_10'):
        unlocked.append('cook_10')
    if count >= 25 and _grant(user, 'cook_25'):
        unlocked.append('cook_25')
    if count >= 50 and _grant(user, 'cook_50'):
        unlocked.append('cook_50')

    if recipes.filter(image__isnull=False).exclude(image='').exists():
        if _grant(user, 'photo_recipe'):
            unlocked.append('photo_recipe')

    categories_count = recipes.values('category').distinct().count()
    if categories_count >= 5 and _grant(user, 'five_categories'):
        unlocked.append('five_categories')

    return unlocked


def check_like_received(recipe_author):
    """Проверка ачивок, когда автор получил лайк"""
    unlocked = []

    recipes = Recipe.objects.filter(author=recipe_author)
    has_any_like = any(r.likes.exists() for r in recipes)

    if has_any_like and _grant(recipe_author, 'first_like'):
        unlocked.append('first_like')

    max_likes = 0
    total_likes = 0
    for r in recipes:
        c = r.likes.count()
        max_likes = max(max_likes, c)
        total_likes += c

    if max_likes >= 50 and _grant(recipe_author, 'likes_50'):
        unlocked.append('likes_50')
    if max_likes >= 100 and _grant(recipe_author, 'likes_100'):
        unlocked.append('likes_100')
    if total_likes >= 1000 and _grant(recipe_author, 'likes_1000'):
        unlocked.append('likes_1000')

    return unlocked


def check_comment_achievements(user):
    """Ачивки за комментарии"""
    unlocked = []

    count = Comment.objects.filter(user=user).count()

    if count >= 1 and _grant(user, 'first_comment'):
        unlocked.append('first_comment')
    if count >= 50 and _grant(user, 'comments_50'):
        unlocked.append('comments_50')

    return unlocked


def check_vote_achievements(user):
    """Ачивки за голосование на комментариях"""
    unlocked = []

    count = CommentVote.objects.filter(user=user).count()

    if count >= 10 and _grant(user, 'judge_10'):
        unlocked.append('judge_10')

    return unlocked