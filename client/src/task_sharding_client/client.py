import json
import logging
import queue
import threading

from websocket import WebSocketConnectionClosedException

from .connection import Connection
from .message_type import MessageType
from .patchset_complexity import PatchsetComplexity
from .repo_state_parser import RepoStateParser
from .schema_loader import SchemaLoader
from .task_runner import TaskRunner

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, config: any, connection: Connection, task_runner: TaskRunner):
        self._config = config
        self._connection = connection
        self._schema = SchemaLoader.load_schema(config.schema_path)
        self._task_runner = task_runner
        self._dispatch = {
            MessageType.BUILD_INSTRUCTION: self._process_build_instructions,
            MessageType.SCHEMA_COMPLETE: self._process_schema_complete,
        }
        self._message_listening = False
        self._build_in_progress = False
        self._build_in_progress_lock = threading.Lock()

    def run(self):
        if self._config.repo_state:
            repo_state = self._config.repo_state
        else:
            repo_state = RepoStateParser.parse_repo_state()

        # Send a message to the server about our requirements.
        initial_message = {
            "message_type": MessageType.INIT,
            "repo_state": repo_state,
            "patchset_complexity": PatchsetComplexity.calculate_patchset_complexity(),
            "cache_id": self._config.cache_id,
            "schema_id": self._schema["name"],
            "total_steps": len(self._schema["steps"]),
        }

        logger.info("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        self._message_listening = True
        background_msg_thread = threading.Thread(target=self._run_background_message_thread)
        background_msg_thread.daemon = True
        background_msg_thread.start()

        background_msg_thread.join()

        logger.info("Closing websocket")
        self._connection.close_websocket()

    def _run_background_message_thread(self):
        # Run an infinite loop that is constantly waiting for messages.
        while self._message_listening:
            try:
                response = self._connection.get_latest_message(1)
                self._process_message(json.loads(response))
            except queue.Empty:
                continue

    def _process_message(self, msg: dict) -> bool:
        msg["message_type"] = MessageType(int(msg["message_type"]))
        return self._dispatch.get(msg["message_type"])(msg=msg)

    def _process_build_instructions(self, msg: dict):
        # This method is reached when the server sends us a build instruction message.
        # The task itself is given to another thread so that the message receiving
        # thread continues to operate in the background.
        logger.info("Received build instructions message: " + str(msg))
        with self._build_in_progress_lock:
            if self._build_in_progress:
                # TODO: Handle this more gracefully, as this is most likely a server-side problem.
                raise Exception("Build is currently in progress, yet we received a build instruction.")
            self._build_in_progress = True

        task_thread = threading.Thread(target=lambda: self._run_build_instructions(msg))
        task_thread.daemon = True
        task_thread.start()
        return True

    def _run_build_instructions(self, msg: dict):
        # This method executes a build instruction task and sends a message to the
        # server when it is complete.
        step_id = msg["step_id"]

        if not self._build_in_progress:
            raise Exception("Building is about to begin, yet the build_in_progress variable is not set to true.")

        task_runner = self._task_runner(self._schema, self._config)
        task_success = task_runner.run(step_id)

        self._build_in_progress = False

        step_message = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": self._schema["name"],
            "step_id": step_id,
            "step_success": task_success,
        }

        logger.info("Sending step complete message: " + str(step_message))
        try:
            self._connection.send_message(step_message)
        except WebSocketConnectionClosedException as e:
            logger.error("Failed to send message to server: " + str(e))
            self._message_listening = False

    def _process_schema_complete(self, msg: dict):
        logger.info("Received schema complete message: " + str(msg))
        self._message_listening = False
        return True
