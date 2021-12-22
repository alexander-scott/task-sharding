import threading

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.consumer_registry import ConsumerRegistry
from task_director.message_type import MessageType
from task_director.schema_director import SchemaDirector


def TaskDirectorController():
    if _Controller._instance is None:
        _Controller._instance = _Controller()
    return _Controller._instance


class _Controller:
    _instance = None

    def __init__(self):
        self._dispatch = {MessageType.INIT: self._handle_init, MessageType.STEP_COMPLETE: self._handle_step_completed}
        self._consumer_registry = ConsumerRegistry()
        self._schema_directors: dict[str, SchemaDirector] = {}
        self._schema_directors_lock = threading.Lock()

    async def handle_received(self, response: dict, consumer_id: str):
        response["message_type"] = MessageType(int(response["message_type"]))
        await self._dispatch.get(response["message_type"])(response=response, consumer_id=consumer_id)

    async def _handle_init(self, response: dict, consumer_id: str):
        schema_id = response["schema_id"]
        total_steps = response["total_steps"]

        with self._schema_directors_lock:
            if not schema_id in self._schema_directors:
                print("Creating schema director with ID " + schema_id + " and total steps: " + str(total_steps))
                schema_director = SchemaDirector(schema_id, total_steps, self._consumer_registry)
                self._schema_directors[schema_id] = schema_director
            await self._schema_directors[schema_id].add(consumer_id)

    async def _handle_step_completed(self, response: dict, consumer_id: str):
        schema_id = response["schema_id"]
        step_id = response["step_id"]

        with self._schema_directors_lock:
            schema_director = self._schema_directors[schema_id]
            await schema_director.step_completed(consumer_id, step_id)
            if await schema_director.schema_completed():
                del self._schema_directors[schema_id]

    async def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        self._consumer_registry.add_consumer(uuid, consumer)

    async def deregister_consumer(self, uuid: str):
        self._consumer_registry.remove_consumer(uuid)
