import logging
import sys
from time import sleep

from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.client import Client
from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class SleepTask(TaskRunner):
    def run(self, task_id: str) -> int:
        logger.info("Starting build task")

        sleep_amount = self._schema["tasks"][int(task_id)]["task"]
        sleep(sleep_amount)

        logger.info("Finished build task")
        return 0

    def abort(self):
        # TODO: Add some logic to abort a running sleep
        pass


def main():
    configuration = parse_input_arguments()
    with Connection("localhost:8000", configuration.client_id) as connection:
        client = Client(configuration, connection, SleepTask)
        sys.exit(client.run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
