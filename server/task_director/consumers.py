import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.src.controller import TaskDirectorController


class TaskDirectorConsumer(AsyncJsonWebsocketConsumer):
    # We want this instance to be shared across all consumers so we make it a
    # class attribute, and re-bind it in every object's __init__ method.
    __controller_instance = TaskDirectorController()

    def __init__(self, *args, **kwargs):
        self._controller = self.__controller_instance
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.api_version = self.scope["url_route"]["kwargs"]["api_version"]
        self.id = self.scope["url_route"]["kwargs"]["id"]

        await self.channel_layer.group_add(self.id, self.channel_name)
        await self.accept()
        self._controller.register_consumer(self.id, self)

    async def disconnect(self, close_code):
        self._controller.deregister_consumer(self.id)
        await self.channel_layer.group_discard(self.id, self.channel_name)

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Get the event and send the appropriate event
        """
        response = json.loads(text_data)
        await self._controller.handle_received(response, self.id)

    # async def send_message(self, res):
    #     """
    #     Receive message from channel layer
    #     """
    #     # Send message to WebSocket
    #     await self.send(
    #         text_data=json.dumps(
    #             {
    #                 "payload": res,
    #             }
    #         )
    #     )
