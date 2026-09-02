from rest_framework_simplejwt.tokens import RefreshToken

from tickets.models import Category, Ticket
from users.models import User


def create_user(username, role=User.Role.CLIENT, password="StrongPass123", **kwargs):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        role=role,
        **kwargs,
    )
    return user


def jwt_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def create_category(name="Texnik muammo"):
    return Category.objects.create(name=name, description="Test kategoriya")


def create_ticket(client, category=None, operator=None, **kwargs):
    defaults = {
        "title": "Test murojaat",
        "description": "Test tavsif",
        "client": client,
        "operator": operator,
        "category": category or create_category(),
    }
    defaults.update(kwargs)
    return Ticket.objects.create(**defaults)
