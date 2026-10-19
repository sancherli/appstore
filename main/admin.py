from django.contrib import admin
from .models import Category, App, Review, Purchase

admin.site.register(Category)


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'author', 'created_at', 'rating_avg', 'rating_count')
    search_fields = ('name', 'description')
    list_filter = ('category',)
    filter_horizontal = ('favorited_by',)


admin.site.register(Review)


@admin.register(Purchase)
class AppAdmin(admin.ModelAdmin):
    list_display = ('user', 'app', 'price_paid', 'purchased_at')
    search_fields = ('app', 'user')
