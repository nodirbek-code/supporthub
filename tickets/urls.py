from django.urls import path

from .views import (
    CategoryDetailView,
    CategoryListCreateView,
    TicketDetailView,
    TicketListCreateView,
    TicketMessageListView,
    TicketStatisticsView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-detail"),

    path("tickets/statistics/", TicketStatisticsView.as_view(), name="ticket-statistics"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("tickets/<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("tickets/<int:ticket_id>/messages/", TicketMessageListView.as_view(), name="ticket-messages"),
]
