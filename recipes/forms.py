from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import User, Recipe, RecipeIngredient


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Электронная почта')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['password1'].help_text = ' '.join(password_validators_help_texts())
        self.fields['password2'].help_text = ''


class ResendConfirmationForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'username'}),
    )
    email = forms.EmailField(
        label='Электронная почта',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
    )


class ProfileImageInput(forms.ClearableFileInput):
    template_name = 'recipes/widgets/profile_image.html'

    def __init__(self, clear_checkbox_label):
        super().__init__()
        self.clear_checkbox_label = clear_checkbox_label


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar', 'banner', 'bio', 'nickname_style']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'avatar': 'Аватар',
            'banner': 'Баннер',
            'bio': 'О себе',
            'nickname_style': 'Стиль ника',
        }
        help_texts = {
            'avatar': 'Квадратное фото',
            'banner': 'Широкое фото',
            'bio': f"До {User._meta.get_field('bio').max_length} символов",
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
            'avatar': ProfileImageInput('Удалить аватар'),
            'banner': ProfileImageInput('Удалить баннер'),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Расскажи о себе...'}),
            'nickname_style': forms.Select(attrs={'class': 'form-input'}),
        }


class RecipeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Выбери'
        if self.instance.pk and self.instance.category_id is None:
            self.fields['category'].required = False

    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'category', 'image',
            'cooking_time', 'servings', 'difficulty',
            'calories', 'proteins', 'fats', 'carbs',
            'steps'
        ]
        labels = {
            'title': 'Название',
            'description': 'Краткое описание',
            'category': 'Категория',
            'image': 'Фото блюда',
            'cooking_time': 'Время (мин)',
            'servings': 'Порции',
            'difficulty': 'Сложность',
            'calories': 'Калории (ккал)',
            'proteins': 'Белки (г)',
            'fats': 'Жиры (г)',
            'carbs': 'Углеводы (г)',
            'steps': 'Приготовление',
        }
        help_texts = {
            'cooking_time': '',
            'calories': '',
            'proteins': '',
            'fats': '',
            'carbs': '',
            'steps': 'Пиши каждый шаг с новой строки. В рецепте шаги пронумеруются автоматически.',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например, куриный суп'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'image': forms.FileInput(),
            'cooking_time': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '30'}),
            'servings': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2'}),
            'difficulty': forms.Select(attrs={'class': 'form-input'}),
            'calories': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'proteins': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'fats': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'carbs': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'steps': forms.Textarea(attrs={'rows': 6, 'class': 'form-input'}),
        }


class IngredientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, ingredient):
        return f'{ingredient.name} ({ingredient.unit})'


class RecipeIngredientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].empty_label = 'Выбери'

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']
        field_classes = {'ingredient': IngredientChoiceField}
        labels = {'ingredient': 'Ингредиент', 'quantity': 'Количество'}
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '100'}),
        }


class BaseRecipeIngredientFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        existing_ids = {ingredient.pk for ingredient in self.get_queryset()}
        submitted_ids = [form.instance.pk for form in self.initial_forms]
        if len(submitted_ids) != len(existing_ids) or set(submitted_ids) != existing_ids:
            raise forms.ValidationError('Список ингредиентов изменился. Открой форму заново.')


RecipeIngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    formset=BaseRecipeIngredientFormSet,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
