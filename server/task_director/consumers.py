import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.controller import Controller


class TicTacToeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["api_version"]
        self.room_group_name = "room_%s" % self.room_name

        print(f"Connected with room name:{self.room_group_name}")

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print("Disconnected")
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Get the event and send the appropriate event
        """
        response = json.loads(text_data)
        await Controller().handle_received(response)

    async def send_message(self, res):
        """Receive message from room group"""
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "payload": res,
                }
            )
        )
