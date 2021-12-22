import json
import threading
from task_director.consumer_registry import ConsumerRegistry
from task_director.message_type import MessageType


class SchemaDirector:
    def __init__(self, schema_id: str, total_steps: int, consumer_registry: ConsumerRegistry):
        self._schema_id = schema_id
        self._total_steps = total_steps
        self._consumer_registry = consumer_registry
        self._in_progress_steps = {}
        self._schema_consumers = set()
        self._lock = threading.Lock()
        self._to_do_steps = [i for i in range(1, total_steps + 1)]

    async def add(self, consumer_id: str):
        with self._lock:
            print(
                "For Schema "
                + self._schema_id
                + " there are currently "
                + str(len(self._to_do_steps))
                + " steps left to do."
            )

            self._schema_consumers.add(consumer_id)

            if len(self._to_do_steps) > 0:
                step = self._to_do_steps.pop()
                self._in_progress_steps[step] = consumer_id

                await self._consumer_registry.get_consumer(consumer_id).send(
                    text_data=json.dumps(
                        {
                            "payload": {
                                "consumer_id": consumer_id,
                                "message_type": MessageType.BUILD_INSTRUCTION,
                                "branch": "master",
                                "cache_id": "1",
                                "schema_id": self._schema_id,
                                "step_id": str(step),
                            },
                        }
                    )
                )

    async def step_completed(self, consumer_id: str, step_id: str):
        with self._lock:
            del self._in_progress_steps[int(step_id)]
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_steps)

        if steps_not_started > 0 or steps_in_progress > 0:
            await self.add(consumer_id)

    async def schema_completed(self):
        with self._lock:
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_steps)

            if steps_not_started == 0 and steps_in_progress == 0:
                print("Schema " + self._schema_id + " completed.")
                for consumer_id in self._schema_consumers:
                    print("Sending schema complete message to consumer: " + consumer_id)
                    await self._consumer_registry.get_consumer(consumer_id).send(
                        text_data=json.dumps(
                            {
                                "payload": {
                                    "consumer_id": consumer_id,
                                    "message_type": MessageType.SCHEMA_COMPLETE,
                                    "schema_id": self._schema_id,
                                },
                            }
                        )
                    )
                return True

            return False
