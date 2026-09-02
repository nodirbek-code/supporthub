import logging
import time

logger = logging.getLogger("supporthub.requests")

EXCLUDED_PREFIXES = ("/admin/", "/static/")


class RequestLoggingMiddleware:
    """
    8-topshiriq: Har bir API so'rovini kuzatadigan middleware.

    Log qiladi: foydalanuvchi ID, HTTP metod, so'rov yo'li, IP manzil,
    javob status kodi, bajarilish vaqti, sana va vaqt.
    Javobga X-Response-Time header qo'shadi.
    /admin/ va /static/ yo'llari log qilinmaydi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(EXCLUDED_PREFIXES):
            return self.get_response(request)

        start_time = time.monotonic()

        try:
            response = self.get_response(request)
        except Exception:
            duration = time.monotonic() - start_time
            logger.exception(
                "Kutilmagan xato | Method=%s | Path=%s | IP=%s | Duration=%.3fs",
                request.method,
                request.path,
                self._get_client_ip(request),
                duration,
            )
            raise

        duration = time.monotonic() - start_time
        response["X-Response-Time"] = f"{duration:.3f}s"

        user_id = getattr(getattr(request, "user", None), "id", None) or "anon"

        logger.info(
            "User=%s | Method=%s | Path=%s | IP=%s | Status=%s | Duration=%.3fs",
            user_id,
            request.method,
            request.path,
            self._get_client_ip(request),
            response.status_code,
            duration,
        )

        return response

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
