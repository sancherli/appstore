from django.apps.registry import Apps
from django.shortcuts import render, get_object_or_404
from pyexpat import features
from django.http import HttpResponse

from .models import App


def index(request):
    apps = App.objects.order_by('created_at').all()
    featured = App.objects.order_by('-price').first()
    return render(request, 'main/index.html', {
        'apps': apps,
        'featured': featured,
    })


def about(request):
    return render(request, 'main/about.html')


def app_detail(request,app_id):
    app = get_object_or_404(id=app_id)
    return render(request, 'main/app_detail.html',{'app': app})