import threading
from typing import Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.consumer_registry import ConsumerRegistry
from task_director.schema_director import SchemaDirector


class TaskDirectorController:
    def __init__(self):
        self._consumer_registry = ConsumerRegistry()
        self._schema_directors: dict[str, SchemaDirector] = {}
        self._schema_directors_lock = threading.Lock()

    async def handle_received(self, msg: dict, consumer_id: str):
        """
        Called when a registered websocket connection sends a JSON message to the server.
        The job of this method is to forward the message to a relevant schema_director
        instance, or create one if it doesn't yet exist.
        """

        with self._schema_directors_lock:
            schema_director = self._find_matching_schema_director_instance(msg)
            if not schema_director:
                schema_director = self._create_schema_director_instance(msg)

            # Forward the message to that schema director
            await schema_director.receive_message(msg, consumer_id)
            if await schema_director.check_if_schema_is_completed():
                self._remove_schema_director(msg)

    def _find_matching_schema_director_instance(self, msg: dict) -> Optional[SchemaDirector]:
        # TODO: Add more logic to determine which consumers best match to a schema_director
        # instance. E.g. branch, cache instance, and git commit baseline are all necessary.
        schema_id = msg["schema_id"]
        return self._schema_directors.get(schema_id, None)

    def _create_schema_director_instance(self, msg: dict) -> SchemaDirector:
        schema_id = msg["schema_id"]
        total_steps = msg["total_steps"]

        print("Creating schema director with ID " + schema_id + " and total steps: " + str(total_steps))

        schema_director = SchemaDirector(schema_id, total_steps, self._consumer_registry)
        self._schema_directors[schema_id] = schema_director
        return schema_director

    def _remove_schema_director(self, msg: dict):
        schema_id = msg["schema_id"]
        print("Deleting schema director with ID " + schema_id)
        del self._schema_directors[schema_id]

    def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        self._consumer_registry.add_consumer(uuid, consumer)

    def deregister_consumer(self, uuid: str):
        self._consumer_registry.remove_consumer(uuid)

    def get_total_registered_consumers(self) -> int:
        return self._consumer_registry.get_total_registered_consumers()
