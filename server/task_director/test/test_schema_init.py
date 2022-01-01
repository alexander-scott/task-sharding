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
                        "branch": "master",
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
                        "branch": "master",
                        "cache_id": "1",
                        "schema_id": "1",
                        "total_steps": 1,
                    },
                    {
                        "message_type": MessageType.INIT,
                        "branch": "master",
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
                        "branch": "master",
                        "cache_id": "1",
                        "schema_id": "1",
                        "total_steps": 1,
                    },
                    {
                        "message_type": MessageType.INIT,
                        "branch": "main",
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
                        "branch": "master",
                        "cache_id": "1",
                        "schema_id": "1",
                        "total_steps": 1,
                    },
                    {
                        "message_type": MessageType.INIT,
                        "branch": "master",
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
                        "branch": "master",
                        "cache_id": "1",
                        "schema_id": "1",
                        "total_steps": 1,
                    },
                    {
                        "message_type": MessageType.INIT,
                        "branch": "master",
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

        self.assertEqual(expected_instance_count, total_instances_created)

        for consumer in consumers:
            asyncio.get_event_loop().run_until_complete(consumer.disconnect("200"))
