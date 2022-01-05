import threading
import logging

from channels.consumer import AsyncConsumer

from task_director.src.schema_details import SchemaDetails
from task_director.src.schema_instance import SchemaInstance

logger = logging.getLogger(__name__)


class TaskDirectorController(AsyncConsumer):
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
        self._schema_instances: list[SchemaInstance] = list()
        super().__init__(*args, **kwargs)

    async def receive_message(self, message):
        msg = message["message"]
        consumer_id = message["consumer_id"]

        if "instance_id" in message:
            schema_instance = self._find_schema_instance_by_id(message["instance_id"])
        else:
            # Find a matching schema instance or create one if it does not exist
            schema_instance = self._find_matching_schema_instance(msg, consumer_id)

            # Triage (assign) the current consumer to this schema instance if untriaged
            schema_instance.register_consumer(consumer_id, msg["repo_state"])

            # Return the instance ID back to the consumer
            await self.channel_layer.send(
                consumer_id, {"type": "assign.instance.id", "instance_id": schema_instance.schema_details.id}
            )

        await schema_instance.receive_message(msg, consumer_id)

    def _find_schema_instance_by_id(self, schema_instance_id: str) -> SchemaInstance:
        with self._lock:
            for instance in self._schema_instances:
                if instance.schema_details.id == schema_instance_id:
                    return instance

            raise Exception("Schema instance not found")

    def _find_matching_schema_instance(self, msg: dict, consumer_id: str) -> SchemaInstance:
        with self._lock:
            # TODO: Add more logic to determine which consumers best match to a schema instance.
            # instance. E.g. branch, cache instance, and git commit baseline are all necessary.
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

            logger.info("No existing instance found for consumer " + consumer_id)
            return self._create_schema_instance(msg)

    def _create_schema_instance(self, msg: dict) -> SchemaInstance:
        schema_details = SchemaDetails(msg["cache_id"], msg["schema_id"], msg["total_steps"])
        logger.info("Creating schema instance with ID: " + schema_details.id)
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
