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
            for consumer_id in untriaged_consumers:
                consumer = untriaged_consumers[consumer_id]
                print("Sening build instructions to: " + consumer.id)
                await consumer.send(
                    text_data=json.dumps(
                        {
                            "payload": {"consumer_id": consumer.id, "message_type": MessageType.BUILD_INSTRUCTIONS},
                        }
                    )
                )
                # await channel_layer.group_send(
                #     consumer, {"type": "send_message", "message_type": MessageType.BUILD_INSTRUCTIONS}
                # )

    async def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        with untriaged_consumers_lock:
            print("Adding consumer with ID: " + uuid)
            untriaged_consumers[uuid] = consumer
            print("Total consumers connected: " + str(len(untriaged_consumers)))

    async def deregister_consumer(self, uuid: str):
        with untriaged_consumers_lock:
            if uuid in untriaged_consumers:
                print("Removing consumer with ID: " + uuid)
                del untriaged_consumers[uuid]
                print("Total consumers connected: " + str(len(untriaged_consumers)))
