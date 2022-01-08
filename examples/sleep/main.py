import logging
from time import sleep

from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.client import Client
from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class SleepTask(TaskRunner):
    def run(self, step_id: str, return_queue) -> bool:
        logger.info("Starting build task")

        sleep_amount = self._schema["steps"][int(step_id)]["task"]
        sleep(sleep_amount)

        logger.info("Finished build task")
        return_queue.put(True)


def main():
    configuration = parse_input_arguments()
    with Connection("localhost:8000", configuration.client_id) as connection:
        client = Client(configuration, connection, SleepTask)
        client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
