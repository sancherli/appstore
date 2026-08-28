from django.urls import path


from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('about/',views.about, name='about'),
    path('app/<int:app_id>',views.app_detail, name='app detail'),
]