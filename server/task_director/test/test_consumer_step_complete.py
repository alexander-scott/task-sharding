import asyncio
import json
from unittest.mock import AsyncMock, call

from django.test import TestCase

from task_director.consumers import TaskDirectorConsumer
from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType


class TaskDirectorTests__SingleConsumerStepComplete(TestCase):
    def setUp(self):
        self.controller = TaskDirectorController()

        self.consumer = TaskDirectorConsumer()
        self.consumer.scope = {"url_route": {"kwargs": {"api_version": "1", "id": "UUID1"}}}
        self.consumer.accept = AsyncMock()
        self.consumer.send = AsyncMock()
        self.consumer._controller = self.controller
        asyncio.get_event_loop().run_until_complete(self.consumer.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer.disconnect("200"))

    def test__when_one_consumer_connected__and_single_schema_step_is_successful__expect_schema_complete_msg_sent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a successful step complete message.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 1,
            "schema_id": "1",
        }
        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_init_msg)))

        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_step_complete_msg)))

        expected_build_instruction_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        expected_schema_complete_msg = {
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }
        self.consumer.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_build_instruction_msg)),
                call(text_data=json.dumps(expected_schema_complete_msg)),
            ]
        )

    def test__when_one_consumer_connected__and_single_schema_step_is_failed__expect_build_instruction_resent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a failed step message.
        EXPECT the server to send the same build instruction message to the consumer.
        """
        client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 1,
            "schema_id": "1",
        }

        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_init_msg)))

        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": False,
        }

        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_step_complete_msg)))
        expected_build_instruction_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        self.consumer.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_build_instruction_msg)),
                call(text_data=json.dumps(expected_build_instruction_msg)),
            ]
        )
