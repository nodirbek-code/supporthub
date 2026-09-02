from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    2-topshiriq: Ro'yxatdan o'tish serializeri.
    Parol set_password() orqali shifrlanadi, rol avtomatik 'client' bo'ladi.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "password")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.CLIENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"), password=attrs.get("password")
        )
        if not user:
            raise serializers.ValidationError("Login yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faol emas.")
        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "role", "is_active", "created_at")
        read_only_fields = ("id", "role", "is_active", "created_at")


class UserShortSerializer(serializers.ModelSerializer):
    """Ticket/Message ichida operator/sender ma'lumotini ko'rsatish uchun."""

    class Meta:
        model = User
        fields = ("id", "username", "role")
