import json
import queue
import threading
import unittest

from src.task_sharding_client.client import Client
from src.task_sharding_client.connection import Connection
from src.task_sharding_client.message_type import MessageType
from src.task_sharding_client.task_runner import DefaultTask


class MockConnection(Connection):
    def __init__(self, server_url: str, client_id: str):
        self.sent_messages = queue.Queue()
        super().__init__(server_url, client_id)

    def _init_connection(self, server_url: str):
        return None

    def send_message(self, msg: dict):
        self.sent_messages.put(msg)

    def get_sent_msg(self):
        return self.sent_messages.get(block=True)


class MockConfiguration:
    def __init__(self, client_id, cache_id, schema_path):
        self.client_id = client_id
        self.cache_id = cache_id
        self.schema_path = schema_path


class TestClient(unittest.TestCase):
    def test_client_lifecycle(self):
        """
        GIVEN a client connected to the server with a designated schema.
        WHEN behaviour is normal.
        EXPECT client to progress through the following states:
          - init
          - build
          - schema complete
        """
        repo_state = {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            },
        }
        config = MockConfiguration("1", "1", "./client/test/test_schema.yaml")
        with MockConnection("localhost:8000", "1") as connection:
            client = Client(config, connection, DefaultTask, False, repo_state)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()

            # Get init_message sent from client (BLOCKING)
            init_msg = connection.get_sent_msg()

            # Mock build instruction message from server
            connection._received_messages.put(
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
            connection._received_messages.put(
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
                    "repo_state": {
                        "org/repo_1": {"base_ref": "main", "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"},
                    },
                    "complex_patchset": False,
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
