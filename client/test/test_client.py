import json
import logging
import queue
import threading
import unittest

from src.task_sharding_client.client import Client
from src.task_sharding_client.connection import Connection
from src.task_sharding_client.message_type import MessageType
from src.task_sharding_client.task_runner import TaskRunner

logger = logging.getLogger(__name__)


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


class MockSuccessfulTaskRunner(TaskRunner):
    def run(self, task_id: str) -> int:
        logger.info("Starting task: %s", task_id)
        logger.info("Finished task: %s", task_id)
        return 0

    def abort(self):
        pass


class MockFailedTaskRunner(TaskRunner):
    def run(self, task_id: str) -> int:
        logger.info("Starting task: %s", task_id)
        logger.info("Finished task: %s", task_id)
        return 1

    def abort(self):
        pass


class MockRunUntilAbortedRunner(TaskRunner):
    def __init__(self, schema: dict, config: any):
        super().__init__(schema, config)
        self._run_loop = True

    def run(self, task_id: str) -> int:
        while self._run_loop:
            continue
        return 1

    def abort(self):
        self._run_loop = False


class MockConfiguration:
    def __init__(self, client_id, cache_id, schema_path):
        self.client_id = client_id
        self.cache_id = cache_id
        self.schema_path = schema_path


class TestClient(unittest.TestCase):
    def test__when_a_client_connects_to_the_server__expect_client_to_progress_through_the_normal_states(self):
        """
        GIVEN a client connected to the server with a designated schema.
        WHEN the client receives build instructions,
          AND subsequently successfully completes those build instructions.
        EXPECT client to send a successful task complete message
          AND receive a schema complete message and disconnect.
        """
        repo_state = {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            },
        }
        config = MockConfiguration("1", "1", "./client/test/data/test_schema.yaml")
        with MockConnection("localhost:8000", "1") as connection:
            client = Client(config, connection, MockSuccessfulTaskRunner, False, repo_state)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()

            # Get init_message sent from client (BLOCKING)
            init_msg = connection.get_sent_msg()

            # Mock build instruction message from server
            connection._received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.BUILD_INSTRUCTION,
                        "schema_id": "mock_schema",
                        "task_id": "0",
                    }
                )
            )

            # Get task_complete message from client (BLOCKING)
            task_complete_msg = connection.get_sent_msg()

            # Mock schema complete message from server
            connection._received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.SCHEMA_COMPLETE,
                        "task_id": "mock_schema",
                    }
                )
            )

            # Join the client thread (Assert that the client's infinite message receiving loop ends)
            client_thread.join()

            self.assertDictEqual(
                {
                    "message_type": MessageType.INIT,
                    "repo_state": {
                        "org/repo_1": {"base_ref": "main", "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"},
                    },
                    "complex_patchset": False,
                    "cache_id": "1",
                    "schema_id": "mock_schema",
                    "total_tasks": 4,
                },
                init_msg,
            )
            self.assertDictEqual(
                {
                    "message_type": MessageType.TASK_COMPLETE,
                    "schema_id": "mock_schema",
                    "task_id": "0",
                    "task_success": True,
                },
                task_complete_msg,
            )

    def test__when_a_client_connects_to_the_server__and_the_build_task_fails__expect_client_to_disconnect(self):
        """
        GIVEN a client connected to the server with a designated schema.
        WHEN the client receives build instructions,
          AND subsequently fails to complete those build instructions.
        EXPECT client to send a failed task complete message
          AND disconnect.
        """
        repo_state = {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            },
        }
        config = MockConfiguration("1", "1", "./client/test/data/test_schema.yaml")
        with MockConnection("localhost:8000", "1") as connection:
            client = Client(config, connection, MockFailedTaskRunner, False, repo_state)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()

            # Get init_message sent from client (BLOCKING)
            init_msg = connection.get_sent_msg()

            # Mock build instruction message from server
            connection._received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.BUILD_INSTRUCTION,
                        "schema_id": "mock_schema",
                        "task_id": "0",
                    }
                )
            )

            # Get task_complete message from client (BLOCKING)
            task_complete_msg = connection.get_sent_msg()

            # Join the client thread (Assert that the client's infinite message receiving loop ends)
            client_thread.join()

            self.assertDictEqual(
                {
                    "message_type": MessageType.INIT,
                    "repo_state": {
                        "org/repo_1": {"base_ref": "main", "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"},
                    },
                    "complex_patchset": False,
                    "cache_id": "1",
                    "schema_id": "mock_schema",
                    "total_tasks": 4,
                },
                init_msg,
            )
            self.assertDictEqual(
                {
                    "message_type": MessageType.TASK_COMPLETE,
                    "schema_id": "mock_schema",
                    "task_id": "0",
                    "task_success": False,
                },
                task_complete_msg,
            )

    def test__when_a_client_connects_to_the_server__and_server_sends_a_websocket_close_message__expect_that_the_build_task_is_aborted_and_the_websocket_is_closed(
        self,
    ):
        """
        GIVEN a client connected to the server with a designated schema.
        WHEN the client receives build instructions,
          AND subsequently the server sends a websocket close message.
        EXPECT client to abort the build task and disconnect.
        """
        repo_state = {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            },
        }
        config = MockConfiguration("1", "1", "./client/test/data/test_schema.yaml")
        with MockConnection("localhost:8000", "1") as connection:
            client = Client(config, connection, MockRunUntilAbortedRunner, False, repo_state)
            client_thread = threading.Thread(target=client.run)
            client_thread.start()

            # Get init_message sent from client (BLOCKING)
            init_msg = connection.get_sent_msg()

            # Mock build instruction message from server
            connection._received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.BUILD_INSTRUCTION,
                        "schema_id": "mock_schema",
                        "task_id": "0",
                    }
                )
            )

            connection._received_messages.put(
                json.dumps(
                    {
                        "message_type": MessageType.WEBSOCKET_CLOSED,
                    }
                )
            )

            # Join the client thread (Assert that the client's infinite message receiving loop ends)
            client_thread.join()

            self.assertDictEqual(
                {
                    "message_type": MessageType.INIT,
                    "repo_state": {
                        "org/repo_1": {"base_ref": "main", "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"},
                    },
                    "complex_patchset": False,
                    "cache_id": "1",
                    "schema_id": "mock_schema",
                    "total_tasks": 4,
                },
                init_msg,
            )
