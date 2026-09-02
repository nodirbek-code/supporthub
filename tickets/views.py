from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin

from .filters import TicketFilter
from .models import Category, Message, Ticket
from .serializers import (
    CategorySerializer,
    MessageSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketUpdateSerializer,
)
from .signals import STATISTICS_CACHE_KEY


# 3-topshiriq: Category CRUD
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]


# 4/5/6/7-topshiriq: Ticket CRUD + role-based ko'rinish + filter + pagination
class TicketListCreateView(generics.ListCreateAPIView):
    filterset_class = TicketFilter
    search_fields = ("title", "description")
    ordering_fields = ("created_at", "updated_at", "priority")
    ordering = ("-created_at",)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related("client", "operator", "category")

        if user.is_admin_role:
            return qs
        if user.is_operator:
            return qs.filter(operator=user)
        return qs.filter(client=user)


class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.select_related("client", "operator", "category").prefetch_related(
        "messages", "history"
    )

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_admin_role:
            return qs
        if user.is_operator:
            return qs.filter(operator=user)
        return qs.filter(client=user)

    def perform_update(self, serializer):
        instance = serializer.instance
        instance._changed_by = self.request.user
        serializer.save()


# 9-topshiriq: Redis cache — statistika endpointi
class TicketStatisticsView(APIView):


    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            cached = cache.get(STATISTICS_CACHE_KEY)
        except Exception:
            cached = None

        if cached is not None:
            return Response(cached)

        data = {
            "total": Ticket.objects.count(),
            "new": Ticket.objects.filter(status=Ticket.Status.NEW).count(),
            "in_progress": Ticket.objects.filter(status=Ticket.Status.IN_PROGRESS).count(),
            "resolved": Ticket.objects.filter(status=Ticket.Status.RESOLVED).count(),
            "closed": Ticket.objects.filter(status=Ticket.Status.CLOSED).count(),
            "urgent": Ticket.objects.filter(priority=Ticket.Priority.URGENT).count(),
        }

        try:
            cache.set(STATISTICS_CACHE_KEY, data, timeout=300)
        except Exception:
            pass

        return Response(data)


# Message — ticket ichidagi tarixiy xabarlar ro'yxati
class TicketMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        ticket_id = self.kwargs["ticket_id"]
        user = self.request.user
        ticket_qs = Ticket.objects.filter(id=ticket_id)

        if not user.is_admin_role:
            if user.is_operator:
                ticket_qs = ticket_qs.filter(operator=user)
            else:
                ticket_qs = ticket_qs.filter(client=user)

        ticket = ticket_qs.first()
        if not ticket:
            return Message.objects.none()

        return ticket.messages.select_related("sender").all()
