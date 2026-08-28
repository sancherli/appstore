from django.apps.registry import Apps
from django.shortcuts import render
from pyexpat import features

from .models import App


def index(request):
    apps = App.objects.order_by('created_at').all()
    features = App.objects.order_by('-price').first()
    return render(request, 'main/index.html', {
        'apps': apps,
        'features': features,
    })


def about(request):
    return render(request, 'main/about.html')