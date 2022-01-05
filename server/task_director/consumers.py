import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TaskDirectorConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self._schema_instance_id: str = None
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.api_version = self.scope["url_route"]["kwargs"]["api_version"]
        self.id = self.scope["url_route"]["kwargs"]["id"]

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.send("controller", {"type": "deregister.consumer", "consumer_id": self.channel_name})

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Get the event and send the appropriate event
        """
        response = json.loads(text_data)
        message = {"type": "receive.message", "consumer_id": self.channel_name, "message": response}
        if self._schema_instance_id:
            message["instance_id"] = self._schema_instance_id

        await self.channel_layer.send("controller", message)

    async def assign_instance_id(self, message):
        self._schema_instance_id = message["instance_id"]

    async def send_message(self, res):
        """
        Receive message from channel layer
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(res))
