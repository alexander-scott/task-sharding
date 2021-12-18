from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def Controller():
    if _Controller._instance is None:
        _Controller._instance = _Controller()
    return _Controller._instance


class _Controller:
    _instance = None

    async def handle_received(self, response: dict):
        print(str(response))
        await self.process(response)

    async def process(self, response: dict):
        channel_layer = get_channel_layer()
        await channel_layer.group_send("room_1", {"type": "send_message"})
