import logging
from time import sleep

logger = logging.getLogger(__name__)


class SleepTask:
    def load_schema(self, schema: dict, step_id: str):
        self._sleep_amount = schema["steps"][int(step_id)]["task"]

    def run(self, cwd: str) -> bool:
        logger.info("Starting build task")
        sleep(self._sleep_amount)
        logger.info("Finished build task")
        return True
