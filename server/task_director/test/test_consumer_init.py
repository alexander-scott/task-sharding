import asyncio
import json

from django.test import TestCase

from task_director.src.message_type import MessageType

from task_director.test.utils import create_consumer


class TaskDirectorTests__SingleConsumerInit(TestCase):
    def setUp(self):
        self.consumer = create_consumer("UUID1")
        asyncio.get_event_loop().run_until_complete(self.consumer.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer.disconnect("200"))

    def test__when_one_consumer_connected__expect_server_to_return_msg(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an init message with a single step.
        EXPECT the server to return to the same consumer a build instruction message.
        """

        mock_client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }

        expected_server_build_msg = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }

        asyncio.get_event_loop().run_until_complete(self.consumer.receive(json.dumps(mock_client_init_msg)))
        self.consumer.send.assert_called_with(text_data=json.dumps(expected_server_build_msg))


class TaskDirectorTests__TwoConsumersInit(TestCase):
    def setUp(self):
        self.consumer1 = create_consumer("UUID1")
        self.consumer2 = create_consumer("UUID2")
        asyncio.get_event_loop().run_until_complete(self.consumer1.connect())
        asyncio.get_event_loop().run_until_complete(self.consumer2.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer1.disconnect("200"))
        asyncio.get_event_loop().run_until_complete(self.consumer2.disconnect("200"))

    def test__when_two_consumers_connected__and_configs_are_compatible__expect_single_schema_instance_created(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send INIT messages with two steps.
        EXPECT the server to return to the first consumer a build instruction for the first step,
          AND the server to return to the second consumer a build instruction for the second step.
        """

        mock_client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 2,
        }
        expected_server_build_msg_1 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        expected_server_build_msg_2 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }

        asyncio.get_event_loop().run_until_complete(self.consumer1.receive(json.dumps(mock_client_init_msg)))
        asyncio.get_event_loop().run_until_complete(self.consumer2.receive(json.dumps(mock_client_init_msg)))

        self.consumer1.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_1))
        self.consumer2.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_2))

    def test__when_two_consumer_connected__and_cache_id_is_incompatible__expect_two_schema_director_instances_created(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send INIT messages with one step,
          AND each consumer has a different cache ID.
        EXPECT a build instruction message with the same step ID to be sent to each consumer.
        """
        mock_client_init_msg_1 = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }
        mock_client_init_msg_2 = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "2",
            "schema_id": "1",
            "total_steps": 1,
        }
        expected_server_build_msg_1 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        expected_server_build_msg_2 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }

        asyncio.get_event_loop().run_until_complete(self.consumer1.receive(json.dumps(mock_client_init_msg_1)))
        asyncio.get_event_loop().run_until_complete(self.consumer2.receive(json.dumps(mock_client_init_msg_2)))

        self.consumer1.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_1))
        self.consumer2.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_2))

    def test__when_two_consumer_connected__and_branch_is_incompatible__expect_two_schema_director_instances_created(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send INIT messages with one step,
          AND each consumer has a different branch.
        EXPECT a build instruction message with the same step ID to be sent to each consumer.
        """
        mock_client_init_msg_1 = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }
        mock_client_init_msg_2 = {
            "message_type": MessageType.INIT,
            "branch": "main",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }
        expected_server_build_msg_1 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        expected_server_build_msg_2 = {
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }

        asyncio.get_event_loop().run_until_complete(self.consumer1.receive(json.dumps(mock_client_init_msg_1)))
        asyncio.get_event_loop().run_until_complete(self.consumer2.receive(json.dumps(mock_client_init_msg_2)))

        self.consumer1.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_1))
        self.consumer2.send.assert_called_with(text_data=json.dumps(expected_server_build_msg_2))
