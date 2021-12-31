import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

from django.test import TestCase
from task_director.consumers import TaskDirectorConsumer

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType


class TaskDirectorTests__SingleConsumerInit(TestCase):
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
        self.controller = TaskDirectorController()

        self.consumer1 = TaskDirectorConsumer()
        self.consumer1.scope = {"url_route": {"kwargs": {"api_version": "1", "id": "UUID1"}}}
        self.consumer1.accept = AsyncMock()
        self.consumer1.send = AsyncMock()
        self.consumer1._controller = self.controller
        asyncio.get_event_loop().run_until_complete(self.consumer1.connect())
        self.consumer2 = TaskDirectorConsumer()
        self.consumer2.scope = {"url_route": {"kwargs": {"api_version": "1", "id": "UUID2"}}}
        self.consumer2.accept = AsyncMock()
        self.consumer2.send = AsyncMock()
        self.consumer2._controller = self.controller
        asyncio.get_event_loop().run_until_complete(self.consumer2.connect())

    def tearDown(self):
        asyncio.get_event_loop().run_until_complete(self.consumer1.disconnect("200"))
        asyncio.get_event_loop().run_until_complete(self.consumer2.disconnect("200"))

    def test__when_two_consumers_connected__expect_server_to_return_two_msgs(self):
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
