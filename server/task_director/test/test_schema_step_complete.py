import copy
import json

from channels.routing import URLRouter
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from channels.layers import get_channel_layer

from django.test import TestCase

from task_director.src.message_type import MessageType

from task_director.src.message_type import MessageType
from task_director.routing import channel_name_patterns, websocket_urlpatterns


class TaskDirectorTests__SingleConsumerStepComplete(TestCase):
    async def setUpAsync(self):
        application = ProtocolTypeRouter(
            {
                "channel": ChannelNameRouter(channel_name_patterns),
                "websocket": URLRouter(websocket_urlpatterns),
            }
        )
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer = WebsocketCommunicator(application, "/ws/api/1/1/")
        connected, subprotocol = await self.consumer.connect()

    async def tearDownAsync(self):
        await self.consumer.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

    async def test__when_one_consumer_connected__and_single_schema_step_is_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a successful step complete message.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        await self.setUpAsync()

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
        # Send client init message to controller
        await self.consumer.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_build_instruction_msg = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_msg, json.loads(actual_build_instruction_msg))

        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }

        # Send step complete message to controller
        await self.consumer.send_to(text_data=json.dumps(client_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_schema_complete_msg = {
            "type": "send.message",
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }
        actual_schema_complete_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()

    async def test__when_one_consumer_connected__and_multi_step_schema_is_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with multiple steps,
          AND the consumer subsequently sends multiple successful step complete messages.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        await self.setUpAsync()

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
        # Send client init message to controller
        await self.consumer.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_build_instruction_1_msg = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_1_msg, json.loads(actual_build_instruction_msg))

        client_step_1_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "1",
            "step_success": True,
        }
        # Send client init message to controller
        await self.consumer.send_to(text_data=json.dumps(client_step_1_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_build_instruction_2_msg = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_2_msg, json.loads(actual_build_instruction_msg))

        client_step_2_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        # Send client init message to controller
        await self.consumer.send_to(text_data=json.dumps(client_step_2_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_schema_complete_msg = {
            "type": "send.message",
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }
        actual_schema_complete_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()


class TaskDirectorTests__TwoConsumersStepComplete(TestCase):
    async def setUpAsync(self):
        application = ProtocolTypeRouter(
            {
                "channel": ChannelNameRouter(channel_name_patterns),
                "websocket": URLRouter(websocket_urlpatterns),
            }
        )
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer1 = WebsocketCommunicator(application, "/ws/api/1/1/")
        connected, subprotocol = await self.consumer1.connect()
        self.consumer2 = WebsocketCommunicator(application, "/ws/api/1/1/")
        connected, subprotocol = await self.consumer2.connect()

    async def tearDownAsync(self):
        await self.consumer1.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))
        await self.consumer2.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

    async def test__when_two_consumers_connected__and_both_schema_steps_are_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send an INIT message with the same config and two steps,
          AND the server sends a different build instruction message to each consumer,
          AND the consumers subsequently send a successful step complete message.
        EXPECT the server to return to both consumers a schema complete message.
        """

        await self.setUpAsync()

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
        # Send client init message to controller
        await self.consumer1.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_client_1_build_instruction_msg = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        actual_build_instruction_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_client_1_build_instruction_msg, json.loads(actual_build_instruction_msg))

        # Send client init message to controller
        await self.consumer2.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_client_2_build_instruction_msg = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_client_2_build_instruction_msg, json.loads(actual_build_instruction_msg))

        client_1_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        await self.consumer1.send_to(text_data=json.dumps(client_1_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        client_2_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "1",
            "step_success": True,
        }
        await self.consumer2.send_to(text_data=json.dumps(client_2_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_schema_complete_msg = {
            "type": "send.message",
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }
        actual_schema_complete_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))
        actual_schema_complete_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()
