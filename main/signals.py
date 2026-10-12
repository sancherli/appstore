from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import App, Review


def refresh_app_rating(app_id):
    stats = Review.objects.filter(app_id=app_id).aggregate(
        avg=Avg('stars'),
        total=Count('id'),
    )
    total = stats['total'] or 0
    if stats['avg'] is None:
        rating = Decimal('0.0')
    else:
        rating = Decimal(str(stats['avg'])).quantize(
            Decimal('0.1'),
            rounding=ROUND_HALF_UP,
        )
    App.objects.filter(pk=app_id).update(
        rating_avg=rating,
        rating_count=total,
    ),


@receiver(post_save, sender=Review, dispatch_uid='main.review_saved_refresh_rating')
def review_saved(sender, instance, **kwargs):
    refresh_app_rating(instance.app_id)


@receiver(post_delete, sender=Review, dispatch_uid='main.review_deleted_refresh_rating')
def review_deleted(sender, instance, **kwargs):
    refresh_app_rating(instance.app_id)


