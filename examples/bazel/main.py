import argparse
import logging
import subprocess

from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.client import Client
from task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class BazelTask(TaskRunner):
    def run(self, step_id: str):
        logger.info("Starting build task")

        target = self._schema["steps"][int(step_id)]["task"]
        proc = subprocess.Popen(["bazel", "test", target], cwd=self._config.workspace_path)
        stdout, stderr = proc.communicate()
        exit_code = proc.wait()

        if exit_code != 0:
            logger.error("Build failure: " + str(stderr))
            return False

        logger.info("Finished build task")
        return True


def main():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--workspace_path", help="Path to workspace", required=False)
    configuration = parse_input_arguments(parser)
    with Connection("localhost:8000", configuration.client_id) as connection:
        client = Client(configuration, connection, BazelTask)
        client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
