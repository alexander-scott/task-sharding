import asyncio
import json

from django.test import TestCase

from task_director.src.controller import TaskDirectorController
from task_director.src.message_type import MessageType

from task_director.test.utils import create_consumer


class TaskDirectorTests__SchemaCompleted(TestCase):
    def test__when_a_consumer_completes_a_schema__and_another_consumer_completes_a_consecutive_schema__expect_two_schemas_completed(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskDirectorController.
        WHEN a consumer connects, completes build instructions, and then disconnects,
          AND then a second consumer connects, completes build instructions, and then disconnects.
        EXPECT two schema instances to be successfully completed.
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
        client_step_complete_msg = {
            "message_type": MessageType.STEP_COMPLETE,
            "schema_id": "1",
            "step_id": "0",
            "step_success": True,
        }
        expected_schema_complete_msg = {
            "message_type": MessageType.SCHEMA_COMPLETE,
            "schema_id": "1",
        }

        controller = TaskDirectorController()
        consumer_1 = create_consumer("UUID1")
        consumer_1._controller = controller
        asyncio.get_event_loop().run_until_complete(consumer_1.connect())
        asyncio.get_event_loop().run_until_complete(consumer_1.receive(json.dumps(client_init_msg)))

        self.assertEqual(1, controller.get_total_running_schema_instances())

        asyncio.get_event_loop().run_until_complete(consumer_1.receive(json.dumps(client_step_complete_msg)))
        consumer_1.send.assert_called_with(text_data=json.dumps(expected_schema_complete_msg))
        asyncio.get_event_loop().run_until_complete(consumer_1.disconnect("200"))

        self.assertEqual(0, controller.get_total_running_schema_instances())

        consumer_2 = create_consumer("UUID1")
        consumer_2._controller = controller
        asyncio.get_event_loop().run_until_complete(consumer_2.connect())
        asyncio.get_event_loop().run_until_complete(consumer_2.receive(json.dumps(client_init_msg)))

        self.assertEqual(1, controller.get_total_running_schema_instances())

        asyncio.get_event_loop().run_until_complete(consumer_2.receive(json.dumps(client_step_complete_msg)))
        consumer_2.send.assert_called_with(text_data=json.dumps(expected_schema_complete_msg))
        asyncio.get_event_loop().run_until_complete(consumer_2.disconnect("200"))

        self.assertEqual(0, controller.get_total_running_schema_instances())
