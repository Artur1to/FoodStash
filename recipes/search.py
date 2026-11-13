import re

from django.db.models import Count

from .models import Ingredient


INGREDIENT_ALIASES = {
    variant: name
    for name, variants in {
        'картофель': ('картофеля', 'картошка', 'картошку', 'картошки', 'картошечка'),
        'лук': ('лука', 'луком', 'лучок', 'лучек'),
        'помидор': ('помидоры', 'помидоров', 'томат', 'томаты', 'помидорчик'),
        'чеснок': ('чеснока', 'чесноком', 'чесночек'),
        'яйцо': ('яйца', 'яиц', 'яйцом'),
        'курица': ('курицу', 'курицы', 'курицей'),
        'макароны': ('макарон', 'макаронами'),
        'сыр': ('сыра', 'сыром'),
    }.items()
    for variant in variants
}


def ingredient_suggestions():
    return Ingredient.objects.annotate(uses=Count('recipeingredient')).filter(
        uses__gt=0
    ).order_by('-uses', 'name', 'pk')[:6]


def normalize(text):
    return text.casefold().replace('ё', 'е')


def match_ingredients(query):
    by_name = {}
    for ingredient in Ingredient.objects.order_by('name', 'pk'):
        name = ' '.join(normalize(ingredient.name).split())
        by_name.setdefault(name, []).append(ingredient)

    by_alias = {}
    for name, ingredients in by_name.items():
        key = INGREDIENT_ALIASES.get(name, name)
        by_alias.setdefault(key, []).extend(ingredients)

    found = {}
    unknown = {}
    phrases = sorted((name for name in by_name if ' ' in name), key=len, reverse=True)
    names = '|'.join(re.escape(phrase) for phrase in phrases)
    terms = re.compile(rf'(?:{names})(?=\s|$)|\S+' if names else r'\S+')
    for part in re.split(r'[,;\n]+', query):
        for match in terms.finditer(' '.join(normalize(part).split())):
            term = match.group()
            matches = by_name.get(term) or by_alias.get(INGREDIENT_ALIASES.get(term, term))
            if matches:
                found.update((ingredient.pk, ingredient) for ingredient in matches)
            else:
                unknown[term] = None

    return found, unknown
