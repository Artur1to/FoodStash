from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Авторизация
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='recipes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Профили
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),

    path('recipe/<int:recipe_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('recipe/<int:recipe_id>/like/', views.toggle_like, name='toggle_like'),
    path('recipe/<int:recipe_id>/comment/', views.add_comment, name='add_comment'),

    path('recipe/add/', views.recipe_add, name='recipe_add'),
    path('recipe/<slug:slug>/', views.recipe_detail, name='recipe_detail'),

    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
]