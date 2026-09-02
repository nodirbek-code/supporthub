import django_filters

from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    """
    6-topshiriq: Ticketlar uchun filter.

    """

    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Ticket
        fields = ("status", "priority", "category", "operator")
