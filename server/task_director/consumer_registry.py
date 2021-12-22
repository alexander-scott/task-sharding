import threading

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ConsumerRegistry:
    def __init__(self) -> None:
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

    def get_consumer(self, consumer_id: str) -> AsyncJsonWebsocketConsumer:
        with self._lock:
            return self._consumers[consumer_id]
