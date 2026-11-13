from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from .passwords import AccountPasswordChangeForm, AccountPasswordResetConfirmView, AccountPasswordResetView

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', TemplateView.as_view(template_name='recipes/info/about.html', extra_context={'page_title': 'О проекте'}), name='about'),
    path('privacy/', TemplateView.as_view(template_name='recipes/info/privacy.html', extra_context={'page_title': 'Конфиденциальность'}), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='recipes/info/terms.html', extra_context={'page_title': 'Правила пользования'}), name='terms'),
    path('cookies/', TemplateView.as_view(template_name='recipes/info/cookies.html', extra_context={'page_title': 'Файлы cookie'}), name='cookies'),

    # Авторизация
    path('register/', views.register_view, name='register'),
    path('register/pending/', views.registration_pending, name='registration_pending'),
    path('register/confirm/<int:user_id>/<str:token>/', views.confirm_email, name='confirm_email'),
    path('register/resend/', views.resend_confirmation, name='resend_confirmation'),
    path('login/', auth_views.LoginView.as_view(template_name='recipes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        form_class=AccountPasswordChangeForm,
        template_name='recipes/passwords/form.html',
        extra_context={
            'title': 'Смена пароля',
            'submit_label': 'Сменить пароль',
            'back_route': 'profile_edit',
            'back_label': 'К настройкам профиля',
        },
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='recipes/passwords/status.html',
        extra_context={
            'title': 'Пароль изменён',
            'action_route': 'profile_edit',
            'action_label': 'К настройкам профиля',
        },
    ), name='password_change_done'),
    path('password/reset/', AccountPasswordResetView.as_view(
        template_name='recipes/passwords/form.html',
        extra_context={
            'title': 'Восстановление пароля',
            'description': 'Введи почту, привязанную к аккаунту. На неё придёт ссылка для сброса пароля.',
            'submit_label': 'Отправить ссылку',
            'back_route': 'login',
            'back_label': 'Вернуться ко входу',
        },
    ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='recipes/passwords/status.html',
        extra_context={
            'title': 'Проверь почту',
            'description': 'Если к адресу привязан активный аккаунт, на него придёт ссылка для сброса пароля. Проверь папку «Спам», если письма нет во входящих.',
            'action_route': 'login',
            'action_label': 'Вернуться ко входу',
        },
    ), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', AccountPasswordResetConfirmView.as_view(
        template_name='recipes/passwords/form.html',
        extra_context={'title': 'Новый пароль', 'submit_label': 'Сохранить пароль'},
    ), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='recipes/passwords/status.html',
        extra_context={
            'title': 'Пароль обновлён',
            'description': 'Теперь можно войти с новым паролем.',
            'action_route': 'login',
            'action_label': 'Войти',
        },
    ), name='password_reset_complete'),

    path('feed/', views.feed, name='feed'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('user/<str:username>/subscribe/', views.toggle_subscription, name='toggle_subscription'),

    # Профили
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/achievements/', views.profile_achievements, name='profile_achievements'),
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # Случайный рецепт (должен быть ДО slug)
    path('recipe/random/', views.random_recipe, name='random_recipe'),

    path('recipe/add/', views.recipe_add, name='recipe_add'),
    path('recipe/<int:recipe_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('recipe/<int:recipe_id>/like/', views.toggle_like, name='toggle_like'),
    path('recipe/<int:recipe_id>/rate/', views.rate_recipe, name='rate_recipe'),
    path('recipe/<int:recipe_id>/comment/', views.add_comment, name='add_comment'),
    path('recipe/<slug:slug>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipe/<slug:slug>/', views.recipe_detail, name='recipe_detail'),

    path('comment/<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),

    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),

    path('search/', views.search_recipes, name='search_recipes'),
]
