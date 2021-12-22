import argparse
import enum
import json
from queue import Empty
import threading

from connection import Connection
from logger import Logger
from task import Task


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTION = 2
    STEP_COMPLETE = 3
    SCHEMA_COMPLETE = 4


class Controller:
    def __init__(self, config: any, connection: Connection, logger: Logger):
        self._config = config
        self._connection = connection
        self._logger = logger
        self._task_thread = None
        self._schema_complete = False
        self._dispatch = {
            MessageType.BUILD_INSTRUCTION: self._process_build_instructions,
            MessageType.SCHEMA_COMPLETE: self._process_schema_complete,
        }

    def run(self):
        initial_message = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 5,
        }
        self._logger.print("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        while threading.main_thread().is_alive() and not self._schema_complete:
            try:
                response = self._connection.get_latest_message(1)  # Wait for next message
                self._process_message(json.loads(response))
            except Empty:
                # print("Errors -- schema completed: " + str(self._schema_complete))
                pass

        print("Closing websocket")
        self._connection.close_websocket()

    def _process_message(self, msg: dict) -> bool:
        msg["message_type"] = MessageType(int(msg["payload"]["message_type"]))
        return self._dispatch.get(msg["message_type"])(msg=msg)

    def _process_build_instructions(self, msg: dict):
        self._logger.print("Received build instructions message: " + str(msg))
        self._task_thread = threading.Thread(target=lambda: self._run_build_instructions(msg))
        self._task_thread.daemon = True
        self._task_thread.start()
        return True

    def _run_build_instructions(self, msg: dict):
        step_id = msg["payload"]["step_id"]
        task = Task(step_id, self._logger)
        task.run()
        step_message = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": step_id,
        }
        self._logger.print("Sending step complete message: " + str(step_message))
        self._connection.send_message(step_message)

    def _process_schema_complete(self, msg: dict):
        self._logger.print("Received schema complete message: " + str(msg))
        self._schema_complete = True
        return True


def main(configuration):
    logger = Logger(configuration.id)
    with Connection("ws://localhost:8000/ws/api/1/" + configuration.id + "/", logger) as connection:
        controller = Controller(configuration, connection, logger)
        controller.run()


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("id", help="Client identifier")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    configuration = parse_input_arguments()
    main(configuration)
