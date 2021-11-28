import argparse
import threading

from connection import Connection
from task import Task


class Controller:
    def __init__(self, connection: Connection, config: any):
        self._config = config
        self._connection = connection

    def run(self):
        initial_message = {"ID": self._config.id, "schemaID": "1"}
        print("Sending initial message: " + str(initial_message))
        self._connection.send_message(initial_message)

        # Wait for initial build instructions from connection (BLOCKING)
        initial_message = self._connection.get_latest_message(5)
        print("Received initial message: " + str(initial_message))

        # Start background message handler
        background_message_thread = threading.Thread(target=self.background_message_handler)
        background_message_thread.daemon = True
        background_message_thread.start()

        # Start build task
        task = Task(5)
        task_thread = threading.Thread(target=task.run)
        task_thread.start()

        # Main thread should wait for task thread to finish
        task_thread.join()

    def background_message_handler(self):
        message = self._connection.get_latest_message(None)
        # Perform logic depending on the message contents, e.g. cancel the task thread


def main(configuration):
    print("Initialising connection")
    with Connection("ws://localhost:8000/ws") as connection:
        controller = Controller(connection, configuration)
        controller.run()


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("id", help="Client identifier")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    configuration = parse_input_arguments()
    main(configuration)
