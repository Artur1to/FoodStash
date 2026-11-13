from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from .achievement_catalog import CATEGORY_LABELS, MILESTONES, TIER_LABELS
from .models import Achievement, Comment, CommentVote, Like, Rating, Subscription


def _measure(user, metrics):
    values = {}
    recipe_counts = {
        'recipes': Count('pk'),
        'photos': Count('pk', filter=Q(image__isnull=False) & ~Q(image='')),
        'categories': Count('category', distinct=True),
    }
    selected_counts = {key: recipe_counts[key] for key in metrics & recipe_counts.keys()}
    if selected_counts:
        values.update(user.recipes.aggregate(**selected_counts))

    if metrics & {'likes_total', 'likes_best'}:
        likes = Like.objects.filter(recipe__author=user).exclude(user=user)
        per_recipe = likes.order_by().values('recipe_id').annotate(like_count=Count('pk'))
        values.update(per_recipe.aggregate(
            likes_total=Sum('like_count', default=0),
            likes_best=Max('like_count', default=0),
        ))

    sources = {
        'comments': lambda: Comment.objects.filter(user=user),
        'votes': lambda: CommentVote.objects.filter(user=user),
        'ratings': lambda: Rating.objects.filter(user=user).exclude(recipe__author=user),
        'followers': lambda: user.subscribers.exclude(subscriber=user),
        'following': lambda: Subscription.objects.filter(subscriber=user).exclude(author=user),
    }
    for key in metrics & sources.keys():
        values[key] = sources[key]().count()
    return values


def grant(user, *metrics, notify=True):
    earned = set(user.achievements.values_list('achievement__code', flat=True))
    candidates = [
        milestone for code, milestone in MILESTONES.items()
        if code not in earned and (not metrics or milestone.metric in metrics)
    ]
    if not candidates:
        return 0

    values = _measure(user, {milestone.metric for milestone in candidates})
    eligible = [milestone.code for milestone in candidates if values[milestone.metric] >= milestone.target]
    granted = 0
    for achievement in Achievement.objects.filter(code__in=eligible):
        _, created = user.achievements.get_or_create(
            achievement=achievement,
            defaults={'notified_at': None if notify else timezone.now()},
        )
        granted += created
    return granted


def take_notifications(user, limit=3):
    pending = list(user.achievements.filter(notified_at__isnull=True)
                   .select_related('achievement').order_by('unlocked_at', 'pk')[:limit])
    shown_at = timezone.now()
    return [
        award for award in pending
        if user.achievements.filter(pk=award.pk, notified_at__isnull=True).update(notified_at=shown_at)
    ]


def notification_data(user):
    return [
        {'name': award.achievement.name, 'icon': award.achievement.icon}
        for award in take_notifications(user)
    ]


def _card(achievement, award=None, progress=None):
    milestone = MILESTONES.get(achievement.code)
    tier = milestone.tier if milestone else 'bronze'
    return {
        'achievement': achievement,
        'earned_at': award.unlocked_at if award else None,
        'tier': tier,
        'tier_label': TIER_LABELS[tier],
        'target': milestone.target if milestone else None,
        'progress': progress,
    }


def preview(user):
    earned = user.achievements.select_related('achievement').order_by('-unlocked_at', '-pk')
    return {
        'count': earned.count(),
        'cards': [_card(award.achievement, award) for award in earned[:4]],
    }


def collection(user, is_own):
    earned = {award.achievement_id: award for award in user.achievements.select_related('achievement')}
    items = Achievement.objects.order_by('order', 'pk') if is_own else (
        award.achievement for award in earned.values()
    )
    groups = {key: {'cards': [], 'secret_count': 0} for key in CATEGORY_LABELS}
    pending = []
    scheduled = []

    for achievement in items:
        award = earned.get(achievement.pk)
        milestone = MILESTONES.get(achievement.code)
        if award is None and milestone is None:
            continue
        category = 'hidden' if achievement.is_hidden else achievement.category
        if category not in groups:
            category = 'activity'
        group = groups[category]
        if category == 'hidden' and award is None:
            group['secret_count'] += 1
            continue
        if award is None:
            scheduled.append(milestone)
        pending.append((achievement, award, group))

    values = _measure(user, {milestone.metric for milestone in scheduled})
    next_goal = None
    best_fraction = -1
    for achievement, award, group in pending:
        progress = None
        if award is None:
            milestone = MILESTONES[achievement.code]
            progress = min(values[milestone.metric], milestone.target)
        card = _card(achievement, award, progress)
        group['cards'].append(card)

        if progress is not None:
            fraction = progress / card['target']
            if fraction > best_fraction:
                best_fraction = fraction
                next_goal = card

    visible_groups = []
    for key, group in groups.items():
        cards = group['cards']
        if cards or group['secret_count']:
            cards.sort(key=lambda card: (card['earned_at'] is None, card['achievement'].order))
            visible_groups.append({
                **group,
                'key': key,
                'name': CATEGORY_LABELS[key],
                'earned': sum(card['earned_at'] is not None for card in cards),
                'total': len(cards) + group['secret_count'],
            })

    total = sum(group['total'] for group in visible_groups)
    return {
        'groups': visible_groups,
        'earned_count': len(earned),
        'total': total,
        'next_goal': next_goal,
    }
