from unittest.mock import AsyncMock
from task_director.consumers import TaskDirectorConsumer


def create_consumer(id: str):
    consumer = TaskDirectorConsumer()
    consumer.scope = {"url_route": {"kwargs": {"api_version": "1", "id": id}}}
    consumer.accept = AsyncMock()
    consumer.send = AsyncMock()
    return consumer
