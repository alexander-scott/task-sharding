import argparse
import json
import queue
import threading

from connection import Connection
from logger import Logger
from message_type import MessageType
from task import Task


class Client:
    def __init__(self, config: any, connection: Connection, logger: Logger):
        self._config = config
        self._connection = connection
        self._logger = logger
        self._dispatch = {
            MessageType.BUILD_INSTRUCTION: self._process_build_instructions,
            MessageType.SCHEMA_COMPLETE: self._process_schema_complete,
        }
        # We do not need a lock when reading/writing boolean values as they are thread-safe.
        # https://stackoverflow.com/a/9620974
        self._schema_complete = False
        self._build_in_progress = False
        self._build_in_progress_lock = threading.Lock()

    def run(self):
        # Send a message to the server about our requirements.
        initial_message = self._create_msg(MessageType.INIT)

        self._logger.print("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        # Run an infinite loop that is constantly waiting for messages.
        while threading.main_thread().is_alive() and not self._schema_complete:
            try:
                response = self._connection.get_latest_message(None)
                self._process_message(json.loads(response))
            except queue.Empty:
                pass

        self._logger.print("Closing websocket")
        self._connection.close_websocket()

    def _process_message(self, msg: dict) -> bool:
        msg["message_type"] = MessageType(int(msg["payload"]["message_type"]))
        return self._dispatch.get(msg["message_type"])(msg=msg)

    def _process_build_instructions(self, msg: dict):
        # This method is reached when the server sends us a build instruction message.
        # The task itself is given to another thread so that the message receiving
        # thread continues to operate in the background.
        self._logger.print("Received build instructions message: " + str(msg))
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
        step_id = msg["payload"]["step_id"]

        if not self._build_in_progress:
            raise Exception("Building is about to begin, yet the build_in_progress variable is not set to true.")

        task = Task(step_id, self._logger)
        task.run()

        self._build_in_progress = False

        step_message = self._create_msg(MessageType.STEP_COMPLETE)
        step_message["step_id"] = step_id

        self._logger.print("Sending step complete message: " + str(step_message))
        self._connection.send_message(step_message)

    def _process_schema_complete(self, msg: dict):
        self._logger.print("Received schema complete message: " + str(msg))
        self._schema_complete = True
        return True

    def _create_msg(self, msg_type: MessageType):
        return {
            "message_type": msg_type,
            "branch": "master",
            "cache_id": "1",
            "schema_id": self._config.schema_id,
            "total_steps": 5,
        }


def main(configuration):
    logger = Logger(configuration.client_id)
    with Connection("ws://localhost:8000/ws/api/1/" + configuration.client_id + "/", logger) as connection:
        client = Client(configuration, connection, logger)
        client.run()


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("client_id", help="Client identifier")
    parser.add_argument("schema_id", help="Schema identifier")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    configuration = parse_input_arguments()
    main(configuration)
