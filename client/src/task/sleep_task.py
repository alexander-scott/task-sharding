from time import sleep


from src.task.abstract_task import AbstractTask


class SleepTask(AbstractTask):
    def load_schema(self, schema: dict, step_id: str):
        self._sleep_amount = schema["steps"][int(step_id)]["task"]

    def run(self):
        self._logger.print("Starting build task")
        sleep(self._sleep_amount)
        self._logger.print("Finished build task")
