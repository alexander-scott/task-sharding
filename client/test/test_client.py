from src.client import Client
from src.logger import Logger

import json
import queue
import threading
import unittest


class MockConnection:
    def __init__(self):
        self.sent_messages = queue.Queue()
        self.received_messages = queue.Queue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def send_message(self, msg):
        self.sent_messages.put(msg)

    def get_sent_msg(self):
        return self.sent_messages.get(block=True)

    def close_websocket(self):
        pass

    def get_latest_message(self, timeout: float) -> dict:
        return self.received_messages.get(block=False, timeout=timeout)


class MockConfiguration:
    def __init__(self, client_id, schema_path, workspace_path):
        self.client_id = client_id
        self.schema_path = schema_path
        self.workspace_path = workspace_path


class TestClient(unittest.TestCase):
    def setUp(self):
        self.logger = Logger("1")

    def test_test(self):
        config = MockConfiguration("1", "./client/test/test_schema.yaml", "test")
        with MockConnection() as connection:
            client = Client(config, connection, self.logger)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()
            connection.received_messages.put(
                json.dumps(
                    {
                        "payload": {
                            "consumer_id": "UUID1",
                            "message_type": 2,
                            "branch": "master",
                            "cache_id": "1",
                            "schema_id": "1",
                            "step_id": "0",
                        }
                    }
                )
            )
            msg1 = connection.get_sent_msg()
            connection.received_messages.put(
                json.dumps(
                    {
                        "payload": {
                            "consumer_id": "UUID1",
                            "message_type": 4,
                            "branch": "master",
                            "cache_id": "1",
                            "schema_id": "1",
                            "step_id": "0",
                        }
                    }
                )
            )
            client_thread.join()
            self.assertDictEqual(
                {
                    "message_type": 1,
                    "branch": "master",
                    "cache_id": "1",
                    "schema_id": "sleep",
                    "total_steps": 4,
                },
                msg1,
            )
