import copy
import json

from channels.routing import URLRouter
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from channels.layers import get_channel_layer
from django.test import TestCase

from task_director.src.message_type import MessageType
from task_director.routing import channel_name_patterns, websocket_urlpatterns


class TaskDirectorTests__SchemaCompleted(TestCase):
    async def test__when_a_consumer_completes_a_schema__and_another_consumer_completes_a_consecutive_schema__expect_two_schemas_completed(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects, completes build instructions, and then disconnects,
          AND then a second consumer connects, completes build instructions, and then disconnects.
        EXPECT two schema instances to be successfully completed.
        """

        application = ProtocolTypeRouter(
            {
                "channel": ChannelNameRouter(channel_name_patterns),
                "websocket": URLRouter(websocket_urlpatterns),
            }
        )
        controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        consumer_1 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await consumer_1.connect()

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
        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        expected_schema_complete_msg = {
            "type": "send.message",
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }

        # Send client init message to controller
        await consumer_1.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        # Build instructions msg
        await consumer_1.receive_from()

        await controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(1, running_instances_msg["total_running_schema_instances"])

        await consumer_1.send_to(text_data=json.dumps(client_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        actual_schema_complete_msg = await consumer_1.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await consumer_1.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        await controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(0, running_instances_msg["total_running_schema_instances"])

        consumer_2 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await consumer_2.connect()

        await consumer_2.send_to(text_data=json.dumps(client_init_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        # Build instructions msg
        await consumer_2.receive_from()

        await controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(1, running_instances_msg["total_running_schema_instances"])

        await consumer_2.send_to(text_data=json.dumps(client_step_complete_msg))
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        actual_schema_complete_msg = await consumer_2.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await consumer_2.disconnect()
        controller_msg = await get_channel_layer().receive("controller")
        await controller.send_input(copy.deepcopy(controller_msg))

        await controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        running_instances_msg = await get_channel_layer().receive("testing")

        self.assertEqual(0, running_instances_msg["total_running_schema_instances"])
