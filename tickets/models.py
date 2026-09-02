from django.conf import settings
from django.db import models


class Category(models.Model):
    """1-topshiriq: Murojaat kategoriyasi (Texnik muammo, To'lov muammosi va )"""

    name = models.CharField(max_length=100, unique=True, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, verbose_name="Kategoriya izohi")
    is_active = models.BooleanField(default=True, verbose_name="Faol yoki faol emas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """1-topshiriq: Mijoz murojaati."""

    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        IN_PROGRESS = "in_progress", "Jarayonda"
        RESOLVED = "resolved", "Hal qilindi"
        CLOSED = "closed", "Yopildi"

    class Priority(models.TextChoices):
        LOW = "low", "Past"
        MEDIUM = "medium", "O'rta"
        HIGH = "high", "Yuqori"
        URGENT = "urgent", "Shoshilinch"

    title = models.CharField(max_length=255, verbose_name="Murojaat sarlavhasi")
    description = models.TextField(verbose_name="Muammo tavsifi")
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets_as_client",
        verbose_name="Murojaat yuborgan mijoz",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_as_operator",
        null=True,
        blank=True,
        verbose_name="Biriktirilgan operator",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Murojaat kategoriyasi",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Holat"
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM, verbose_name="Muhimlik"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Oxirgi yangilangan vaqt")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Yopilgan vaqt")

    class Meta:
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"#{self.id} — {self.title}"


class Message(models.Model):
    """1-topshiriq / 10-topshiriq: Ticket ichidagi yozishma xabari."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages", verbose_name="Murojaat"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="Xabar yuboruvchi",
    )
    text = models.TextField(verbose_name="Xabar matni")
    is_read = models.BooleanField(default=False, verbose_name="Xabar o'qilganmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ["created_at"]

    def __str__(self):
        return f"Ticket #{self.ticket_id} — {self.sender}: {self.text[:30]}"


class TicketHistory(models.Model):
    """1-topshiriq: Ticket holati o'zgarishlari tarixi."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="history", verbose_name="Murojaat"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ticket_changes",
        verbose_name="O'zgarishni amalga oshirgan shaxs",
    )
    old_status = models.CharField(max_length=20, verbose_name="Avvalgi holat")
    new_status = models.CharField(max_length=20, verbose_name="Yangi holat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="O'zgartirilgan vaqt")

    class Meta:
        verbose_name = "Murojaat tarixi"
        verbose_name_plural = "Murojaat tarixlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.ticket_id}: {self.old_status} -> {self.new_status}"
