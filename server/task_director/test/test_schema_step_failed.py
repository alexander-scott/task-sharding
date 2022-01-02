import asyncio
import json
from unittest.mock import call

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.utils import create_consumer


class TaskDirectorTests__SingleConsumerStepFailed(TestCase):
    def setUp(self):
        self.consumer = create_consumer("UUID1")
        asyncio.get_event_loop().run_until_complete(self.consumer.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer.disconnect("200"))

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
            "repo_state": {
                "org/repo_1": {
                    "base_ref": "main",
                    "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                }
            },
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


class TaskDirectorTests__SingleConsumerStepAbandoned(TestCase):
    def test__when_one_consumer_connected__and_single_schema_step_is_abandoned__expect_schema_is_abandoned(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently disconnects.
        EXPECT the server to abandon the schema.
        """

        controller = TaskDirectorController()
        consumer = create_consumer("1")
        consumer._controller = controller
        asyncio.get_event_loop().run_until_complete(consumer.connect())

        client_init_msg = {
            "message_type": MessageType.INIT,
            "repo_state": {
                "org/repo_1": {
                    "base_ref": "main",
                    "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                }
            },
            "cache_id": "1",
            "total_steps": 1,
            "schema_id": "1",
        }

        asyncio.get_event_loop().run_until_complete(consumer.receive(json.dumps(client_init_msg)))

        self.assertEqual(1, controller.get_total_running_schema_instances())

        asyncio.get_event_loop().run_until_complete(consumer.disconnect("500"))

        self.assertEqual(0, controller.get_total_running_schema_instances())


class TaskDirectorTests__MultipleConsumerStepAbandoned(TestCase):
    def test__when_two_consumers_connected__and_schema_step_is_abandoned__expect_abandoned_schema_step_to_be_assigned_to_other_consumer(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send an INIT message with the same config and two steps,
          AND the server sends a different build instruction message to each consumer,
          AND one consumer subsequently disconnects during the step.
        EXPECT the abandoned step to be assigned to the remaining consumer.
        """

        controller = TaskDirectorController()
        consumer1 = create_consumer("1")
        consumer1._controller = controller
        asyncio.get_event_loop().run_until_complete(consumer1.connect())
        consumer2 = create_consumer("2")
        consumer2._controller = controller
        asyncio.get_event_loop().run_until_complete(consumer2.connect())

        client_init_msg = {
            "message_type": MessageType.INIT,
            "repo_state": {
                "org/repo_1": {
                    "base_ref": "main",
                    "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                }
            },
            "cache_id": "1",
            "total_steps": 2,
            "schema_id": "1",
        }

        asyncio.get_event_loop().run_until_complete(consumer1.receive(json.dumps(client_init_msg)))
        asyncio.get_event_loop().run_until_complete(consumer2.receive(json.dumps(client_init_msg)))

        self.assertEqual(1, controller.get_total_running_schema_instances())

        asyncio.get_event_loop().run_until_complete(consumer1.disconnect("500"))

        consumer_2_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }

        asyncio.get_event_loop().run_until_complete(consumer2.receive(json.dumps(consumer_2_step_complete_msg)))

        expected_consumer_2_build_instruction_msg_1 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        expected_consumer_2_build_instruction_msg_2 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }

        consumer1.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_consumer_2_build_instruction_msg_2)),
            ]
        )
        consumer2.send.assert_has_calls(
            [
                call(text_data=json.dumps(expected_consumer_2_build_instruction_msg_1)),
                call(text_data=json.dumps(expected_consumer_2_build_instruction_msg_2)),
            ]
        )
