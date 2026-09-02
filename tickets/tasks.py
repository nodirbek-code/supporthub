import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger("supporthub.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_urgent_ticket(self, ticket_id):
    """
    11-topshiriq (1-task): Yangi urgent ticket yaratilganda operator yoki
    administratorga bildirishnoma yuborish. Development rejimida email
    console backend orqali terminalga chiqadi. Task muvaffaqiyatsiz bo'lsa
    ham asosiy ticket yaratish amaliyoti to'xtamaydi (Celery orqali async).
    """
    from tickets.models import Ticket
    from users.models import User

    try:
        ticket = Ticket.objects.select_related("client", "category").get(id=ticket_id)
    except Ticket.DoesNotExist:
        logger.warning("notify_urgent_ticket: ticket #%s topilmadi", ticket_id)
        return

    recipients = list(
        User.objects.filter(role__in=[User.Role.OPERATOR, User.Role.ADMIN])
        .exclude(email="")
        .values_list("email", flat=True)
    )

    if not recipients:
        logger.info("notify_urgent_ticket: bildirishnoma yuboriladigan operator/admin topilmadi")
        return

    try:
        send_mail(
            subject=f"[URGENT] Yangi shoshilinch murojaat: #{ticket.id} — {ticket.title}",
            message=(
                f"Mijoz: {ticket.client}\n"
                f"Kategoriya: {ticket.category}\n"
                f"Tavsif: {ticket.description}\n"
            ),
            from_email="noreply@supporthub.local",
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info("Ticket #%s uchun urgent bildirishnoma yuborildi (%d ta qabul qiluvchi)",
                    ticket.id, len(recipients))
    except Exception as exc:
        logger.error("notify_urgent_ticket xato: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def check_stale_new_tickets():
    """
    11-topshiriq (2-task): Har kuni 24 soatdan ortiq 'new' holatida qolgan
    ticketlarni aniqlab, logga yozadi. Celery Beat orqali kunlik ishga tushiriladi.
    """
    from datetime import timedelta

    from tickets.models import Ticket

    threshold = timezone.now() - timedelta(hours=24)
    stale_tickets = Ticket.objects.filter(status=Ticket.Status.NEW, created_at__lte=threshold)

    count = stale_tickets.count()
    if count:
        ids = list(stale_tickets.values_list("id", flat=True))
        logger.warning("24 soatdan ortiq 'new' holatida qolgan %d ta ticket: %s", count, ids)
    else:
        logger.info("24 soatdan ortiq 'new' holatida qolgan ticket topilmadi.")

    return count
