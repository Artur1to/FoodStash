from django import template

from recipes.achievements import take_notifications

register = template.Library()


@register.simple_tag
def achievement_notifications(request):
    if request.method == 'GET' and request.user.is_authenticated:
        return take_notifications(request.user)
    return []
