from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review, App


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['username', 'comment', 'stars', 'recommended']
        labels = {
            'username': 'Ваше имя',
            'comment': 'Комментарий',
            'stars': 'Оценка (1–5)',
            'recommended': 'Рекомендую это приложение',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Как вас зовут?',
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Что понравилось или не понравилось?',
            }),
            'stars': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
            }),
        }

    def clean_stars(self):
        stars = self.cleaned_data['stars']
        if stars < 1 or stars > 5:
            raise forms.ValidationError('Оценка должна быть от 1 до 5.')
        return stars


class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'description', 'price', 'category', 'icon']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
            'category': 'Категория',
            'icon': 'Иконка',
        }


class ForSuperUserEditAppForm(AppForm):
    class Meta(AppForm.Meta):
        fields = ['name', 'description', 'price', 'category', 'icon', 'author']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['author'].label = 'Автор'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Повтор пароля"

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Аккаунт с такой почтой уже существует')
        return email
