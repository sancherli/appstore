from django import forms
from .models import Review, App

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['username', 'comment', 'stars', 'rating', 'recommended']
        labels = {
            'username': 'Your name',
            'comment': 'Text here',
            'stars': 'Mark',
            'rating': 'Rating',
            'recommended': 'Do you recommended this app'
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Как вас зовут?',
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Что вам понравилось или не понравилось',
            }),
            'stars': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
            }),
        }

    def clean_stars(self):
        stars = self.cleaned_data['stars']
        if stars < 1 or stars > 5:
            raise forms.ValidationError('Оценка должна быть от 1 до 5')
        return stars


class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'description', 'price', 'category', 'icon']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена (0 = бесплатно)',
            'category': 'Категория',
            'icon': 'Иконка',
        }

