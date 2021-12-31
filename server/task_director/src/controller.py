import threading
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from task_director.src.consumer_registry import ConsumerRegistry
from task_director.src.schema_details import SchemaDetails
from task_director.src.schema_instance import SchemaInstance

logger = logging.getLogger(__name__)


class TaskDirectorController:
    """
    This class is a mediator between connected consumers and existing schema instances.
    Consumers will call the `handle_received` method to forward messages to the most
    relevant schema instance.
    """

    def __init__(self):
        self._lock = threading.Lock()
        """
        This lock should be used whenever interacting with the `schema_instances` list below.
        """
        self._schema_instances: list[SchemaInstance] = list()
        self._untriaged_consumer_registry = ConsumerRegistry()

    def assign_consumer_to_instance(self, msg: dict, consumer_id: str):
        """
        Called when a registered websocket connection sends a JSON message to the server. The job
        of this method is to forward the message to a relevant schema instance, or create one if
        it doesn't yet exist.
        """

        # Find a matching schema instance or create one if it does not exist
        schema_instance = self._find_matching_schema_instance(msg, consumer_id)

        # Triage (assign) the current consumer to this schema instance if untriaged
        if self._untriaged_consumer_registry.check_if_consumer_exists(consumer_id):
            consumer = self._untriaged_consumer_registry.get_consumer(consumer_id, True)
            schema_instance.register_consumer(consumer_id, consumer)

        return schema_instance

    def _find_matching_schema_instance(self, msg: dict, consumer_id: str) -> SchemaInstance:
        with self._lock:
            # TODO: Add more logic to determine which consumers best match to a schema instance.
            # instance. E.g. branch, cache instance, and git commit baseline are all necessary.
            branch = msg["branch"]
            schema_id = msg["schema_id"]
            cache_id = msg["cache_id"]
            for instance in self._schema_instances:
                if (
                    instance.schema_details.schema_id == schema_id
                    and instance.schema_details.cache_id == cache_id
                    and instance.schema_details.branch == branch
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
        schema_details = SchemaDetails(msg["cache_id"], msg["branch"], msg["schema_id"], msg["total_steps"])
        logger.info("Creating schema instance with ID: " + schema_details.id)
        schema_instance = SchemaInstance(schema_details)
        self._schema_instances.append(schema_instance)
        return schema_instance

    def _remove_schema_instance(self, schema_instance: SchemaInstance):
        logger.info("Deleting schema instance with ID " + schema_instance.schema_details.id)
        with self._lock:
            self._schema_instances.remove(schema_instance)

    def register_consumer(self, consumer_id: str, consumer: AsyncJsonWebsocketConsumer):
        """
        Called when a new http request is upgraded to a websocket connection. As the consumer has
        not yet given any schema information, is it put into an `untriaged registry` until it does
        so.
        """
        self._untriaged_consumer_registry.add_consumer(consumer_id, consumer)

    def deregister_consumer(self, consumer_id: str):
        """
        Called when a consumer disconnects. The consumer is removed from the untriaged registry
        (if it exists there) and also any schema instance which it is a part of.
        """
        self._untriaged_consumer_registry.remove_consumer(consumer_id)
        with self._lock:
            for instance in self._schema_instances:
                instance.deregister_consumer(consumer_id)
                if instance.get_total_registered_consumers() == 0:
                    self._schema_instances.remove(instance)

    def get_total_untriaged_consumers(self) -> int:
        return self._untriaged_consumer_registry.get_total_registered_consumers()

    def get_total_registered_consumers(self) -> int:
        total_registered_consumers = 0
        with self._lock:
            for instance in self._schema_instances:
                total_registered_consumers += instance.get_total_registered_consumers()
        return total_registered_consumers

    def get_total_running_schema_instances(self) -> int:
        return len(self._schema_instances)
