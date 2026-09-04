from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
       return self.name

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'


class App(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
       return self.name

    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'


