from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import create_user, jwt_header
from users.models import User


class RegisterTests(APITestCase):
    def test_user_can_register_successfully(self):
        """1. Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tishi."""
        url = reverse("auth-register")
        payload = {
            "username": "aliyor",
            "email": "aliyor@example.com",
            "phone": "+998901234567",
            "password": "StrongPass123",
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="aliyor")
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertTrue(user.check_password("StrongPass123"))


class LoginTests(APITestCase):
    def setUp(self):
        self.user = create_user("dilnoza")

    def test_login_fails_with_wrong_password(self):
        """2. Noto'g'ri parol bilan login bajarilmasligi."""
        url = reverse("auth-login")
        response = self.client.post(url, {"username": "dilnoza", "password": "wrong-pass"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_succeeds_and_returns_tokens(self):
        url = reverse("auth-login")
        response = self.client.post(url, {"username": "dilnoza", "password": "StrongPass123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = create_user("shoxrux")

    def test_profile_requires_jwt_token(self):
        """3. JWT tokensiz profilga kirib bo'lmasligi."""
        url = reverse("auth-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_accessible_with_valid_token(self):
        url = reverse("auth-profile")
        response = self.client.get(url, **jwt_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "shoxrux")
