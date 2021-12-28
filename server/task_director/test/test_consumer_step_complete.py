import asyncio
import json

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.mock_classes.mock_consumer import MockConsumer


class TaskDirectorTests__StepComplete(TestCase):
    def setUp(self):
        self.controller = TaskDirectorController()

    def test__one_consumer_connected(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step.
        EXPECT the server to return to the same consumer a BUILD instruction message.
        """
        consumer_id = "UUID1"
        consumer = MockConsumer(consumer_id)
        self.controller.register_consumer(consumer_id, consumer)
        client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 1,
            "schema_id": "1",
        }

        asyncio.get_event_loop().run_until_complete(self.controller.handle_received(client_init_msg, consumer_id))
        consumer.get_sent_data()

        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 1,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }

        asyncio.get_event_loop().run_until_complete(
            self.controller.handle_received(client_step_complete_msg, consumer_id)
        )
        expected_schema_complete_msg = {
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
            "consumer_id": "UUID1",
        }
        actual_schema_complete_msg = json.loads(consumer.get_sent_data())

        self.assertDictEqual(expected_schema_complete_msg, actual_schema_complete_msg)
