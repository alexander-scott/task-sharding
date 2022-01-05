import logging
import threading

from channels.layers import get_channel_layer
from task_director.src.message_type import MessageType
from task_director.src.schema_details import SchemaDetails

logger = logging.getLogger(__name__)


class SchemaInstance:
    def __init__(self, schema_details: SchemaDetails):
        self.schema_details = schema_details

        self._channel_layer = get_channel_layer()
        self._registered_consumers = set()
        self._in_progress_consumers = {}
        self._lock = threading.Lock()
        self._repo_states = {}
        self._to_do_steps = list(range(0, self.schema_details.total_steps))
        self._dispatch = {
            MessageType.INIT: self._send_build_instructions,
            MessageType.STEP_COMPLETE: self._receive_step_completed,
        }

    def register_consumer(self, consumer_id: str, repo_state: dict):
        self._print_with_prefix("Registering consumer " + consumer_id)
        self._registered_consumers.add(consumer_id)
        self._repo_states[consumer_id] = repo_state

    def deregister_consumer(self, consumer_id: str):
        self._registered_consumers.remove(consumer_id)
        if consumer_id in self._in_progress_consumers:
            step_id = self._in_progress_consumers[consumer_id]
            del self._in_progress_consumers[consumer_id]
            self._to_do_steps.append(int(step_id))
        if consumer_id in self._repo_states:
            del self._repo_states[consumer_id]

    def is_consumer_registered(self, uuid: str) -> bool:
        return uuid in self._registered_consumers

    def get_total_registered_consumers(self) -> int:
        return len(self._registered_consumers)

    def check_repo_state_is_aligned(self, repo_state: dict) -> bool:
        # Loop over every repository sent by the client
        for repo_name in repo_state:
            client_repo = repo_state[repo_name]
            client_branch = client_repo["base_ref"]
            client_patchset = client_repo["patchset"]
            client_additional_patchsets = client_repo.get("additional_patchsets", [])

            # Loop over every consumer assigned to this schema instance
            for consumer_id in self._repo_states:
                if not repo_name in self._repo_states[consumer_id]:
                    return False
                consumer_repo = self._repo_states[consumer_id][repo_name]
                consumer_branch = consumer_repo["base_ref"]
                consumer_patchset = consumer_repo["patchset"]

                # Branch name must be the same
                if not (client_branch == consumer_branch):
                    return False

                # Patchset must be the same or this consumers patchset may be in the clients additional patchsets list
                if not (client_patchset == consumer_patchset):
                    if not (consumer_patchset in client_additional_patchsets):
                        return False

        return True

    async def receive_message(self, msg: dict, consumer_id: str):
        msg["message_type"] = MessageType(int(msg["message_type"]))
        await self._dispatch.get(msg["message_type"])(msg=msg, consumer_id=consumer_id)

    async def _send_build_instructions(self, msg: dict, consumer_id: str):
        with self._lock:
            if len(self._to_do_steps) > 0:
                step = self._to_do_steps.pop()
                self._in_progress_consumers[consumer_id] = step

                self._print_with_prefix("Assigning step ID " + str(step) + " to consumer " + consumer_id)

                await self._channel_layer.send(
                    consumer_id,
                    {
                        "type": "send.message",
                        "message_type": MessageType.BUILD_INSTRUCTION,
                        "schema_id": self.schema_details.schema_id,
                        "step_id": str(step),
                    },
                )

    async def _receive_step_completed(self, msg: dict, consumer_id: str):
        with self._lock:
            step_id = msg["step_id"]
            step_success = msg["step_success"]
            del self._in_progress_consumers[consumer_id]
            if step_success:
                self._print_with_prefix("Consumer " + consumer_id + " completed step " + step_id)
            else:
                self._to_do_steps.append(int(step_id))
                pass  # TODO: Do something on a step failure
            steps_not_started = len(self._to_do_steps)
            steps_in_progress = len(self._in_progress_consumers)

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
            steps_in_progress = len(self._in_progress_consumers)

            if steps_not_started == 0 and steps_in_progress == 0:
                self._print_with_prefix("Schema completed")
                for consumer_id in self._registered_consumers:
                    self._print_with_prefix("Sending schema complete message to consumer " + consumer_id)
                    await self._channel_layer.send(
                        consumer_id,
                        {
                            "type": "send.message",
                            "message_type": MessageType.SCHEMA_COMPLETE,
                            "schema_id": self.schema_details.schema_id,
                        },
                    )
                return True

            return False

    def _print_with_prefix(self, msg: str):
        logger.info("[" + self.schema_details.id + "] " + msg)
