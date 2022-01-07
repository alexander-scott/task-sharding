from task_sharding_client.arg_parse import parse_input_arguments
from task_sharding_client.connection import Connection
from task_sharding_client.logger import Logger
from task_sharding_client.client import Client

from bazel_task import BazelTask


def main():
    configuration = parse_input_arguments()
    logger = Logger(configuration.client_id)
    with Connection("ws://localhost:8000/ws/api/1/" + configuration.client_id + "/", logger) as connection:
        client = Client(configuration, connection, logger, BazelTask)
        client.run()


if __name__ == "__main__":
    main()
