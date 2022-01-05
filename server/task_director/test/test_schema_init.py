import copy
import json

from channels.routing import URLRouter
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from channels.layers import get_channel_layer
from django.test import TestCase

from task_director.src.message_type import MessageType
from task_director.routing import channel_name_patterns, websocket_urlpatterns


param_list = [
    [
        "single_instance_connected",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            }
        ],
        1,
    ],
    [
        "two_instances_connected_with_identical_config",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        1,
    ],
    [
        "two_instances_connected_with_differing_branch_names",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "master",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        2,
    ],
    [
        "two_instances_connected_with_differing_patchsets",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b72",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        2,
    ],
    [
        "two_instances_connected_with_differing_repo_names",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_2": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        2,
    ],
    [
        "two_instances_connected_with_initial_patchset_present_in_additional_patchsets_list",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                        "additional_patchsets": [
                            "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                        ],
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        1,
    ],
    [
        "two_instances_connected_with_initial_patchset_not_present_in_additional_patchsets_list",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                        "additional_patchsets": [
                            "234234eadf9uqhr9ueafbizdh923849efk99s8f",
                        ],
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        2,
    ],
    [
        "two_instances_connected_with_differing_cache_id",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "2",
                "schema_id": "1",
                "total_steps": 1,
            },
        ],
        2,
    ],
    [
        "two_instances_connected_with_differing_schema_id",
        [
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "1",
                "total_steps": 1,
            },
            {
                "message_type": MessageType.INIT,
                "repo_state": {
                    "org/repo_1": {
                        "base_ref": "main",
                        "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    }
                },
                "cache_id": "1",
                "schema_id": "2",
                "total_steps": 1,
            },
        ],
        2,
    ],
]


class TaskDirectorTests__SchemaInstanceInitialisation(TestCase):
    async def test__schema_instance_count(self):
        for name, consumer_configs, expected_instance_count in param_list:
            with self.subTest(name):
                application = ProtocolTypeRouter(
                    {
                        "channel": ChannelNameRouter(channel_name_patterns),
                        "websocket": URLRouter(websocket_urlpatterns),
                    }
                )
                controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})

                consumers = []
                for index, consumer_config in enumerate(consumer_configs):
                    consumer = WebsocketCommunicator(application, "/ws/api/1/" + str(index) + "/")
                    connected, subprotocol = await consumer.connect()
                    self.assertTrue(connected)
                    consumers.append(consumer)

                    # Mock client send to consumer via the websocket communicator
                    await consumer.send_to(text_data=json.dumps(consumer_config))

                    # Wait for consumer to send to controller channel
                    controller_msg = await get_channel_layer().receive("controller")
                    # Forward message from channel to controller via the application communicator
                    await controller.send_input(copy.deepcopy(controller_msg))

                total_registered_consumers = await self.get_total_registered_consumers(controller)
                total_running_schema_instances = await self.get_total_running_schema_instances(controller)

                self.assertEqual(expected_instance_count, total_running_schema_instances)
                self.assertEqual(len(consumer_configs), total_registered_consumers)

                for consumer in consumers:
                    await consumer.disconnect()
                    controller_msg = await get_channel_layer().receive("controller")
                    await controller.send_input(copy.deepcopy(controller_msg))

                controller.stop()

    async def get_total_registered_consumers(self, controller):
        await controller.send_input(
            {
                "type": "get.total.registered.consumers.msg",
                "channel_name": "testing",
            }
        )
        registered_consumers_msg = await get_channel_layer().receive("testing")
        return registered_consumers_msg["total_registered_consumers"]

    async def get_total_running_schema_instances(self, controller):
        await controller.send_input(
            {
                "type": "get.total.running.schema.instances.msg",
                "channel_name": "testing",
            }
        )
        instances_created_msg = await get_channel_layer().receive("testing")
        return instances_created_msg["total_running_schema_instances"]
