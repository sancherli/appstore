from decimal import Decimal, ROUND_HALF_UP
from math import factorial

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

def validate_not_negative_price(value):
    if value < 0:
        raise ValidationError('Цена не может быть отрицательной')


class Category(models.Model):
    name = models.CharField(max_length=50)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
       return self.name

    def get_absolute_url(self):
        return reverse(
            'main:category',
            kwargs={'category_id': self.id}
        )

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'


class App(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[validate_not_negative_price])
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    icon = models.ImageField(upload_to='icons/', blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='apps',)
    favorited_by = models.ManyToManyField(User, related_name='favorite_apps', blank=True, verbose_name='В избранном у')
    rating_avg = models.DecimalField(max_digits=2,decimal_places=1,default=0,editable=False,verbose_name='Средняя оценка',)
    rating_count = models.PositiveIntegerField(default=0,editable=False,verbose_name='Число оценок',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:app_detail', kwargs={'app_id': self.pk})

    def price_label(self):
        if self.price == 0:
            return 'Бесплатно'
        return f'{self.price} $'

    def similar_by_price(self):
        return App.objects.filter(
            price__gte=self.price - 10,
            price__lte=self.price + 10,
        ).exclude(pk=self.pk)[:3]

    @classmethod
    def discount_paid(cls, percent):
        if type(percent) is not int or not 1 <= percent <= 90:
            raise ValueError('Скидка должна быть целым числом от 1 до 90.')
        factor = (Decimal(100) - Decimal(percent)) / Decimal(100)
        paid = list(cls.objects.filter(price__gt=0))
        for app in paid:
            app.price = (app.price * factor).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
        return cls.objects.bulk_update(paid, ['price'])


    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'


class Review(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    username = models.CharField(max_length=50)
    comment = models.TextField(blank=True)
    stars = models.PositiveSmallIntegerField(
        default=5,
        validators=[
            MinValueValidator(1, message='Оценка должна быть от 1 до 5.'),
            MaxValueValidator(5, message='Оценка должна быть от 1 до 5.'),
        ],
    )
    recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.username} → {self.app.name}'
