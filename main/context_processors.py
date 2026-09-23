from django.db.models import Count
from django.http import request
from .models import Category, App, Review


def store_menu(request):
    categories = list(
        Category.objects
        .annotate(apps_count=Count('app'))
        .order_by('name')
    )

    return {
        'categories': Category.objects.all(),
        'category_total': Category.objects.count(),
        'apps_total': App.objects.count(),
        'reviews_total': Review.objects.count(),
    }