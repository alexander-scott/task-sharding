import json
import logging
from multiprocessing.managers import BaseManager
import queue
import threading

from websocket import WebSocketConnectionClosedException

from .connection import Connection
from .message_type import MessageType
from .repo_state_parser import RepoStateParser
from .schema_loader import SchemaLoader
from .task_runner import TaskRunner

logger = logging.getLogger(__name__)


class ClientConfig:
    client_id: str
    cache_id: str
    schema_path: str


class Client:
    def __init__(
        self,
        config: ClientConfig,
        connection: Connection,
        task_runner_type: TaskRunner,
        complex_patchset: bool = False,
        repo_state: dict = None,
    ):
        self._complex_patchset = complex_patchset
        self._config = config
        self._connection = connection

        self._repo_state = repo_state if repo_state else RepoStateParser.parse_repo_state()
        self._schema = SchemaLoader.load_schema(config.schema_path)
        self._dispatch = {
            MessageType.BUILD_INSTRUCTION: self._process_build_instructions,
            MessageType.SCHEMA_COMPLETE: self._process_schema_complete,
            MessageType.ABORT_STEP: self._process_abort_step,
            MessageType.WEBSOCKET_CLOSED: self._process_websocket_closed,
        }
        self._message_listening = False
        self._task_in_progress_lock = threading.Lock()

        # This object manager here allows us to share instances of TaskRunner across processes
        BaseManager.register("TaskRunner", task_runner_type)
        self._object_manager = BaseManager()
        self._object_manager.start()
        self._task_runner_instance: TaskRunner = None
        self._task_return_code: int = 1

    def run(self) -> int:
        # Send a message to the server about our requirements.
        initial_message = {
            "message_type": MessageType.INIT,
            "repo_state": self._repo_state,
            "complex_patchset": self._complex_patchset,
            "cache_id": self._config.cache_id,
            "schema_id": self._schema["name"],
            "total_steps": len(self._schema["steps"]),
        }

        logger.info("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        self._message_listening = True

        # Run an infinite loop on the MAIN THREAD that is constantly waiting for messages.
        while self._message_listening:
            try:
                response = self._connection.get_latest_message()
                self._process_message(json.loads(response))
            except queue.Empty:
                continue

        logger.info("Closing websocket")
        self._connection.close_websocket()

        return self._task_return_code

    def _process_message(self, msg: dict) -> bool:
        """
        Proxies the message to the relevant function depending on the message type.
        """

        msg["message_type"] = MessageType(int(msg["message_type"]))
        return self._dispatch.get(msg["message_type"])(msg=msg)

    def _process_build_instructions(self, msg: dict):
        """
        This method is reached when the server sends us a build instruction message.
        The task itself is given to another thread so that the message receiving
        thread continues to operate in the background.
        """

        logger.info("Received build instructions message: " + str(msg))

        # Create a new task runner instance
        with self._task_in_progress_lock:
            if self._task_runner_instance:
                raise Exception("Instance is running when it shouldn't be!")
            self._task_runner_instance = self._object_manager.TaskRunner(self._schema, self._config)

        # Spawn a new TASK THREAD that processes the build instructions
        task_thread = threading.Thread(target=lambda: self._run_build_instructions(msg))
        task_thread.daemon = True
        task_thread.start()

    def _run_build_instructions(self, msg: dict):
        """
        This method starts the task runner and passes to it a step ID.
        """

        step_id = msg["step_id"]

        # Run the task (BLOCKING)
        self._task_return_code = self._task_runner_instance.run(step_id)

        # Setting this to None signifies that the task has finished
        self._task_runner_instance = None

        step_message = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": self._schema["name"],
            "step_id": step_id,
            "step_success": True if self._task_return_code == 0 else False,
        }

        logger.info("Sending step complete message: " + str(step_message))
        try:
            self._connection.send_message(step_message)
        except WebSocketConnectionClosedException as e:
            logger.error("Failed to send message to server: " + str(e))
            self._message_listening = False

        if self._task_return_code != 0:
            self._message_listening = False

    def _process_schema_complete(self, msg: dict):
        logger.info("Received schema complete message: " + str(msg))
        self._message_listening = False

    def _process_abort_step(self, msg: dict):
        with self._task_in_progress_lock:
            if self._task_runner_instance:
                logger.info("Aborting current step")
                self._task_runner_instance.abort()
                self._task_runner_instance = None

    def _process_websocket_closed(self, msg: dict):
        self._process_abort_step(msg)
        self._message_listening = False
