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
        self._consumer_registry = ConsumerRegistry()
        self._schema_directors: dict[str, SchemaDirector] = {}
        self._schema_directors_lock = threading.Lock()

    async def handle_received(self, response: dict, consumer_id: str):
        response["message_type"] = MessageType(int(response["message_type"]))
        schema_id = response["schema_id"]
        with self._schema_directors_lock:
            # Find the correct schema director for the current consumer
            if not schema_id in self._schema_directors:
                total_steps = response["total_steps"]
                print("Creating schema director with ID " + schema_id + " and total steps: " + str(total_steps))
                schema_director = SchemaDirector(schema_id, total_steps, self._consumer_registry)
                self._schema_directors[schema_id] = schema_director

            # Forward the message to that schema director
            await self._schema_directors[schema_id].receive_message(response, consumer_id)
            if await self._schema_directors[schema_id].check_if_schema_is_completed():
                del self._schema_directors[schema_id]

    async def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        self._consumer_registry.add_consumer(uuid, consumer)

    async def deregister_consumer(self, uuid: str):
        self._consumer_registry.remove_consumer(uuid)
