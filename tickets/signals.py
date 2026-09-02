import logging

from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Ticket, TicketHistory

logger = logging.getLogger("supporthub.tasks")

STATISTICS_CACHE_KEY = "tickets:statistics"


def _clear_statistics_cache():
    cache.delete(STATISTICS_CACHE_KEY)


@receiver(pre_save, sender=Ticket)
def track_status_change(sender, instance, **kwargs):
    """
    9-topshiriq / 1-topshiriq: Ticket holati o'zgarganda TicketHistory yozuvi
    yaratiladi va statistikaning cache'i tozalanadi.
    """
    if not instance.pk:
        instance._old_status = None
        return

    try:
        old = Ticket.objects.get(pk=instance.pk)
    except Ticket.DoesNotExist:
        instance._old_status = None
        return

    instance._old_status = old.status

    if old.status != instance.status:
        if instance.status in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED):
            instance.resolved_at = instance.resolved_at or timezone.now()


@receiver(post_save, sender=Ticket)
def on_ticket_saved(sender, instance, created, **kwargs):
    _clear_statistics_cache()

    if created:
        TicketHistory.objects.create(
            ticket=instance,
            changed_by=instance.client,
            old_status="",
            new_status=instance.status,
        )
        if instance.priority == Ticket.Priority.URGENT:
            from .tasks import notify_urgent_ticket

            notify_urgent_ticket.delay(instance.id)
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status is not None and old_status != instance.status:
        TicketHistory.objects.create(
            ticket=instance,
            changed_by=getattr(instance, "_changed_by", instance.operator or instance.client),
            old_status=old_status,
            new_status=instance.status,
        )
        logger.info("Ticket #%s holati o'zgardi: %s -> %s", instance.id, old_status, instance.status)
