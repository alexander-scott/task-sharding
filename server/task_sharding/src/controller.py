import threading
import logging

from channels.consumer import AsyncConsumer

from task_sharding.src.schema_details import SchemaDetails
from task_sharding.src.schema_instance import SchemaInstance

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
        self._client_id_to_consumer_id_map: dict[str, str] = {}
        self._consumer_id_to_instance_map: dict[str, SchemaInstance] = {}
        self._schema_instances: list[SchemaInstance] = []
        super().__init__(*args, **kwargs)

    async def receive_message(self, message):
        msg = message["message"]
        consumer_id = message["consumer_id"]
        client_id = message["client_id"]

        if consumer_id in self._consumer_id_to_instance_map:
            schema_instance = self._consumer_id_to_instance_map[consumer_id]
        else:
            # Find a matching schema instance or create one if it does not exist
            schema_instance = self._find_matching_schema_instance(msg, consumer_id)

            # Triage (assign) the current consumer to this schema instance if untriaged
            schema_instance.register_consumer(consumer_id, msg["repo_state"])
            self._consumer_id_to_instance_map[consumer_id] = schema_instance
            self._client_id_to_consumer_id_map[client_id] = consumer_id

        await schema_instance.receive_message(msg, consumer_id)

    def _find_schema_instance_by_id(self, schema_instance_id: str) -> SchemaInstance:
        with self._lock:
            for instance in self._schema_instances:
                if instance.schema_details.id == schema_instance_id:
                    return instance

            raise Exception("Schema instance not found")

    def _find_matching_schema_instance(self, msg: dict, consumer_id: str) -> SchemaInstance:
        """
        Determines which schema instance is most relevant for a new consumer.
        It does this by looping over every existing schema instance and finds the
        instance which the highest number of patchsets that the new consumer has.
        This instance must also share the same schema_id and cache_id, and much
        not be a complex patchset.

        If no instance is found, a new schema instance will be created instead.
        """
        with self._lock:
            complex_patchset = msg["complex_patchset"]
            if not complex_patchset:
                schema_id = msg["schema_id"]
                cache_id = msg["cache_id"]
                repo_state = msg["repo_state"]

                matching_instance = None
                highest_instance_score = -1
                for instance in self._schema_instances:
                    if (
                        instance.schema_details.schema_id == schema_id
                        and instance.schema_details.cache_id == cache_id
                        and not complex_patchset
                    ):
                        instance_score = instance.get_total_common_patchsets_in_repo_state(repo_state)
                        if instance_score > highest_instance_score:
                            highest_instance_score = instance_score
                            matching_instance = instance

                if matching_instance:
                    logger.info(
                        "Consumer %s would be a perfect fit in existing instance: %s",
                        consumer_id,
                        matching_instance.schema_details.id,
                    )
                    return matching_instance

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
        client_id = message["client_id"]
        consumer_id = message["consumer_id"]
        with self._lock:
            if client_id in self._client_id_to_consumer_id_map:
                del self._client_id_to_consumer_id_map[client_id]
            if consumer_id in self._consumer_id_to_instance_map:
                del self._consumer_id_to_instance_map[consumer_id]
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

    def get_schema_instance_id_for_client_id(self, client_id: str) -> str:
        consumer_id = self._client_id_to_consumer_id_map[client_id]
        return self._consumer_id_to_instance_map[consumer_id].schema_details.id

    async def get_schema_instance_id_for_client_id_msg(self, message: dict) -> str:
        channel_name = message["channel_name"]
        client_id = message["id"]
        schema_instance_id = self.get_schema_instance_id_for_client_id(client_id)
        await self.channel_layer.send(channel_name, {"type": channel_name, "schema_instance_id": schema_instance_id})
