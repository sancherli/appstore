from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
       return self.name

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'

class App(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, default='')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    downloads = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'

class Review(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    username = models.CharField(max_length=50)
    comment = models.TextField(blank=True)
    email = models.EmailField(max_length=100)
    rating = models.PositiveIntegerField()
    stars = models.PositiveIntegerField(default=5)
    recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} > {self.app.name}"