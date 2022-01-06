import threading
import logging

from channels.consumer import AsyncConsumer

from task_director.src.schema_details import SchemaDetails
from task_director.src.schema_instance import SchemaInstance

logger = logging.getLogger(__name__)


class Controller(AsyncConsumer):
    """
    This class is a mediator between connected consumers and existing schema instances.
    Consumers will call the `handle_received` method to forward messages to the most
    relevant schema instance.
    """

    def __init__(self, *args, **kwargs):
        self._lock = threading.Lock()
        """
        This lock should be used whenever interacting with the `schema_instances` list below.
        """
        self._consumer_to_instance_map: dict[str, SchemaInstance] = {}
        self._schema_instances: list[SchemaInstance] = []
        super().__init__(*args, **kwargs)

    async def receive_message(self, message):
        msg = message["message"]
        consumer_id = message["consumer_id"]

        if consumer_id in self._consumer_to_instance_map:
            schema_instance = self._consumer_to_instance_map[consumer_id]
        else:
            # Find a matching schema instance or create one if it does not exist
            schema_instance = self._find_matching_schema_instance(msg, consumer_id)

            # Triage (assign) the current consumer to this schema instance if untriaged
            schema_instance.register_consumer(consumer_id, msg["repo_state"])
            self._consumer_to_instance_map[consumer_id] = schema_instance

        await schema_instance.receive_message(msg, consumer_id)

    def _find_schema_instance_by_id(self, schema_instance_id: str) -> SchemaInstance:
        with self._lock:
            for instance in self._schema_instances:
                if instance.schema_details.id == schema_instance_id:
                    return instance

            raise Exception("Schema instance not found")

    def _find_matching_schema_instance(self, msg: dict, consumer_id: str) -> SchemaInstance:
        with self._lock:
            schema_id = msg["schema_id"]
            cache_id = msg["cache_id"]
            repo_state = msg["repo_state"]
            for instance in self._schema_instances:
                if (
                    instance.schema_details.schema_id == schema_id
                    and instance.schema_details.cache_id == cache_id
                    and instance.check_repo_state_is_aligned(repo_state)
                ):
                    logger.info(
                        "Consumer "
                        + consumer_id
                        + " would be a perfect fit in existing instance: "
                        + instance.schema_details.id
                    )
                    return instance

            logger.info("No existing instance found for consumer %s", consumer_id)
            return self._create_schema_instance(msg)

    def _create_schema_instance(self, msg: dict) -> SchemaInstance:
        schema_details = SchemaDetails(msg["cache_id"], msg["schema_id"], msg["total_steps"])
        logger.info("Creating schema instance with ID: %s", schema_details.id)
        schema_instance = SchemaInstance(schema_details)
        self._schema_instances.append(schema_instance)
        return schema_instance

    async def deregister_consumer(self, message: dict):
        """
        Called when a consumer disconnects. The consumer is removed from the untriaged registry
        (if it exists there) and also any schema instance which it is a part of.
        """
        consumer_id = message["consumer_id"]
        with self._lock:
            if consumer_id in self._consumer_to_instance_map:
                del self._consumer_to_instance_map[consumer_id]
            for instance in self._schema_instances:
                instance.deregister_consumer(consumer_id)
                if instance.get_total_registered_consumers() == 0:
                    self._schema_instances.remove(instance)

    def get_total_registered_consumers(self) -> int:
        total_registered_consumers = 0
        with self._lock:
            for instance in self._schema_instances:
                total_registered_consumers += instance.get_total_registered_consumers()
        return total_registered_consumers

    async def get_total_registered_consumers_msg(self, message: dict):
        channel_name = message["channel_name"]
        total_registered_consumers = self.get_total_registered_consumers()
        await self.channel_layer.send(
            channel_name, {"type": channel_name, "total_registered_consumers": total_registered_consumers}
        )

    def get_total_running_schema_instances(self) -> int:
        return len(self._schema_instances)

    async def get_total_running_schema_instances_msg(self, message: dict):
        channel_name = message["channel_name"]
        total_running_schema_instances = self.get_total_running_schema_instances()
        await self.channel_layer.send(
            channel_name, {"type": channel_name, "total_running_schema_instances": total_running_schema_instances}
        )
