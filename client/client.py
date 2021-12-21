import argparse
import enum
import json
import threading

from connection import Connection
from logger import Logger
from task import Task


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTIONS = 2


class Controller:
    def __init__(self, config: any, connection: Connection, logger: Logger):
        self._config = config
        self._connection = connection
        self._logger = logger
        self._task_thread = None
        self._dispatch = {MessageType.BUILD_INSTRUCTIONS: self._process_build_instructions}

    def run(self):
        initial_message = {"message_type": MessageType.INIT, "schema_id": "1", "branch": "master"}
        self._logger.print("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        while True:
            # Wait for next message
            response = self._connection.get_latest_message(None)
            self._process_message(json.loads(response))

    def _process_message(self, msg: dict) -> bool:
        message_type = MessageType(int(msg["payload"]["message_type"]))
        return self._dispatch.get(message_type)(msg=msg)

    def _process_build_instructions(self, msg: dict):
        self._logger.print("Received build instructions message: " + str(msg))
        task = Task(5, self._logger)
        self._task_thread = threading.Thread(target=task.run)
        self._task_thread.start()
        return True


def main(configuration):
    logger = Logger(configuration.id)
    with Connection("ws://localhost:8000/ws/api/1/", logger) as connection:
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
