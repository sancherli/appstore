from django.apps.registry import Apps
from django.shortcuts import render


from .models import App


def index(request):
    apps = App.objects.all()
    return render(request, 'main/index.html', {'apps': apps})


def about(request):
    return render(request, 'main/about.html')