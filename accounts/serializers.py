from rest_framework import serializers
from djoser.conf import settings
from djoser.serializers import TokenCreateSerializer


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(source="key")

    class Meta:
        model = settings.TOKEN_MODEL
        fields = ("token",)


class CustomTokenCreateSerializer(TokenCreateSerializer):
    Password = serializers.CharField(required=False, style={"input_type": "password"}, source="password")
    Username = serializers.CharField(required=False, style={"input_type": "username"}, source="username")