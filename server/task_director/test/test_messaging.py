import asyncio
import json

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.mock_classes.mock_consumer import MockConsumer


class TaskDirectorTests__Messaging(TestCase):
    def setUp(self):
        self.controller = TaskDirectorController()
        self.consumer_id = "UUID1"
        self.consumer = MockConsumer(self.consumer_id)
        self.controller.register_consumer("UUID1", self.consumer)

    def test__send_init_message(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message.
        EXPECT the server to return to the same consumer a BUILD instruction message.
        """
        mock_client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }
        expected_server_build_msg = {
            "payload": {
                "consumer_id": "UUID1",
                "message_type": 2,
                "branch": "master",
                "cache_id": "1",
                "schema_id": "1",
                "step_id": "0",
            }
        }

        asyncio.get_event_loop().run_until_complete(self.controller.handle_received(mock_client_init_msg, "UUID1"))

        actual_server_build_msg = json.loads(self.consumer.get_sent_data())

        self.assertDictEqual(expected_server_build_msg, actual_server_build_msg)
