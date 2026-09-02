import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class TicketChatConsumer(AsyncWebsocketConsumer):
    """
    10-topshiriq:

    - Faqat autentifikatsiyadan o'tgan foydalanuvchi ulanadi.
    - Faqat ticket egasi, biriktirilgan operator yoki admin ulana oladi.
    - Mavjud bo'lmagan ticket uchun ulanish rad etiladi.
    - Yuborilgan xabar Message modeliga saqlanadi.
    - Xabar bir xil ticketga ulangan barcha foydalanuvchilarga real vaqtda yuboriladi.
    - Bo'sh xabar qabul qilinmaydi.
    """

    async def connect(self):
        self.ticket_id = self.scope["url_route"]["kwargs"]["ticket_id"]
        self.user = self.scope["user"]
        self.group_name = f"ticket_{self.ticket_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        ticket = await self._get_ticket(self.ticket_id)
        if ticket is None:
            await self.close(code=4404)
            return

        if not await self._user_can_access(ticket, self.user):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Noto'g'ri JSON format."}))
            return

        message_text = (payload.get("message") or "").strip()
        if not message_text:
            await self.send(text_data=json.dumps({"error": "Bo'sh xabar qabul qilinmaydi."}))
            return

        message = await self._save_message(self.ticket_id, self.user, message_text)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "id": message.id,
                "ticket_id": int(self.ticket_id),
                "sender": self.user.username,
                "message": message.text,
                "created_at": message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "id": event["id"],
                    "ticket_id": event["ticket_id"],
                    "sender": event["sender"],
                    "message": event["message"],
                    "created_at": event["created_at"],
                }
            )
        )

    @database_sync_to_async
    def _get_ticket(self, ticket_id):
        from tickets.models import Ticket

        return Ticket.objects.filter(id=ticket_id).first()

    @database_sync_to_async
    def _user_can_access(self, ticket, user):
        if user.is_admin_role:
            return True
        if user.is_operator:
            return ticket.operator_id == user.id
        return ticket.client_id == user.id

    @database_sync_to_async
    def _save_message(self, ticket_id, user, text):
        from tickets.models import Message

        return Message.objects.create(ticket_id=ticket_id, sender=user, text=text)
