from src.arg_parse import parse_input_arguments
from src.connection import Connection
from src.logger import Logger
from src.client import Client


def main():
    configuration = parse_input_arguments()
    logger = Logger(configuration.client_id)
    with Connection("ws://localhost:8000/ws/api/1/" + configuration.client_id + "/", logger) as connection:
        client = Client(configuration, connection, logger)
        client.run()


if __name__ == "__main__":
    main()
