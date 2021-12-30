import threading
from typing import Optional

from task_director.src.schema_instance import SchemaInstance


class SchemaInstanceManager:
    def __init__(self):
        self.lock = threading.Lock()
        self._schema_instances: list[SchemaInstance] = list()

    def find_matching_schema_instance(self, msg: dict, consumer_id: str) -> Optional[SchemaInstance]:
        for instance in self._schema_instances:
            if instance.is_consumer_registered(consumer_id):
                print("Consumer " + consumer_id + " is already registered within an instace.")
                return instance

        # TODO: Add more logic to determine which consumers best match to a schema instance.
        # instance. E.g. branch, cache instance, and git commit baseline are all necessary.
        schema_id = msg["schema_id"]
        cache_id = msg["cache_id"]
        for instance in self._schema_instances:
            if instance.schema_id == schema_id and instance.cache_id == cache_id:
                print("Consumer " + consumer_id + " would be a perfect fit in an existing instance.")
                return instance

        return None

    def create_schema_instance(self, msg: dict) -> SchemaInstance:
        cache_id = msg["cache_id"]
        schema_id = msg["schema_id"]
        total_steps = msg["total_steps"]

        print("Creating schema instance with ID " + schema_id + " and total steps: " + str(total_steps))

        schema_instance = SchemaInstance(cache_id, schema_id, total_steps)
        self._schema_instances.append(schema_instance)
        return schema_instance

    def remove_schema_instance(self, schema_instance: SchemaInstance):
        print("Deleting schema instance with ID " + schema_instance.schema_id)
        self._schema_instances.remove(schema_instance)

    def deregister_consumer(self, consumer_id: str):
        with self.lock:
            for instance in self._schema_instances:
                instance.deregister_consumer(consumer_id)

    def get_total_registered_consumers(self) -> int:
        total_registered_consumers = 0
        for instance in self._schema_instances:
            total_registered_consumers += instance.get_total_registered_consumers()
        return total_registered_consumers

    def get_total_running_schema_instances(self) -> int:
        return len(self._schema_instances)
