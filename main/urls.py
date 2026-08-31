from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('about/',views.about, name='about'),
    path('app/<int:app_id>/',views.app_detail, name='app_detail'),
    path('category/<int:category_id>/',views.category_detail, name='category'),
    path('new/', views.new, name='new'),
    path('free/', views.free_apps, name='free'),
    path('top/', views.top_apps, name='top'),
]