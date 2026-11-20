from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from rest_framework import serializers

from main.models import App

class AppSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = App
        fields = ['id', 'name', 'description', 'price', 'category', 'author', 'rating_avg']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username','password', 'is_active']

    def validate_password(self, value):
        return make_password(value)
