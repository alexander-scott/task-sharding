import asyncio
import json

from parameterized import parameterized

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.utils import create_consumer


class TaskDirectorTests__SchemaInstanceInitialisation(TestCase):
    @parameterized.expand(
        [
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
    )
    def test__schema_instance_count(self, name: str, consumer_configs: list[dict], expected_instance_count: int):
        controller = TaskDirectorController()
        consumers = []
        for index, consumer_config in enumerate(consumer_configs):
            consumer = create_consumer(str(index))
            consumer._controller = controller
            consumers.append(consumer)
            asyncio.get_event_loop().run_until_complete(consumer.connect())
            asyncio.get_event_loop().run_until_complete(consumer.receive(json.dumps(consumer_config)))

        total_instances_created = controller.get_total_running_schema_instances()
        total_consumers_connected = controller.get_total_registered_consumers()

        self.assertEqual(expected_instance_count, total_instances_created)
        self.assertEqual(len(consumer_configs), total_consumers_connected)

        for consumer in consumers:
            asyncio.get_event_loop().run_until_complete(consumer.disconnect("200"))
