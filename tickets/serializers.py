from rest_framework import serializers

from users.serializers import UserShortSerializer

from .models import Category, Message, Ticket, TicketHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description", "is_active", "created_at")

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu nomli kategoriya allaqachon mavjud.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    sender = UserShortSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "ticket", "sender", "text", "is_read", "created_at")
        read_only_fields = ("id", "sender", "is_read", "created_at")

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Bo'sh xabar yuborib bo'lmaydi.")
        return value


class TicketHistorySerializer(serializers.ModelSerializer):
    changed_by = UserShortSerializer(read_only=True)

    class Meta:
        model = TicketHistory
        fields = ("id", "changed_by", "old_status", "new_status", "created_at")


class TicketListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    operator = UserShortSerializer(read_only=True)
    client = UserShortSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id", "title", "client", "operator", "category", "category_name",
            "status", "priority", "created_at", "updated_at",
        )


class TicketDetailSerializer(serializers.ModelSerializer):
    """
    4-topshiriq: Ticket tafsiloti — kategoriya nomi va operator ma'lumotlari
    ham ko'rsatiladi.
    """

    category_name = serializers.CharField(source="category.name", read_only=True)
    operator = UserShortSerializer(read_only=True)
    client = UserShortSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    history = TicketHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id", "title", "description", "client", "operator", "category",
            "category_name", "status", "priority", "created_at", "updated_at",
            "resolved_at", "messages", "history",
        )
        read_only_fields = ("id", "client", "created_at", "updated_at")


class TicketCreateSerializer(serializers.ModelSerializer):
    """
    4-topshiriq: Ticket yaratish — client token orqali avtomatik aniqlanadi,
    holat avtomatik 'new' bo'ladi.
    """

    class Meta:
        model = Ticket
        fields = ("id", "title", "description", "category", "priority")

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["client"] = request.user
        validated_data["status"] = Ticket.Status.NEW
        return super().create(validated_data)


class TicketUpdateSerializer(serializers.ModelSerializer):
    """
    4/5-topshiriq: Ticketni yangilash.
    client, created_at, updated_at maydonlari qo'lda o'zgartirilmaydi.
    Mijoz status va operator maydonlarini o'zgartira olmaydi
    """

    class Meta:
        model = Ticket
        fields = (
            "id", "title", "description", "category", "status", "operator",
            "priority", "resolved_at",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        if user.is_client:
            if "status" in attrs or "operator" in attrs:
                raise serializers.ValidationError(
                    "Mijoz ticketning status yoki operator maydonlarini o'zgartira olmaydi."
                )
        return attrs
