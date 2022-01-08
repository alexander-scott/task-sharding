import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TaskShardingConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self._schema_instance_id: str = None
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.api_version = self.scope["url_route"]["kwargs"]["api_version"]
        self.client_id = self.scope["url_route"]["kwargs"]["id"]

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.send(
            "controller", {"type": "deregister.consumer", "client_id": self.client_id, "consumer_id": self.channel_name}
        )

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Get the event and send the appropriate event
        """
        response = json.loads(text_data)
        message = {
            "type": "receive.message",
            "client_id": self.client_id,
            "consumer_id": self.channel_name,
            "message": response,
        }

        await self.channel_layer.send("controller", message)

    async def send_message(self, res):
        """
        Receive message from channel layer
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(res))
