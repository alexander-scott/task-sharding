from time import sleep

from src.logger import Logger


from src.task.abstract_task import AbstractTask


class SleepSchema:
    tasks = {
        "1": 3,
        "2": 1,
        "3": 2,
        "4": 7,
        "5": 6,
    }


class SleepTask(AbstractTask):
    def set_logger(self, logger: Logger):
        self._logger = logger

    def set_step_id(self, step_id: str):
        self._step_id = step_id

    def run(self):
        self._logger.print("Starting build task")
        sleep(SleepSchema.tasks[self._step_id])
        self._logger.print("Finished build task")
