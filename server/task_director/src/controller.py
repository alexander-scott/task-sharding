from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.src.consumer_registry import ConsumerRegistry
from task_director.src.schema_instance_manager import SchemaInstanceManager


class TaskDirectorController:
    def __init__(self):
        self._schema_instance_manager = SchemaInstanceManager()
        self._untriaged_consumer_registry = ConsumerRegistry()

    async def handle_received(self, msg: dict, consumer_id: str):
        """
        Called when a registered websocket connection sends a JSON message to the server.
        The job of this method is to forward the message to a relevant schema instance.
        instance, or create one if it doesn't yet exist.
        """

        with self._schema_instance_manager.lock:
            # Find a matching schema instance or create one if it does not exist
            schema_instance = self._schema_instance_manager.find_matching_schema_instance(msg, consumer_id)
            if not schema_instance:
                schema_instance = self._schema_instance_manager.create_schema_instance(msg)

            # Triage (assign) the current consumer to this schema instance if untriaged
            if self._untriaged_consumer_registry.check_if_consumer_exists(consumer_id):
                consumer = self._untriaged_consumer_registry.get_consumer(consumer_id, True)
                schema_instance.register_consumer(consumer_id, consumer)

            # Forward the message to that schema instance
            await schema_instance.receive_message(msg, consumer_id)
            if await schema_instance.check_if_schema_is_completed():
                self._schema_instance_manager.remove_schema_instance(schema_instance)

    def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        self._untriaged_consumer_registry.add_consumer(uuid, consumer)

    def deregister_consumer(self, uuid: str):
        # self._consumer_registry.remove_consumer(uuid)
        # TODO: Find all schema instances which have this consumer in progress and inform them
        pass

    def get_total_registered_consumers(self) -> int:
        return self._schema_instance_manager.get_total_registered_consumers()

    def get_total_untriaged_consumers(self) -> int:
        return self._untriaged_consumer_registry.get_total_registered_consumers()
