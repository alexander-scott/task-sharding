import copy
import json

from channels.routing import URLRouter
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from channels.layers import get_channel_layer

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.src.message_type import MessageType
from task_director.routing import channel_name_patterns, websocket_urlpatterns


class TaskDirectorTests__SingleConsumerStepFailed(TestCase):
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

    async def test__when_one_consumer_connected__and_single_schema_step_is_failed__expect_build_instruction_resent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a failed step message.
        EXPECT the server to send the same build instruction message to the consumer.
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
            "step_success": False,
        }

        await self.consumer.send_to(text_data=json.dumps(client_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_msg, json.loads(actual_build_instruction_msg))

        await self.tearDownAsync()


class TaskDirectorTests__SingleConsumerStepAbandoned(TestCase):
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

    async def test__when_one_consumer_connected__and_single_schema_step_is_abandoned__expect_schema_is_abandoned(self):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects and sends an INIT message with a single step,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently disconnects.
        EXPECT the server to abandon the schema.
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

        await self.controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(1, running_instances_msg["total_running_schema_instances"])

        await self.tearDownAsync()

        await self.controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(0, running_instances_msg["total_running_schema_instances"])


class TaskDirectorTests__MultipleConsumerStepAbandoned(TestCase):
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

    async def test__when_two_consumers_connected__and_schema_step_is_abandoned__expect_abandoned_schema_step_to_be_assigned_to_other_consumer(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN two consumers connect and send an INIT message with the same config and two steps,
          AND the server sends a different build instruction message to each consumer,
          AND one consumer subsequently disconnects during the step.
        EXPECT the abandoned step to be assigned to the remaining consumer.
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

        expected_build_instruction_msg_step_1 = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "1",
        }
        actual_build_instruction_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_step_1, json.loads(actual_build_instruction_msg))

        # Send client init message to controller
        await self.consumer2.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        expected_build_instruction_msg_step_0 = {
            "type": "send.message",
            "message_type": MessageType.BUILD_INSTRUCTION,
            "schema_id": "1",
            "step_id": "0",
        }
        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_step_0, json.loads(actual_build_instruction_msg))

        await self.consumer1.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        step_2_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }

        await self.consumer2.send_to(text_data=json.dumps(step_2_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))

        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_step_1, json.loads(actual_build_instruction_msg))

        await self.consumer2.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await self.controller.send_input(copy.deepcopy(controller_msg))
