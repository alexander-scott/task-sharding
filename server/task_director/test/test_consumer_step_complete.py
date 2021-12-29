import asyncio
import json
from queue import Empty

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.mock_classes.mock_consumer import MockConsumer


class TaskDirectorTests__StepComplete(TestCase):
    def setUp(self):
        self.controller = TaskDirectorController()

    def test__when_one_consumer_connected__and_single_schema_step_is_successful__expect_schema_complete_msg_sent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
        AND the server sends a build instruction message to the consumer,
        AND the consumer subsequently sends a successful step complete message.
        EXPECT the server to return to the same consumer a schema complete message.
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
        }
        actual_schema_complete_msg = json.loads(consumer.get_sent_data())

        self.assertDictEqual(expected_schema_complete_msg, actual_schema_complete_msg)

    def test__when_one_consumer_connected__and_single_schema_step_is_failed__expect_build_instruction_resent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
        AND the server sends a build instruction message to the consumer,
        AND the consumer subsequently sends a failed step message.
        EXPECT the server to send the same build instruction message to the consumer.
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
            "schema_id": "1",
            "step_id": "0",
            "step_success": False,
        }

        asyncio.get_event_loop().run_until_complete(
            self.controller.handle_received(client_step_complete_msg, consumer_id)
        )
        expected_schema_complete_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        actual_schema_complete_msg = json.loads(consumer.get_sent_data())

        self.assertDictEqual(expected_schema_complete_msg, actual_schema_complete_msg)
