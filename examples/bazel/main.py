import argparse
import logging
import subprocess

from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.client import Client
from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class BazelTask(TaskRunner):
    def __init__(self, schema: dict, config: any):
        super().__init__(schema, config)
        self.proc = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.proc:
            self.proc.terminate()

    def run(self, step_id: str, return_queue):
        logger.info("Starting build task")

        target = self._schema["steps"][int(step_id)]["task"]
        self.proc = subprocess.Popen(["bazel", "test", target], cwd=self._config.workspace_path)
        stdout, stderr = self.proc.communicate()
        exit_code = self.proc.wait()

        if exit_code != 0:
            logger.error("Build did not complete successfully: " + str(stderr) + " -- " + str(stdout))
            return_queue.put(False)
        else:
            logger.info("Finished build task")
            return_queue.put(True)

    def abort(self):
        if self.proc:
            self.proc.terminate()


def main():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--workspace_path", help="Path to workspace", required=True)
    configuration = parse_input_arguments(parser)

    with Connection("localhost:8000", configuration.client_id) as connection:
        client = Client(configuration, connection, BazelTask)
        client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
