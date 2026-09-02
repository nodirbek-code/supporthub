from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    1-topshiriq: AbstractUser asosidagi custom User modeli.
    """

    class Role(models.TextChoices):
        CLIENT = "client", "Mijoz"
        OPERATOR = "operator", "Operator"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True, verbose_name="Elektron pochta")
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CLIENT, verbose_name="Rol"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon raqami")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqt")

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
