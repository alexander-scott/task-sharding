import enum
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from channels.generic.websocket import AsyncJsonWebsocketConsumer

import threading
import uuid


def TaskDirectorController():
    if _Controller._instance is None:
        _Controller._instance = _Controller()
    return _Controller._instance


untriaged_consumers = {}
untriaged_consumers_lock = threading.Lock()


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTIONS = 2


class _Controller:
    _instance = None

    async def handle_received(self, response: dict):
        await self.process(response)

    async def process(self, response: dict):
        channel_layer = get_channel_layer()
        with untriaged_consumers_lock:
            for consumer in untriaged_consumers:
                await untriaged_consumers[consumer].send(
                    text_data=json.dumps(
                        {
                            "payload": {"message_type": MessageType.BUILD_INSTRUCTIONS},
                        }
                    )
                )
                # await channel_layer.group_send(consumer, {"type": "send_message"})

    async def register_consumer(self, consumer: AsyncJsonWebsocketConsumer) -> str:
        with untriaged_consumers_lock:
            consumer_id = str(uuid.uuid4())
            untriaged_consumers[consumer_id] = consumer
        return consumer_id

    async def deregister_consumer(self, uuid: str):
        with untriaged_consumers_lock:
            if uuid in untriaged_consumers:
                del untriaged_consumers[uuid]
