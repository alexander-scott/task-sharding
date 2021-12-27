import subprocess
from src.task.abstract_task import AbstractTask


class BazelTask(AbstractTask):
    def load_schema(self, schema: dict, step_id: str):
        self._target = schema["steps"][int(step_id)]["task"]

    def run(self):
        self._logger.print("Starting build task")
        proc = subprocess.Popen(["bazel", "test", self._target], cwd=self._cwd)
        proc.communicate()
        self._logger.print("Finished build task")
