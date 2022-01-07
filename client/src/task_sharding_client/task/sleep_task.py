from time import sleep


class SleepTask:
    def load_schema(self, schema: dict, step_id: str):
        self._sleep_amount = schema["steps"][int(step_id)]["task"]

    def run(self, cwd: str) -> bool:
        print("Starting build task")
        sleep(self._sleep_amount)
        print("Finished build task")
        return True
