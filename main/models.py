from decimal import Decimal, ROUND_HALF_UP
from math import factorial

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
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


class AppQuerySet(models.QuerySet):
    def free(self):
        return self.filter(price=0)

    def paid(self):
        return self.filter(price__gt=0)

    def cheap(self):
        return self.filter(price__lt=100).order_by('-price')

    def newest(self):
        return self.order_by('-created_at')

    def in_category(self, category):
        return self.filter(category=category)


class AppManager(models.Manager.from_queryset(AppQuerySet)):
    def move_to_category(self,source,target):
        if source.pk is None or target.pk is None or source.pk == target.pk:
            raise ValueError("Нельзя перенести приложение в ту же категорию")
        with transaction.atomic():
            moved = self.model.objects.in_category(source).uodate(category=target)
            source.delete()
        return moved


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

    buyers = models.ManyToManyField(
        User,
        through='Purchase',
        related_name='purchased_apps',
        verbose_name='Купили',
    )
    objects = AppManager()

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

    def purchase_of(self, user):
        if not user.is_authenticated:
            return None
        return self.purchases.filter(user=user).first()


    @classmethod
    def discount_paid(cls, percent):
        if type(percent) is not int or not 1 <= percent <= 90:
            raise ValueError('Скидка должна быть целым числом от 1 до 90.')
        factor = (Decimal(100) - Decimal(percent)) / Decimal(100)
        paid = list(cls.objects.paid())
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


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='purchases')
    price_paid = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[validate_not_negative_price],
        verbose_name='Оплачено',
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'app'], name='unique_purchase_user_app'),
        ]

    def __str__(self):
        return f'{self.user} → {self.app}'

    def purchase_of(self, user):
        if not user.is_authenticated:
            return None
        return self.purchase.filter(user=user).first()

    def price_label(self):
        if self.price_paid == 0:
            return 'Бесплатно'
        return f'{self.price_paid} $'
