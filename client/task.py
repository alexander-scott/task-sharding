from time import sleep
from logger import Logger


class AbstractTask:
    def run(self):
        raise NotImplementedError()


class SleepSchema:
    tasks = {
        "1": 3,
        "2": 1,
        "3": 2,
        "4": 7,
        "5": 6,
    }


class Task(AbstractTask):
    def __init__(self, step_id: str, logger: Logger):
        self._step_id = step_id
        self._logger = logger
        super().__init__()

    def run(self):
        self._logger.print("Starting build task")
        sleep(SleepSchema.tasks[self._step_id])
        self._logger.print("Finished build task")
