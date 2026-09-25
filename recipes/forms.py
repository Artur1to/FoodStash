from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar', 'banner', 'bio', 'nickname_style']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Расскажи о себе...'}),
            'nickname_style': forms.Select(attrs={'class': 'form-input'}),
        }


from .models import Recipe, RecipeIngredient


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'category', 'image', 'cooking_time', 'servings', 'difficulty', 'steps']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: Куриный суп'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-input', 'placeholder': 'Краткое описание (необязательно)'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'cooking_time': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '30'}),
            'servings': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2'}),
            'difficulty': forms.Select(attrs={'class': 'form-input'}),
            'steps': forms.Textarea(attrs={'rows': 8, 'class': 'form-input', 'placeholder': 'Опиши шаги приготовления. Каждый шаг — с новой строки.'}),
        }


class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-input ingredient-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '100', 'step': '0.1'}),
        }