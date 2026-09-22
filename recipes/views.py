from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from .forms import RegisterForm, UserForm, RecipeForm, RecipeIngredientForm
from .models import (
    User, Category, Ingredient, Recipe,
    RecipeIngredient, Favorite, Rating, Comment
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
    recipes = Recipe.objects.filter(author=user_obj).order_by('-created_at')
    is_own = request.user == user_obj

    return render(request, 'recipes/profile.html', {
        'profile_user': user_obj,
        'recipes': recipes,
        'is_own': is_own,
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

    # Увеличиваем счётчик просмотров
    recipe.views_count += 1
    recipe.save(update_fields=['views_count'])

    ingredients = recipe.ingredients.select_related('ingredient').all()
    comments = recipe.comments.select_related('user').order_by('-created_at')

    # Проверяем, в избранном ли у текущего пользователя
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, recipe=recipe).exists()

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'comments': comments,
        'is_favorite': is_favorite,
    })

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