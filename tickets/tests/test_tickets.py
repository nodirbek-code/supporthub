from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import create_category, create_ticket, create_user, jwt_header
from tickets.models import Ticket
from users.models import User


class TicketCreateTests(APITestCase):
    def setUp(self):
        self.client_user = create_user("mijoz1", role=User.Role.CLIENT)
        self.category = create_category()

    def test_client_can_create_ticket(self):
        """4. Mijoz ticket yarata olishi."""
        url = reverse("ticket-list-create")
        payload = {
            "title": "Internet ishlamayapti",
            "description": "Uy internetim 2 kundan beri ishlamayapti",
            "category": self.category.id,
            "priority": "high",
        }
        response = self.client.post(url, payload, **jwt_header(self.client_user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ticket_client_is_auto_assigned(self):
        """5. Ticket yaratuvchisi avtomatik aniqlanishi."""
        url = reverse("ticket-list-create")
        payload = {
            "title": "To'lov muammosi",
            "description": "Kartadan pul yechildi",
            "category": self.category.id,
        }
        self.client.post(url, payload, **jwt_header(self.client_user))
        ticket = Ticket.objects.latest("id")
        self.assertEqual(ticket.client, self.client_user)
        self.assertEqual(ticket.status, Ticket.Status.NEW)


class TicketVisibilityTests(APITestCase):
    def setUp(self):
        self.category = create_category()
        self.client1 = create_user("mijoz_a", role=User.Role.CLIENT)
        self.client2 = create_user("mijoz_b", role=User.Role.CLIENT)
        self.operator = create_user("operator_a", role=User.Role.OPERATOR)
        self.admin = create_user("admin_a", role=User.Role.ADMIN)

        self.ticket1 = create_ticket(self.client1, self.category)
        self.ticket2 = create_ticket(self.client2, self.category, operator=self.operator)

    def test_client_cannot_see_others_ticket(self):
        """6. Mijoz boshqa mijozning ticketini ko'ra olmasligi."""
        url = reverse("ticket-detail", args=[self.ticket2.id])
        response = self.client.get(url, **jwt_header(self.client1))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_operator_sees_only_assigned_tickets(self):
        """7. Operator faqat o'ziga biriktirilgan ticketni ko'rishi."""
        url = reverse("ticket-list-create")
        response = self.client.get(url, **jwt_header(self.operator))
        ids = [t["id"] for t in response.data["results"]]
        self.assertIn(self.ticket2.id, ids)
        self.assertNotIn(self.ticket1.id, ids)

    def test_admin_sees_all_tickets(self):
        url = reverse("ticket-list-create")
        response = self.client.get(url, **jwt_header(self.admin))
        self.assertEqual(response.data["count"], 2)


class CategoryPermissionTests(APITestCase):
    def setUp(self):
        self.admin = create_user("admin_b", role=User.Role.ADMIN)
        self.client_user = create_user("mijoz_c", role=User.Role.CLIENT)

    def test_admin_can_create_category(self):
        """8. Admin kategoriya yarata olishi."""
        url = reverse("category-list-create")
        response = self.client.post(url, {"name": "Shikoyat"}, **jwt_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_cannot_create_category(self):
        """9. Oddiy mijoz kategoriya yarata olmasligi."""
        url = reverse("category-list-create")
        response = self.client.post(url, {"name": "Taklif"}, **jwt_header(self.client_user))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SearchFilterOrderingTests(APITestCase):
    def setUp(self):
        self.category = create_category()
        self.admin = create_user("admin_c", role=User.Role.ADMIN)
        self.client_user = create_user("mijoz_d", role=User.Role.CLIENT)

        create_ticket(self.client_user, self.category, title="Internet uzilishi",
                      priority=Ticket.Priority.URGENT, status=Ticket.Status.NEW)
        create_ticket(self.client_user, self.category, title="To'lov xatosi",
                      priority=Ticket.Priority.LOW, status=Ticket.Status.RESOLVED)

    def test_search_returns_correct_result(self):
        """10. Search to'g'ri natija qaytarishi."""
        url = reverse("ticket-list-create") + "?search=Internet"
        response = self.client.get(url, **jwt_header(self.admin))
        self.assertEqual(response.data["count"], 1)
        self.assertIn("Internet", response.data["results"][0]["title"])

    def test_status_and_priority_filters_work(self):
        """11. Status va priority filtrlari ishlashi."""
        url = reverse("ticket-list-create") + "?status=resolved&priority=low"
        response = self.client.get(url, **jwt_header(self.admin))
        self.assertEqual(response.data["count"], 1)


class PaginationTests(APITestCase):
    def setUp(self):
        self.category = create_category()
        self.admin = create_user("admin_d", role=User.Role.ADMIN)
        self.client_user = create_user("mijoz_e", role=User.Role.CLIENT)
        for i in range(15):
            create_ticket(self.client_user, self.category, title=f"Murojaat {i}")

    def test_pagination_works_correctly(self):
        """12. Pagination to'g'ri ishlashi."""
        url = reverse("ticket-list-create") + "?page=1&page_size=10"
        response = self.client.get(url, **jwt_header(self.admin))
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertEqual(response.data["current_page"], 1)


class StatisticsCacheTests(APITestCase):
    def setUp(self):
        self.category = create_category()
        self.admin = create_user("admin_e", role=User.Role.ADMIN)
        self.client_user = create_user("mijoz_f", role=User.Role.CLIENT)

    def test_statistics_endpoint_is_cached(self):
        """13. Ticket statistikasi cache qilinishi."""
        from django.core.cache import cache

        from tickets.signals import STATISTICS_CACHE_KEY

        cache.clear()
        url = reverse("ticket-statistics")
        self.client.get(url, **jwt_header(self.admin))
        self.assertIsNotNone(cache.get(STATISTICS_CACHE_KEY))

    def test_cache_cleared_when_ticket_changes(self):
        """14. Ticket o'zgarganda cache tozalanishi."""
        from django.core.cache import cache

        from tickets.signals import STATISTICS_CACHE_KEY

        url = reverse("ticket-statistics")
        self.client.get(url, **jwt_header(self.admin))
        self.assertIsNotNone(cache.get(STATISTICS_CACHE_KEY))

        create_ticket(self.client_user, self.category)
        self.assertIsNone(cache.get(STATISTICS_CACHE_KEY))


class MiddlewareTests(APITestCase):
    def setUp(self):
        self.admin = create_user("admin_f", role=User.Role.ADMIN)

    def test_middleware_adds_response_time_header(self):
        """15. Middleware X-Response-Time header qaytarishi."""
        url = reverse("ticket-list-create")
        response = self.client.get(url, **jwt_header(self.admin))
        self.assertIn("X-Response-Time", response)
