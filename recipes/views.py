from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.db.models import Count, Q
from .forms import RegisterForm, UserForm, RecipeForm, RecipeIngredientForm
from .models import (
    User, Category, Ingredient, Recipe,
    RecipeIngredient, Favorite, Rating, Comment, Like, CommentVote
)

def home(request):
    recipes = Recipe.objects.order_by('-created_at')[:8]
    categories = Category.objects.all()[:8]
    return render(request, 'recipes/home.html', {
        'recipes': recipes,
        'categories': categories,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'recipes/register.html', {'form': form})


def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
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

    # Счётчики для вкладок
    counts = {
        'recipes': Recipe.objects.filter(author=user_obj).count(),
        'likes': Like.objects.filter(user=user_obj).count(),
        'favorites': Favorite.objects.filter(user=user_obj).count(),
    }

    return render(request, 'recipes/profile.html', {
        'profile_user': user_obj,
        'items': items,
        'tab': tab,
        'is_own': is_own,
        'counts': counts,
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

    # Уникальный просмотр
    viewed = request.session.get('viewed_recipes', [])
    if recipe.id not in viewed:
        recipe.views_count += 1
        recipe.save(update_fields=['views_count'])
        viewed.append(recipe.id)
        request.session['viewed_recipes'] = viewed

    ingredients = recipe.ingredients.select_related('ingredient').all()

    # === СОРТИРОВКА КОММЕНТАРИЕВ ===
    sort = request.GET.get('sort', 'date')
    if sort == 'likes':
        comments = recipe.comments.select_related('user').annotate(
            likes_count=Count('votes', filter=Q(votes__vote_type='like'))
        ).order_by('-likes_count', '-created_at')
    else:
        comments = recipe.comments.select_related('user').order_by('-created_at')

    # Прокачиваем каждый комментарий данными о лайках/дизлайках
    user_votes = {}
    if request.user.is_authenticated:
        votes = CommentVote.objects.filter(
            user=request.user,
            comment__recipe=recipe
        ).values_list('comment_id', 'vote_type')
        user_votes = dict(votes)

    comments_data = []
    for comment in comments:
        likes = comment.votes.filter(vote_type='like').count()
        dislikes = comment.votes.filter(vote_type='dislike').count()
        comments_data.append({
            'obj': comment,
            'likes': likes,
            'dislikes': dislikes,
            'user_vote': user_votes.get(comment.id),
        })

    is_favorite = False
    is_liked = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, recipe=recipe).exists()
        is_liked = Like.objects.filter(user=request.user, recipe=recipe).exists()

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'comments_data': comments_data,
        'comments_count': len(comments_data),
        'is_favorite': is_favorite,
        'is_liked': is_liked,
        'likes_count': recipe.likes.count(),
        'sort': sort,
    })


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

    return JsonResponse({'status': 'added', 'count': recipe.likes.count()})


@require_POST
def add_comment(request, recipe_id):
    if not request.user.is_authenticated:
        return redirect('login')

    recipe = get_object_or_404(Recipe, id=recipe_id)
    content = request.POST.get('content', '').strip()

    if content:
        Comment.objects.create(user=request.user, recipe=recipe, content=content)

    return redirect('recipe_detail', slug=recipe.slug)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'recipes/category_list.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    recipes = Recipe.objects.filter(category=category).order_by('-created_at')
    return render(request, 'recipes/category_detail.html', {
        'category': category,
        'recipes': recipes,
    })

def recipe_add(request):
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/recipe/add/')

    RecipeIngredientFormSet = inlineformset_factory(
        Recipe,
        RecipeIngredient,
        form=RecipeIngredientForm,
        extra=3,
        can_delete=True,
        min_num=1,
        validate_min=True,
    )

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        formset = RecipeIngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            formset.instance = recipe
            formset.save()
            return redirect('recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm()
        formset = RecipeIngredientFormSet()

    return render(request, 'recipes/recipe_add.html', {
        'form': form,
        'formset': formset,
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

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'user_vote': user_vote,
    })