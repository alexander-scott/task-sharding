import argparse

from src.connection import Connection
from src.logger import Logger
from src.client import Client


def main(configuration):
    logger = Logger(configuration.client_id)
    with Connection("ws://localhost:8000/ws/api/1/" + configuration.client_id + "/", logger) as connection:
        client = Client(configuration, connection, logger)
        client.run()


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("client_id", help="Client identifier")
    parser.add_argument("schema_id", help="Schema identifier")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main(parse_input_arguments())
