from django.db.models import Count
from django.http import request

from .models import App, Category


def store_menu(request):
    categories = list(
        Category.objects
        .annotate(apps_count=Count('app'))
        .order_by('name')
    )
    return {
        'categories': categories,
        'apps_total': App.objects.count(),
        'categories_total': len(categories),
    }