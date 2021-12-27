import subprocess
from enum import IntEnum

from src.task.abstract_task import AbstractTask


class BazelExitCodes(IntEnum):
    # Exit codes common to all commands:
    SUCCESS = 0
    COMMAND_LINE_PROBLEM = 2
    BUILD_TERMINATED_ORDERLY_SHUTDOWN = 8
    EXTERNAL_ENVIRONMENT_FAILURE = 32
    OOM_FAILURE = 33
    LOCAL_ENVIRONMENTAL_ISSUE = 36
    UNHANDLED_EXCEPTION = 37

    # Exit codes for bazel build, bazel test:
    BUILD_FAILED = 1
    BUILD_OK_TESTS_FAILED = 3
    BUILD_OK_NO_TESTS_FOUND = 4

    # Exit codes for bazel query:
    PARTIAL_SUCCESS = 3
    COMMAND_FAILURE = 7


class BazelTask(AbstractTask):
    def load_schema(self, schema: dict, step_id: str):
        self._target = schema["steps"][int(step_id)]["task"]

    def run(self):
        self._logger.print("Starting build task")
        proc = subprocess.Popen(["bazel", "test", self._target], cwd=self._cwd)
        stdout, stderr = proc.communicate()
        exit_code = proc.wait()

        if exit_code != BazelExitCodes.SUCCESS:
            self._logger.print("Build failure: " + str(stderr))
            return False
        else:
            print("Finished build task")
            return True
