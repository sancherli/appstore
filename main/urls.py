from django.urls import path, register_converter
from . import views
from .mainapp.converter import YearConverter

register_converter(YearConverter, 'yyyy')

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('reviews/', views.reviews, name='reviews'),
    path('top/', views.top_apps, name='top'),
    path('app/<int:app_id>/', views.AppsDetailView.as_view(), name='app_detail'),
    path('app/<int:app_id>/review/', views.add_review, name='add_review'),

    path('new/', views.new, name='new'),

    path('no_category/', views.no_category, name='no_category'),
    path('free/<int:category_id>/', views.free_by_category, name='free_by_category'),
    path('cheap/', views.cheap_apps, name='cheap'),
    path('free/',views.AppsListView.as_view(),{'is_free': True},name='free'),
    path('paid-apps/', views.AppsListView.as_view(), {'is_free': False}, name='paid_apps'),
    path('app/<int:app_id>/<slug:slug>/',views.AppDetailView.as_view(),name='app_detail'),

    path('archive/<yyyy:year>/', views.archive_year, name='archive'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('free-apps/',views.AppsListView.as_view(),{'is_free': True},name='free_apps'),
    path('paid-apps/',views.AppsListView.as_view(),{'is_free': False},name='paid_apps'),
]
