import json

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from chat.middleware import JWTAuthMiddleware
from chat.routing import websocket_urlpatterns
from common.test_utils import create_category, create_ticket, create_user
from tickets.models import Message
from users.models import User


application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


def _access_token(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    return str(RefreshToken.for_user(user).access_token)


class WebSocketTests(TransactionTestCase):
    def setUp(self):
        self.category = create_category()
        self.client_user = create_user("ws_client", role=User.Role.CLIENT)
        self.other_client = create_user("ws_other", role=User.Role.CLIENT)
        self.ticket = create_ticket(self.client_user, self.category)

    async def test_unauthorized_user_cannot_connect(self):
        """16. Ruxsatsiz foydalanuvchi WebSocket'ga ulana olmasligi."""
        communicator = WebsocketCommunicator(
            application, f"/ws/tickets/{self.ticket.id}/"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_unrelated_client_cannot_connect(self):
        token = _access_token(self.other_client)
        communicator = WebsocketCommunicator(
            application, f"/ws/tickets/{self.ticket.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_message_is_saved_to_database(self):
        """17. WebSocket xabari bazaga saqlanishi."""
        token = _access_token(self.client_user)
        communicator = WebsocketCommunicator(
            application, f"/ws/tickets/{self.ticket.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_to(text_data=json.dumps({"message": "Salom, yordam kerak"}))
        response = await communicator.receive_from()
        data = json.loads(response)
        self.assertEqual(data["message"], "Salom, yordam kerak")

        exists = await self._message_exists()
        self.assertTrue(exists)

        await communicator.disconnect()

    async def _message_exists(self):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def check():
            return Message.objects.filter(ticket=self.ticket, text="Salom, yordam kerak").exists()

        return await check()
