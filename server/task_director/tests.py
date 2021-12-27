import asyncio
import json

from django.test import TestCase

from task_director.controller import TaskDirectorController
from task_director.message_type import MessageType


class MockAsyncJsonWebsocketConsumer:
    def __init__(self, id):
        self.id = id

    async def send(self, text_data: str):
        self.sent_data = text_data

    def get_sent_data(self):
        return self.sent_data


class TaskDirectorTests__Setup(TestCase):
    def test__controller_initialisation(self):
        """
        Check that the controller can be initialised.
        """
        controller = TaskDirectorController()
        self.assertNotEqual(None, controller)

    def test__add_consumer_to_controller(self):
        controller = TaskDirectorController()
        created_consumer = MockAsyncJsonWebsocketConsumer("UUID1")

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(0, registered_consumers)

        controller.register_consumer("UUID1", created_consumer)

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(1, registered_consumers)

        controller.deregister_consumer("UUID1")

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(0, registered_consumers)


class TaskDirectorTests__Messaging(TestCase):
    def test__send_message(self):
        controller = TaskDirectorController()
        created_consumer = MockAsyncJsonWebsocketConsumer("UUID1")
        controller.register_consumer("UUID1", created_consumer)

        mock_client_init_msg = {
            "message_type": MessageType.INIT,
            "branch": "master",
            "cache_id": "1",
            "schema_id": "1",
            "total_steps": 1,
        }
        expected_server_build_msg = {
            "payload": {
                "consumer_id": "UUID1",
                "message_type": 2,
                "branch": "master",
                "cache_id": "1",
                "schema_id": "1",
                "step_id": "0",
            }
        }

        asyncio.get_event_loop().run_until_complete(controller.handle_received(mock_client_init_msg, "UUID1"))

        actual_server_build_msg = json.loads(created_consumer.get_sent_data())

        self.assertDictEqual(expected_server_build_msg, actual_server_build_msg)
