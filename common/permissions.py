from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Faqat admin roliga ruxsat beradi."""

    message = "Bu amal faqat administrator uchun ochiq."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_role
        )


class IsOperator(permissions.BasePermission):
    """Faqat operator roliga ruxsat beradi."""

    message = "Bu amal faqat operator uchun ochiq."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_operator
        )


class IsTicketOwner(permissions.BasePermission):
    """
    Mijoz faqat o'z ticketini ko'ra/tahrirlay oladi.
    Mijoz status va operator maydonlarini o'zgartira olmaydi (view darajasida tekshiriladi).
    """

    message = "Siz faqat o'zingizga tegishli murojaatni boshqarishingiz mumkin."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role:
            return True
        if request.user.is_operator:
            return obj.operator_id == request.user.id
        return obj.client_id == request.user.id


class IsAdminOrAssignedOperator(permissions.BasePermission):
    """
    Admin istalgan ticketni, operator esa faqat o'ziga biriktirilgan
    ticketni boshqarishi mumkin.
    """

    message = "Bu murojaatni boshqarishga ruxsatingiz yo'q."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role:
            return True
        if request.user.is_operator:
            return obj.operator_id == request.user.id
        return False
