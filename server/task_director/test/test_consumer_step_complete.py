import asyncio
import json
from unittest.mock import call

from django.test import TestCase

from task_director.src.message_type import MessageType

from task_director.test.utils import create_consumer


class TaskDirectorTests__SingleConsumerStepComplete(TestCase):
    def setUp(self):
        self.consumer = create_consumer("UUID1")
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

    def test__when_one_consumer_connected__and_multi_step_schema_is_successful__expect_schema_complete_msg_sent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with multiple steps,
          AND the consumer subsequently sends multiple successful step complete messages.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 2,
            "schema_id": "1",
        }
        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_init_msg)))

        client_step_1_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "1",
            "step_success": True,
        }
        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_step_1_complete_msg)))

        client_step_2_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(client_step_2_complete_msg)))

        expected_build_instruction_1_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        expected_build_instruction_2_msg = {
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
                call(text_data=json.dumps(expected_build_instruction_1_msg)),
                call(text_data=json.dumps(expected_build_instruction_2_msg)),
                call(text_data=json.dumps(expected_schema_complete_msg)),
            ]
        )


class TaskDirectorTests__TwoConsumersStepComplete(TestCase):
    def setUp(self):
        self.consumer1 = create_consumer("UUID1")
        self.consumer2 = create_consumer("UUID2")
        asyncio.get_event_loop().run_until_complete(self.consumer1.connect())
        asyncio.get_event_loop().run_until_complete(self.consumer2.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer1.disconnect("200"))
        asyncio.get_event_loop().run_until_complete(self.consumer2.disconnect("200"))

    def test__when_two_consumers_connected__and_both_schema_steps_are_successful__expect_schema_complete_msg_sent(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send an INIT message with two steps,
          AND the server sends a build instruction message to each consumer,
          AND the consumers subsequently send a successful step complete message.
        EXPECT the server to return to both consumers a schema complete message.
        """

        client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "total_steps": 2,
            "schema_id": "1",
        }
        asyncio.get_event_loop().run_until_complete(self.consumer1.receive(json.dumps(client_init_msg)))
        asyncio.get_event_loop().run_until_complete(self.consumer2.receive(json.dumps(client_init_msg)))

        client_1_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        client_2_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "1",
            "step_success": True,
        }
        asyncio.get_event_loop().run_until_complete(self.consumer1.receive(json.dumps(client_1_step_complete_msg)))
        asyncio.get_event_loop().run_until_complete(self.consumer2.receive(json.dumps(client_2_step_complete_msg)))

        expected_client_1_build_instruction_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        expected_client_2_build_instruction_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        expected_schema_complete_msg = {
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }
        self.consumer1.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_client_1_build_instruction_msg)),
                call(text_data=json.dumps(expected_schema_complete_msg)),
            ]
        )
        self.consumer2.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_client_2_build_instruction_msg)),
                call(text_data=json.dumps(expected_schema_complete_msg)),
            ]
        )
