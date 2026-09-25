from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, Ingredient, Recipe, RecipeIngredient,
    Favorite, Rating, Comment, Achievement, UserAchievement, Like, CommentVote
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar', 'bio')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 3


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'cooking_time', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [RecipeIngredientInline]


admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Favorite)
admin.site.register(Rating)
admin.site.register(Comment)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'code', 'category', 'is_hidden', 'order')
    list_filter = ('category', 'is_hidden')
    search_fields = ('name', 'code')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')
    list_filter = ('achievement',)
    search_fields = ('user__username', 'achievement__name')