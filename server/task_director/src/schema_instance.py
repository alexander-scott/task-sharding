import json
import logging
import threading

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from task_director.src.consumer_registry import ConsumerRegistry
from task_director.src.message_type import MessageType
from task_director.src.schema_details import SchemaDetails

logger = logging.getLogger(__name__)


class SchemaInstance:
    def __init__(self, schema_details: SchemaDetails):
        self.schema_details = schema_details

        self._consumer_registry = ConsumerRegistry()
        self._in_progress_steps = {}
        self._schema_consumers = set()
        self._lock = threading.Lock()
        self._to_do_steps = list(range(0, self.schema_details.total_steps))
        self._dispatch = {
            MessageType.INIT: self._send_build_instructions,
            MessageType.STEP_COMPLETE: self._receive_step_completed,
        }

    def register_consumer(self, uuid: str, consumer: AsyncJsonWebsocketConsumer):
        self._print_with_prefix("Registering consumer " + uuid)
        self._consumer_registry.add_consumer(uuid, consumer)

    def deregister_consumer(self, uuid: str):
        self._consumer_registry.remove_consumer(uuid)

    def is_consumer_registered(self, uuid: str) -> bool:
        return self._consumer_registry.check_if_consumer_exists(uuid)

    def get_total_registered_consumers(self) -> int:
        return self._consumer_registry.get_total_registered_consumers()

    async def receive_message(self, msg: dict, consumer_id: str):
        msg["message_type"] = MessageType(int(msg["message_type"]))
        await self._dispatch.get(msg["message_type"])(msg=msg, consumer_id=consumer_id)

    async def _send_build_instructions(self, msg: dict, consumer_id: str):
        with self._lock:
            self._schema_consumers.add(consumer_id)

            if len(self._to_do_steps) > 0:
                step = self._to_do_steps.pop()
                self._in_progress_steps[step] = consumer_id

                self._print_with_prefix("Assigning step ID " + str(step) + " to consumer " + consumer_id)

                await self._consumer_registry.get_consumer(consumer_id).send(
                    text_data=json.dumps(
                        {
                            "message_type": MessageType.BUILD_INSTRUCTION,
                            "schema_id": self.schema_details.schema_id,
                            "step_id": str(step),
                        }
                    )
                )

    async def _receive_step_completed(self, msg: dict, consumer_id: str):
        with self._lock:
            step_id = msg["step_id"]
            step_success = msg["step_success"]
            if step_success:
                self._print_with_prefix("Consumer " + consumer_id + " completed step " + step_id)
                del self._in_progress_steps[int(step_id)]
            else:
                self._to_do_steps.append(int(step_id))
                pass  # TODO: Do something on a step failure
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_steps)

        if steps_not_started > 0 or steps_in_progress > 0:
            self._print_with_prefix(
                "There are currently "
                + str(steps_not_started)
                + " steps not yet assigned and "
                + str(steps_in_progress)
                + " steps in progress"
            )
            await self._send_build_instructions(msg, consumer_id)
        else:
            await self.check_if_schema_is_completed()

    async def check_if_schema_is_completed(self):
        with self._lock:
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_steps)

            if steps_not_started == 0 and steps_in_progress == 0:
                self._print_with_prefix("Schema completed")
                for consumer_id in self._schema_consumers:
                    self._print_with_prefix("Sending schema complete message to consumer " + consumer_id)
                    await self._consumer_registry.get_consumer(consumer_id).send(
                        text_data=json.dumps(
                            {
                                "message_type": MessageType.SCHEMA_COMPLETE,
                                "schema_id": self.schema_details.schema_id,
                            }
                        )
                    )
                return True

            return False

    def _print_with_prefix(self, msg: str):
        logger.info("[" + self.schema_details.id + "] " + msg)
