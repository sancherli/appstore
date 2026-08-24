from django.shortcuts import render
from django.http import HttpResponse
from .models import App


def index(request):
    return HttpResponse(f'Приложений в магазине: {App.objects.count()}')
