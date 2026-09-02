from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Noto'g'ri sahifa yoki mavjud bo'lmagan obyekt so'ralganda
    tushunarli xato javobi qaytaradi (3-topshiriq, 7-topshiriq).
    """
    response = exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, NotFound):
        response.data = {
            "detail": response.data.get("detail", "So'ralgan obyekt topilmadi."),
        }

    return response
