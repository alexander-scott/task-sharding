import json

from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from django.test import TestCase

from task_sharding.test.defaults import (
    create_application,
    create_default_client_init_message,
    create_default_build_instruction_message,
    create_default_task_complete_message,
)
from task_sharding.test.utils import (
    proxy_message_from_channel_to_communicator,
    prompt_response_from_communicator,
    send_message_between_communicators,
)


class TaskShardingTests__SingleConsumerTaskFailed(TestCase):
    async def setUpAsync(self):
        application = create_application()
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer.connect()

    async def tearDownAsync(self):
        await self.consumer.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)

    async def test__when_one_consumer_connected__and_single_schema_task_is_failed__expect_build_instruction_resent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN a consumer connects and sends an INIT message with a single task,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a failed task message.
        EXPECT the server to send the same build instruction message to the consumer.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message()
        await send_message_between_communicators(self.consumer, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_msg = create_default_build_instruction_message()
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_msg, json.loads(actual_build_instruction_msg))

        # Send task failed to controller
        client_task_complete_msg = create_default_task_complete_message(0, False)
        await send_message_between_communicators(self.consumer, self.controller, client_task_complete_msg)

        # Assert the controller sent the correct build instruction to the consumer
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_msg, json.loads(actual_build_instruction_msg))

        await self.tearDownAsync()


class TaskShardingTests__SingleConsumerTaskAbandoned(TestCase):
    async def setUpAsync(self):
        application = create_application()
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer.connect()

    async def tearDownAsync(self):
        await self.consumer.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)

    async def test__when_one_consumer_connected__and_single_schema_task_is_abandoned__expect_schema_is_abandoned(self):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN a consumer connects and sends an INIT message with a single task,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently disconnects.
        EXPECT the server to abandon the schema.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message()
        await send_message_between_communicators(self.consumer, self.controller, client_init_msg)

        # Assert one schema instance is running
        total_running_schema_instances = await prompt_response_from_communicator(
            self.controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(1, total_running_schema_instances)

        # Disconnect consumer
        await self.tearDownAsync()

        # Assert no schema instances are running
        total_running_schema_instances = await prompt_response_from_communicator(
            self.controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
        )
        self.assertEqual(0, total_running_schema_instances)


class TaskShardingTests__MultipleConsumerTaskAbandoned(TestCase):
    async def setUpAsync(self):
        application = create_application()
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer1 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer1.connect()
        self.consumer2 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer2.connect()

    async def test__when_two_consumers_connected__and_schema_task_is_abandoned__expect_abandoned_schema_task_to_be_assigned_to_other_consumer(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN two consumers connect and send an INIT message with the same config and two tasks,
          AND the server sends a different build instruction message to each consumer,
          AND one consumer subsequently disconnects during the task.
        EXPECT the abandoned task to be assigned to the remaining consumer.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message(2)
        await send_message_between_communicators(self.consumer1, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_msg_task_1 = create_default_build_instruction_message("1")
        actual_build_instruction_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_task_1, json.loads(actual_build_instruction_msg))

        # Send client init message to controller
        await send_message_between_communicators(self.consumer2, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_msg_task_0 = create_default_build_instruction_message()
        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_task_0, json.loads(actual_build_instruction_msg))

        # Disconnect consumer1
        await self.consumer1.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)

        # Send task complete message to controller
        task_2_task_complete_msg = create_default_task_complete_message()
        await send_message_between_communicators(self.consumer2, self.controller, task_2_task_complete_msg)

        # Assert the controller sent the correct build instruction to the consumer
        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_build_instruction_msg_task_1, json.loads(actual_build_instruction_msg))

        await self.consumer2.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)
