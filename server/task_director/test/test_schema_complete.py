import json

from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from django.test import TestCase

from task_director.test.defaults import (
    create_application,
    create_default_client_init_message,
    create_default_step_complete_message,
    create_default_schema_complete_message,
)
from task_director.test.utils import (
    proxy_message_from_channel_to_communicator,
    prompt_response_from_communicator,
    send_message_between_communicators,
)


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

        application = create_application()
        controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        consumer_1 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await consumer_1.connect()

        client_init_msg = create_default_client_init_message()
        client_step_complete_msg = create_default_step_complete_message()
        expected_schema_complete_msg = create_default_schema_complete_message()

        # Send client init message to controller
        await send_message_between_communicators(consumer_1, controller, client_init_msg)

        # Build instructions msg
        await consumer_1.receive_from()

        # Assert one schema instance is running
        total_running_schema_instances = await prompt_response_from_communicator(
            controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(1, total_running_schema_instances)

        # Send client step complete message to controller
        await send_message_between_communicators(consumer_1, controller, client_step_complete_msg)

        # Assert the controller sent the correct schema complete message to the consumer
        actual_schema_complete_msg = await consumer_1.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await consumer_1.disconnect()
        await proxy_message_from_channel_to_communicator("controller", controller)

        # Assert no schema instances are running
        total_running_schema_instances = await prompt_response_from_communicator(
            controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(0, total_running_schema_instances)

        consumer_2 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await consumer_2.connect()

        # Send client init message to controller
        await send_message_between_communicators(consumer_2, controller, client_init_msg)

        # Build instructions msg
        await consumer_2.receive_from()

        # Assert one schema instance is running
        total_running_schema_instances = await prompt_response_from_communicator(
            controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(1, total_running_schema_instances)

        # Send client step complete message to controller
        await send_message_between_communicators(consumer_2, controller, client_step_complete_msg)

        # Assert the controller sent the correct schema complete message to the consumer
        actual_schema_complete_msg = await consumer_2.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await consumer_2.disconnect()
        await proxy_message_from_channel_to_communicator("controller", controller)

        # Assert no schema instances are running
        total_running_schema_instances = await prompt_response_from_communicator(
            controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(0, total_running_schema_instances)
