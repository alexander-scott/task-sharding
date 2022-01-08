import logging
from time import sleep

from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class SleepTask(TaskRunner):
    def run(self, step_id: str) -> bool:
        logger.info("Starting build task")

        sleep_amount = self._schema["steps"][int(step_id)]["task"]
        sleep(sleep_amount)

        logger.info("Finished build task")
        return True
