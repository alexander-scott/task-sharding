import enum
import json
from queue import Queue
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from channels.generic.websocket import AsyncJsonWebsocketConsumer

import threading


def TaskDirectorController():
    if _Controller._instance is None:
        _Controller._instance = _Controller()
    return _Controller._instance


untriaged_consumers = {}
untriaged_consumers_lock = threading.Lock()

schema_directors = {}
schema_directors_lock = threading.Lock()


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTION = 2
    STEP_COMPLETE = 3
    SCHEMA_COMPLETE = 4


class SchemaDirector:
    def __init__(self, schema_id: str, total_steps: int):
        self._schema_id = schema_id
        self._total_steps = total_steps
        self._in_progress_steps = {}
        self._schema_consumers = set()
        self._lock = threading.Lock()
        self._to_do_steps = [i for i in range(1, total_steps + 1)]

    async def add(self, consumer_id: str):
        with self._lock:
            print(
                "For Schema "
                + self._schema_id
                + " there are currently "
                + str(len(self._to_do_steps))
                + " steps left to do."
            )

            self._schema_consumers.add(consumer_id)

            if len(self._to_do_steps) > 0:
                step = self._to_do_steps.pop()
                self._in_progress_steps[step] = consumer_id

                await untriaged_consumers[consumer_id].send(
                    text_data=json.dumps(
                        {
                            "payload": {
                                "consumer_id": consumer_id,
                                "message_type": MessageType.BUILD_INSTRUCTION,
                                "branch": "master",
                                "cache_id": "1",
                                "schema_id": self._schema_id,
                                "step_id": str(step),
                            },
                        }
                    )
                )

    async def step_completed(self, consumer_id: str, step_id: str):
        with self._lock:
            del self._in_progress_steps[int(step_id)]
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_steps)

        if steps_not_started > 0 or steps_in_progress > 0:
            await self.add(consumer_id)
        else:
            await self.schema_completed()

    async def schema_completed(self):
        with self._lock:
            print("Schema " + self._schema_id + " completed.")
            for consumer in self._schema_consumers:
                print("Sending schema complete message to consumer: " + consumer)
                await untriaged_consumers[consumer].send(
                    text_data=json.dumps(
                        {
                            "payload": {
                                "consumer_id": consumer,
                                "message_type": MessageType.SCHEMA_COMPLETE,
                                "schema_id": self._schema_id,
                            },
                        }
                    )
                )
            # with schema_directors_lock:
            #     del schema_directors[self._schema_id]


class _Controller:
    _instance = None

    def __init__(self) -> None:
        self._dispatch = {MessageType.INIT: self._handle_init, MessageType.STEP_COMPLETE: self._handle_step_completed}

    async def handle_received(self, response: dict, consumer_id: str):
        response["message_type"] = MessageType(int(response["message_type"]))
        await self._dispatch.get(response["message_type"])(response=response, consumer_id=consumer_id)

    async def _handle_init(self, response: dict, consumer_id: str):
        schema_id = response["schema_id"]
        total_steps = response["total_steps"]
        with schema_directors_lock:
            if not schema_id in schema_directors:
                print("Creating schema director with ID " + schema_id + " and total steps: " + str(total_steps))
                schema_director = SchemaDirector(schema_id, total_steps)
                schema_directors[schema_id] = schema_director
            await schema_directors[schema_id].add(consumer_id)

    async def _handle_step_completed(self, response: dict, consumer_id: str):
        schema_id = response["schema_id"]
        step_id = response["step_id"]
        with schema_directors_lock:
            schema_director = schema_directors[schema_id]
            await schema_director.step_completed(consumer_id, step_id)

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
