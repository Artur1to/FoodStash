from contextlib import nullcontext

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.cache import add_never_cache_headers, patch_vary_headers
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from .email_confirmation import RESEND_DELAY, confirmation_matches, send_confirmation
from .forms import RegisterForm, ResendConfirmationForm, UserForm, RecipeForm, RecipeIngredientFormSet
from . import achievements
from .search import ingredient_suggestions, match_ingredients, normalize
from .models import (
    User, Category, Recipe,
    RecipeIngredient, Favorite, Rating, Comment, Like, CommentVote,
    Subscription
)


def _wants_fragment(request):
    return request.headers.get('X-FoodStash-Fragment') == '1'


def _render_section(request, template_name, partial, context):
    is_fragment = _wants_fragment(request)
    template = f'{template_name}#{partial}' if is_fragment else template_name
    response = render(request, template, context)
    patch_vary_headers(response, ('X-FoodStash-Fragment',))
    if is_fragment:
        add_never_cache_headers(response)
    return response


def home(request):
    recipes = Recipe.objects.order_by('-created_at')[:8]
    categories = Category.objects.all()
    return render(request, 'recipes/home.html', {
        'recipes': recipes,
        'categories': categories,
    })


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            if 'registration' not in settings.MAILERS:
                form.add_error(None, 'Отправка писем пока недоступна. Попробуй позже.')
            else:
                user = form.save(commit=False)
                user.is_active = False
                user.email_confirmation_requested_at = timezone.now()
                user.save()
                request.session['pending_registration_id'] = user.pk
                request.session['registration_mail_state'] = 'sent' if send_confirmation(request, user) else 'failed'
                return redirect('registration_pending')
    else:
        form = RegisterForm()

    return render(request, 'recipes/register.html', {'form': form})


@never_cache
def registration_pending(request):
    return render(request, 'recipes/registration_pending.html', {
        'mail_state': request.session.get('registration_mail_state', 'sent'),
    })


@never_cache
@require_http_methods(['GET', 'POST'])
def confirm_email(request, user_id, token):
    candidates = User.objects.filter(
        pk=user_id,
        is_active=False,
        email_confirmation_requested_at__isnull=False,
    )
    user = candidates.first()
    valid = user is not None and confirmation_matches(user, token)
    confirmed = False
    if valid and request.method == 'POST':
        confirmed = bool(candidates.filter(email=user.email, date_joined=user.date_joined).update(
            is_active=True,
            email_confirmation_requested_at=None,
        ))
        valid = False

    response = render(request, 'recipes/confirm_email.html', {
        'valid': valid,
        'confirmed': confirmed,
    })
    # Send the origin for HTTPS CSRF checks without exposing the token in the URL.
    response['Referrer-Policy'] = 'strict-origin'
    return response


@never_cache
@require_http_methods(['GET', 'POST'])
def resend_confirmation(request):
    form = ResendConfirmationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        if 'registration' not in settings.MAILERS:
            form.add_error(None, 'Отправка писем пока недоступна. Попробуй позже.')
        else:
            now = timezone.now()
            candidates = User.objects.filter(
                username=form.cleaned_data['username'],
                email__iexact=form.cleaned_data['email'],
                is_active=False,
                email_confirmation_requested_at__lt=now - RESEND_DELAY,
            )
            user = candidates.first()
            mail_state = 'resent'
            if user and candidates.filter(pk=user.pk).update(email_confirmation_requested_at=now):
                sent = send_confirmation(request, user)
                if user.pk == request.session.get('pending_registration_id'):
                    mail_state = 'sent' if sent else 'failed'

            request.session['registration_mail_state'] = mail_state
            return redirect('registration_pending')

    return render(request, 'recipes/resend_confirmation.html', {'form': form})


def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username, email_confirmation_requested_at__isnull=True)
    is_own = request.user == user_obj

    # Определяем активную вкладку
    tab = request.GET.get('tab', 'recipes')
    if tab not in ('recipes', 'likes', 'favorites'):
        tab = 'recipes'

    # Избранное — только для владельца
    if tab == 'favorites' and not is_own:
        tab = 'recipes'

    # Загружаем данные в зависимости от вкладки
    if tab == 'likes':
        liked_ids = Like.objects.filter(user=user_obj).values_list('recipe_id', flat=True)
        items = Recipe.objects.filter(id__in=liked_ids).order_by('-created_at')
    elif tab == 'favorites':
        fav_ids = Favorite.objects.filter(user=user_obj).values_list('recipe_id', flat=True)
        items = Recipe.objects.filter(id__in=fav_ids).order_by('-created_at')
    else:
        items = Recipe.objects.filter(author=user_obj).order_by('-created_at')

    counts = {
        'recipes': user_obj.recipes.count(),
        'likes': Like.objects.filter(user=user_obj).count(),
    }
    if is_own:
        counts['favorites'] = Favorite.objects.filter(user=user_obj).count()

    context = {
        'profile_user': user_obj,
        'items': items,
        'tab': tab,
        'is_own': is_own,
        'counts': counts,
    }
    if not _wants_fragment(request):
        context.update(
            achievement_preview=achievements.preview(user_obj),
            is_subscribed=request.user.is_authenticated and not is_own
            and user_obj.subscribers.filter(subscriber=request.user).exists(),
            subscribers_count=user_obj.subscribers.count(),
        )
    return _render_section(request, 'recipes/profile.html', 'profile_tabs', context)


def profile_achievements(request, username):
    profile_user = get_object_or_404(User, username=username, email_confirmation_requested_at__isnull=True)
    is_own = request.user == profile_user
    return render(request, 'recipes/achievements.html', {
        'profile_user': profile_user,
        'is_own': is_own,
        'collection': achievements.collection(profile_user, is_own),
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = UserForm(instance=request.user)

    return render(request, 'recipes/profile_edit.html', {'form': form})


def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    comments_context = _recipe_comments(request, recipe)
    if _wants_fragment(request):
        return _render_section(request, 'recipes/recipe_detail.html', 'comments', comments_context)

    # Уникальный просмотр
    viewed = request.session.get('viewed_recipes', [])
    if recipe.id not in viewed:
        recipe.views_count += 1
        recipe.save(update_fields=['views_count'])
        viewed.append(recipe.id)
        request.session['viewed_recipes'] = viewed

    ingredients = recipe.ingredients.select_related('ingredient').all()

    is_favorite = False
    is_liked = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, recipe=recipe).exists()
        is_liked = Like.objects.filter(user=request.user, recipe=recipe).exists()

    user_rating = recipe.user_rating(request.user) if request.user.is_authenticated else 0
    avg_rating = recipe.average_rating()
    ratings_count = recipe.ratings_count()
    servings = recipe.servings or 1
    nutrition = [
        (label, value, value * servings if value is not None else None)
        for label, value in (
            ('ккал', recipe.calories),
            ('белки (г)', recipe.proteins),
            ('жиры (г)', recipe.fats),
            ('углеводы (г)', recipe.carbs),
        )
    ]

    return _render_section(request, 'recipes/recipe_detail.html', 'comments', {
        **comments_context,
        'show_comment_form': True,
        'recipe': recipe,
        'ingredients': ingredients,
        'is_favorite': is_favorite,
        'is_liked': is_liked,
        'likes_count': recipe.likes.count(),
        'user_rating': user_rating,
        'avg_rating': avg_rating,
        'ratings_count': ratings_count,
        'servings': servings,
        'nutrition': nutrition if any(value is not None for _, value, _ in nutrition) else [],
    })


def _recipe_comments(request, recipe):
    sort = 'likes' if request.GET.get('sort') == 'likes' else 'date'
    ordering = ('-likes_count', '-created_at', '-pk') if sort == 'likes' else ('-created_at', '-pk')
    comments = recipe.comments.select_related('user').annotate(
        likes_count=Count('votes', filter=Q(votes__vote_type='like')),
        dislikes_count=Count('votes', filter=Q(votes__vote_type='dislike')),
    ).order_by(*ordering)
    user_votes = {}
    if request.user.is_authenticated:
        user_votes = dict(CommentVote.objects.filter(
            user=request.user, comment__recipe=recipe,
        ).values_list('comment_id', 'vote_type'))

    comments_data = [
        {'comment': comment, 'likes': comment.likes_count, 'dislikes': comment.dislikes_count,
         'user_vote': user_votes.get(comment.pk)}
        for comment in comments
    ]
    return {'comments_data': comments_data, 'comments_count': len(comments_data), 'sort': sort}


@require_POST
def toggle_favorite(request, recipe_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)

    recipe = get_object_or_404(Recipe, id=recipe_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'added'})


@require_POST
def toggle_like(request, recipe_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)

    recipe = get_object_or_404(Recipe, id=recipe_id)
    like, created = Like.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        like.delete()
        return JsonResponse({'status': 'removed', 'count': recipe.likes.count()})

    if recipe.author != request.user:
        achievements.grant(recipe.author, 'likes_total', 'likes_best')

    return JsonResponse({'status': 'added', 'count': recipe.likes.count()})


@require_POST
def add_comment(request, recipe_id):
    if not request.user.is_authenticated:
        return redirect('login')

    recipe = get_object_or_404(Recipe, id=recipe_id)
    content = request.POST.get('content', '').strip()

    if content:
        Comment.objects.create(user=request.user, recipe=recipe, content=content)
        achievements.grant(request.user, 'comments')

    return redirect('recipe_detail', slug=recipe.slug)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'recipes/category_list.html', {'categories': categories})




@require_POST
def rate_recipe(request, recipe_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)
    try:
        value = int(request.POST.get('value', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'invalid_value'}, status=400)
    if not (1 <= value <= 5):
        return JsonResponse({'error': 'out_of_range'}, status=400)
    recipe = get_object_or_404(Recipe, id=recipe_id)
    _, created = Rating.objects.update_or_create(
        user=request.user,
        recipe=recipe,
        defaults={'value': value}
    )
    unlocked = created and request.user != recipe.author and achievements.grant(request.user, 'ratings')
    return JsonResponse({
        'status': 'ok',
        'user_rating': value,
        'avg_rating': recipe.average_rating(),
        'ratings_count': recipe.ratings_count(),
        'awards': achievements.notification_data(request.user) if unlocked else [],
    })


def random_recipe(request):
    recipe = Recipe.objects.order_by('?').first()
    if recipe:
        return redirect('recipe_detail', slug=recipe.slug)
    return redirect('home')

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    difficulty = request.GET.get('difficulty', '')
    time_max = request.GET.get('time_max', '')
    sort = request.GET.get('sort', 'new')

    recipes = list(Recipe.objects.filter(category=category).select_related('author', 'category').prefetch_related('likes', 'ratings'))

    if difficulty in ('easy', 'medium', 'hard'):
        recipes = [r for r in recipes if r.difficulty == difficulty]
    if time_max and time_max.isdigit():
        recipes = [r for r in recipes if r.cooking_time <= int(time_max)]

    if sort == 'rating':
        recipes = sorted(recipes, key=lambda r: r.average_rating(), reverse=True)
    elif sort == 'likes':
        recipes = sorted(recipes, key=lambda r: r.likes.count(), reverse=True)
    elif sort == 'views':
        recipes = sorted(recipes, key=lambda r: r.views_count, reverse=True)
    elif sort == 'time_asc':
        recipes = sorted(recipes, key=lambda r: r.cooking_time)
    elif sort == 'time_desc':
        recipes = sorted(recipes, key=lambda r: r.cooking_time, reverse=True)
    else:
        recipes = sorted(recipes, key=lambda r: r.created_at, reverse=True)

    return _render_section(request, 'recipes/category_detail.html', 'category_results', {
        'category': category,
        'recipes': recipes,
        'selected_difficulty': difficulty,
        'time_max': time_max,
        'sort': sort,
        'has_filters': any([difficulty, time_max, sort != 'new']),
    })

@login_required
def recipe_add(request):
    return _recipe_form(request)


@login_required
def recipe_edit(request, slug):
    return _recipe_form(request, slug)


def _recipe_form(request, slug=None):
    editing = slug is not None
    submitting = request.method == 'POST'
    data = request.POST if submitting else None
    files = request.FILES if submitting else None
    uploaded_photo = None

    try:
        with transaction.atomic() if submitting else nullcontext():
            if editing:
                recipes = Recipe.objects.select_for_update() if submitting else Recipe.objects.all()
                recipe = get_object_or_404(recipes, slug=slug, author=request.user)
            else:
                recipe = Recipe(author=request.user)

            photo_url = recipe.image.url if recipe.image else ''
            form = RecipeForm(data, files, instance=recipe)
            formset = RecipeIngredientFormSet(
                data,
                instance=recipe,
                error_messages={'too_few_forms': 'Добавь хотя бы один ингредиент.'},
            )
            saved = submitting and form.is_valid() and formset.is_valid()
            if saved:
                recipe = form.save(commit=False)
                if 'image' in form.changed_data:
                    photo = form.cleaned_data['image']
                    recipe.image.save(photo.name, photo, save=False)
                    uploaded_photo = recipe.image

                recipe.save(update_fields=form.changed_data if editing else None)
                formset.save()
                if not editing or {'category', 'image'}.intersection(form.changed_data):
                    achievements.grant(request.user, 'recipes', 'photos', 'categories')
    except Exception:
        # File storage does not roll back with the database transaction.
        if uploaded_photo:
            uploaded_photo.storage.delete(uploaded_photo.name)
        raise

    if saved:
        return redirect('recipe_detail', slug=recipe.slug)

    return render(request, 'recipes/recipe_add.html', {
        'form': form,
        'formset': formset,
        'editing': editing,
        'recipe': recipe,
        'photo_url': photo_url,
    })

@require_POST
def vote_comment(request, comment_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)

    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get('vote_type')

    if vote_type not in ('like', 'dislike'):
        return JsonResponse({'error': 'invalid'}, status=400)

    existing = CommentVote.objects.filter(user=request.user, comment=comment).first()

    if existing:
        if existing.vote_type == vote_type:
            # Убираем голос
            existing.delete()
            user_vote = None
        else:
            # Меняем голос
            existing.vote_type = vote_type
            existing.save()
            user_vote = vote_type
    else:
        CommentVote.objects.create(user=request.user, comment=comment, vote_type=vote_type)
        user_vote = vote_type

    likes = comment.votes.filter(vote_type='like').count()
    dislikes = comment.votes.filter(vote_type='dislike').count()

    unlocked = existing is None and achievements.grant(request.user, 'votes')

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'user_vote': user_vote,
        'awards': achievements.notification_data(request.user) if unlocked else [],
    })

@require_POST
def toggle_subscription(request, username):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)

    author = get_object_or_404(User, username=username, email_confirmation_requested_at__isnull=True)

    if author == request.user:
        return JsonResponse({'error': 'cant_subscribe_self'}, status=400)

    sub, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        author=author
    )

    unlocked = 0
    if not created:
        sub.delete()
        status = 'removed'
    else:
        status = 'added'
        achievements.grant(author, 'followers')
        unlocked = achievements.grant(request.user, 'following')

    return JsonResponse({
        'status': status,
        'count': author.subscribers.count(),
        'awards': achievements.notification_data(request.user) if unlocked else [],
    })

def feed(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Кто на кого подписан
    subscribed_authors = Subscription.objects.filter(
        subscriber=request.user
    ).values_list('author_id', flat=True)

    # Рецепты от этих авторов
    recipes = Recipe.objects.filter(
        author_id__in=subscribed_authors
    ).select_related('author', 'category').order_by('-created_at')

    return render(request, 'recipes/feed.html', {
        'recipes': recipes,
        'authors_count': len(subscribed_authors),
    })

def leaderboard(request):
    tab = request.GET.get('tab', 'subscribers')
    if tab not in ('subscribers', 'likes', 'views'):
        tab = 'subscribers'

    if tab == 'likes':
        # Считаем лайки через аннотацию
        users = User.objects.annotate(
            score=Count('recipes__likes')
        ).filter(score__gt=0).order_by('-score')[:50]
    elif tab == 'views':
        users = User.objects.annotate(
            score=Sum('recipes__views_count')
        ).filter(score__gt=0).order_by('-score')[:50]
    else:  # subscribers
        users = User.objects.annotate(
            score=Count('subscribers')
        ).filter(score__gt=0).order_by('-score')[:50]

    # Прокачиваем данными для карточек
    leaders = []
    for i, u in enumerate(users, start=1):
        leaders.append({
            'rank': i,
            'user': u,
            'score': u.score,
        })

    return _render_section(request, 'recipes/leaderboard.html', 'leaderboard_tabs', {
        'leaders': leaders,
        'tab': tab,
    })


def search_recipes(request):
    query = request.GET.get('q', '').strip()
    name = request.GET.get('name', '').strip()
    category_id = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    time_max = request.GET.get('time_max', '')
    all_ingredients = bool(query) and request.GET.get('all') == '1'
    default_sort = 'match' if query else 'new'
    orderings = {
        'new': ('-created_at', '-pk'),
        'rating': ('-catalog_rating', '-created_at', '-pk'),
        'likes': ('-catalog_likes', '-created_at', '-pk'),
        'views': ('-views_count', '-created_at', '-pk'),
        'time_asc': ('cooking_time', '-pk'),
        'time_desc': ('-cooking_time', '-pk'),
    }
    sort = request.GET.get('sort', default_sort)
    if sort not in orderings and not (sort == 'match' and query):
        sort = default_sort

    recipes = Recipe.objects.annotate(
        catalog_rating=Avg('ratings__value'),
        catalog_likes=Count('likes', distinct=True),
    ).order_by(*orderings.get(sort, orderings['new']))
    if category_id.isascii() and category_id.isdecimal() and len(category_id) <= 19:
        category_pk = int(category_id)
        recipes = recipes.filter(category_id=category_pk) if category_pk < 2**63 else recipes.none()
    if difficulty in dict(Recipe.DIFFICULTY_CHOICES):
        recipes = recipes.filter(difficulty=difficulty)
    if time_max.isascii() and time_max.isdecimal() and len(time_max) <= 10:
        recipes = recipes.filter(cooking_time__lte=int(time_max))

    found_ingredients, unknown_ingredients = {}, {}
    if query:
        found_ingredients, unknown_ingredients = match_ingredients(query)
        if found_ingredients:
            matched_recipes = RecipeIngredient.objects.filter(
                ingredient_id__in=found_ingredients
            ).values('recipe_id')
            recipes = recipes.filter(pk__in=matched_recipes).prefetch_related('ingredients__ingredient')
        else:
            recipes = recipes.none()

    # SQLite's case-insensitive lookup does not handle Cyrillic.
    if name:
        term = normalize(name)
        recipes = [recipe for recipe in recipes if term in normalize(recipe.title)
                   or term in normalize(recipe.description)]

    if query and found_ingredients:
        matches = []
        for recipe in recipes:
            ingredients = {row.ingredient_id: row.ingredient.name for row in recipe.ingredients.all()}
            missing = [label for pk, label in ingredients.items() if pk not in found_ingredients]
            if all_ingredients and missing:
                continue
            recipe.total_count = len(ingredients)
            recipe.matched_count = recipe.total_count - len(missing)
            recipe.match_ratio = recipe.matched_count / recipe.total_count
            recipe.match_percent = min(99, round(100 * recipe.match_ratio)) if missing else 100
            recipe.missing = missing
            matches.append(recipe)
        recipes = matches
        if sort == 'match':
            recipes.sort(key=lambda recipe: (recipe.match_ratio, recipe.matched_count), reverse=True)

    paginator = Paginator(recipes, 12)
    filters_open = any([name, category_id, difficulty, time_max, sort != default_sort])
    return _render_section(request, 'recipes/search.html', 'catalog_results', {
        'query': query,
        'name': name,
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'time_max': time_max,
        'sort': sort,
        'all_ingredients': all_ingredients,
        'found_ingredients': found_ingredients.values(),
        'unknown_ingredients': unknown_ingredients,
        'ingredient_suggestions': ingredient_suggestions(),
        'page_obj': paginator.get_page(request.GET.get('page')),
        'results_count': paginator.count,
        'categories': Category.objects.all(),
        'filters_open': filters_open,
        'has_filters': bool(query) or filters_open,
    })
