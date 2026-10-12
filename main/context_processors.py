from django.db.models import Count

from .models import App, Category


def store_menu(request):
    categories = list(
        Category.objects
        .annotate(apps_count=Count('app'))
        .order_by('name')
    )
    favorites_count = 0
    if request.user.is_authenticated:
        favorites_count = request.user.favorite_apps.count()
    return {
        'categories': categories,
        'apps_total': App.objects.count(),
        'categories_total': len(categories),
        'favorites_count': favorites_count,
    }
