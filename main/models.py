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
    name = models.CharField(max_length=100)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    recommended = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} → {self.app.name}"