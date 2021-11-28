from time import sleep
from logger import Logger


class AbstractTask:
    def run(self):
        raise NotImplementedError()


class Task(AbstractTask):
    def __init__(self, task_duration: int, logger: Logger):
        self._task_duration = task_duration
        self._logger = logger
        super().__init__()

    def run(self):
        self._logger.print("Starting build task")
        sleep(self._task_duration)
        self._logger.print("Finished build task")
