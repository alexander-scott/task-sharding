import threading

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ConsumerRegistry:
    def __init__(self):
        self._consumers: dict[str, AsyncJsonWebsocketConsumer] = {}
        self._lock = threading.Lock()

    def add_consumer(self, consumer_id: str, consumer: any):
        with self._lock:
            print("Adding consumer with ID: " + consumer_id)
            self._consumers[consumer_id] = consumer
            print("Total consumers connected: " + str(len(self._consumers)))

    def remove_consumer(self, consumer_id: str):
        with self._lock:
            if consumer_id in self._consumers:
                print("Removing consumer with ID: " + consumer_id)
                del self._consumers[consumer_id]
                print("Total consumers connected: " + str(len(self._consumers)))

    def get_consumer(self, consumer_id: str, remove_consumer: bool = False) -> AsyncJsonWebsocketConsumer:
        with self._lock:
            consumer = self._consumers[consumer_id]
            if remove_consumer:
                del self._consumers[consumer_id]
            return consumer

    def check_if_consumer_exists(self, consumer_id: str) -> bool:
        with self._lock:
            return consumer_id in self._consumers

    def get_total_registered_consumers(self) -> int:
        with self._lock:
            return len(self._consumers)
