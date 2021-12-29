from src.client import Client
from src.logger import Logger
from src.message_type import MessageType

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

    def test_client_lifecycle(self):
        """
        GIVEN a client connected to the server with a designated schema.
        WHEN behaviour is normal.
        EXPECT client to progress through the following states:
          - init
          - build
          - schema complete
        """
        config = MockConfiguration("1", "./client/test/test_schema.yaml", "test")
        with MockConnection() as connection:
            client = Client(config, connection, self.logger)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()

            # Get init_message sent from client (BLOCKING)
            init_msg = connection.get_sent_msg()

            # Mock build instruction message from server
            connection.received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.BUILD_INSTRUCTION,
                        "schema_id": "sleep",
                        "step_id": "0",
                    }
                )
            )

            # Get step_complete message from client (BLOCKING)
            step_complete_msg = connection.get_sent_msg()

            # Mock schema complete message from server
            connection.received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.SCHEMA_COMPLETE,
                        "schema_id": "sleep",
                    }
                )
            )

            client_thread.join()

            self.assertDictEqual(
                {
                    "message_type": MessageType.INIT,
                    "branch": "master",
                    "cache_id": "1",
                    "schema_id": "sleep",
                    "total_steps": 4,
                },
                init_msg,
            )
            self.assertDictEqual(
                {
                    "message_type": MessageType.STEP_COMPLETE,
                    "schema_id": "sleep",
                    "step_id": "0",
                    "step_success": True,
                },
                step_complete_msg,
            )
