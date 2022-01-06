import json

from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from django.test import TestCase

from task_director.src.message_type import MessageType

from task_director.test.defaults import create_application
from task_director.test.utils import proxy_message_from_channel_to_communicator, prompt_response_from_communicator


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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                "patchset_complexity": {
                    "complex": False,
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
                application = create_application()
                controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})

                consumers = []
                for index, consumer_config in enumerate(consumer_configs):
                    consumer = WebsocketCommunicator(application, "/ws/api/1/" + str(index) + "/")
                    connected, _ = await consumer.connect()
                    self.assertTrue(connected)
                    consumers.append(consumer)

                    # Mock client send to consumer via the websocket communicator
                    await consumer.send_to(text_data=json.dumps(consumer_config))

                    # Proxy the message sent from consumer to the controller
                    await proxy_message_from_channel_to_communicator("controller", controller)

                total_registered_consumers = await prompt_response_from_communicator(
                    controller, "get.total.registered.consumers.msg", "total_registered_consumers"
                )
                total_running_schema_instances = await prompt_response_from_communicator(
                    controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
                )

                self.assertEqual(expected_instance_count, total_running_schema_instances)
                self.assertEqual(len(consumer_configs), total_registered_consumers)

                for consumer in consumers:
                    await consumer.disconnect()
                    await proxy_message_from_channel_to_communicator("controller", controller)

                controller.stop()
