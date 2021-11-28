from time import sleep


class AbstractTask:
    def run(self):
        raise NotImplementedError()


class Task(AbstractTask):
    def __init__(self, task_duration: int):
        self._task_duration = task_duration
        super().__init__()

    def run(self):
        print("Starting build task")
        sleep(self._task_duration)
        print("Finished build task")
