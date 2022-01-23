import argparse
import logging
import subprocess
import sys

from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.client import Client
from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class BazelTask(TaskRunner):
    def __init__(self, schema: dict, config: any):
        super().__init__(schema, config)
        self._process = None

    def run(self, task_id: str) -> int:
        logger.info("Starting build task")

        target = self._schema["steps"][int(task_id)]["task"]
        self._process = subprocess.Popen(["bazel", "test", target], cwd=self._config.workspace_path)
        stdout, stderr = self._process.communicate()
        exit_code = self._process.wait()

        if exit_code != 0:
            logger.error("Build did not complete successfully: %s -- %s", str(stderr), str(stdout))
        else:
            logger.info("Finished build task")

        return exit_code

    def abort(self):
        if self._process:
            self._process.terminate()


def main():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--workspace_path", help="Path to workspace", required=True)
    configuration = parse_input_arguments(parser)

    with Connection("localhost:8000", configuration.client_id) as connection:
        client = Client(configuration, connection, BazelTask)
        sys.exit(client.run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
