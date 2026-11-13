from django import template

register = template.Library()


@register.filter
def category_icon(category):
    icons = {
        'salatiki': '🥗',
        'sosiskisiski': '🍲',
        'zavtraki': '🍳',
        'osnovnye-blyuda': '🍛',
        'pasta': '🍝',
        'zakuski': '🥙',
        'vypechka': '🥐',
        'deserty': '🍰',
        'napitki': '🍋',
    }
    return icons.get(category.slug, '🍽️')
